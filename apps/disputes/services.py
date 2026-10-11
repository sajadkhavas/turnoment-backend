import re

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.matches.models import Match
from apps.results.models import MatchResult
from apps.results.services import finalize_locked

from .models import Dispute, DisputeEvidence
from .projections import MAX_BYTES, MAX_FILES, REASONS, dispute_data, evidence_data


def _lock(match_id, user):
    match = Match.objects.select_for_update().filter(pk=match_id).first()
    if match is None or not match.has_participant(user):
        raise PermissionDenied("Not a match participant")
    return match


@transaction.atomic
def create_dispute(match_id, user, revision, reason, statement, key):
    match = _lock(match_id, user)
    existing = Dispute.objects.filter(match=match).first()
    if existing:
        if (
            existing.created_by_id == user.pk
            and existing.idempotency_key == key
            and (
                existing.reason != reason
                or not isinstance(statement, str)
                or existing.statement != statement.strip()
            )
        ):
            return {
                "outcome": "validation_error",
                "fields": {"form": "Idempotency key conflict"},
            }
        return {
            "outcome": "already_open",
            "matchId": str(match.pk),
            "revision": str(match.revision),
            "dispute": dispute_data(existing),
        }
    if str(match.revision) != revision:
        return {"outcome": "stale", "revision": str(match.revision)}
    if match.state != Match.State.AWAITING_CONFIRMATION:
        return {
            "outcome": "unavailable",
            "reason": ("cancelled" if match.state == Match.State.CANCELLED else "not-eligible"),
        }
    errors = {}
    if reason not in REASONS:
        errors["reason"] = "Invalid reason"
    if not isinstance(statement, str) or not 20 <= len(statement.strip()) <= 1000:
        errors["statement"] = "Statement must contain 20-1000 characters"
    if errors:
        return {"outcome": "validation_error", "fields": errors}
    dispute = Dispute.objects.create(
        match=match,
        created_by=user,
        reason=reason,
        statement=statement.strip(),
        idempotency_key=key,
    )
    match.state = Match.State.DISPUTED
    match.revision += 1
    match.save(update_fields=["state", "revision"])
    return {
        "outcome": "accepted",
        "matchId": str(match.pk),
        "revision": str(match.revision),
        "dispute": dispute_data(dispute),
    }


def detect_image(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


@transaction.atomic
def add_evidence(match_id, dispute_id, user, revision, key, file):
    match = _lock(match_id, user)
    dispute = Dispute.objects.filter(pk=dispute_id, match=match).first()
    if dispute is None:
        raise PermissionDenied("Not an accessible dispute")
    old = DisputeEvidence.objects.filter(
        dispute=dispute, uploaded_by=user, idempotency_key=key
    ).first()
    if old:
        return {
            "outcome": "already_uploaded",
            "matchId": str(match.pk),
            "disputeId": str(dispute.pk),
            "revision": str(match.revision),
            "evidence": evidence_data(old),
        }
    if revision != str(match.revision):
        return {"outcome": "stale", "revision": str(match.revision)}
    if dispute.status == "resolved" or dispute.review_locked:
        return {
            "outcome": "unavailable",
            "reason": "resolved" if dispute.status == "resolved" else "review-locked",
        }
    if DisputeEvidence.objects.filter(dispute=dispute).count() >= MAX_FILES:
        return {"outcome": "unavailable", "reason": "quota-reached"}
    if file is None or file.size == 0 or file.size > MAX_BYTES:
        return {"outcome": "validation_error", "file": "File size must be 1-5242880 bytes"}
    content = file.read(MAX_BYTES + 1)
    sniffed = detect_image(content)
    if len(content) != file.size or not sniffed or file.content_type != sniffed:
        return {"outcome": "validation_error", "file": "Invalid image content or type"}
    original = file.name.replace("\\", "/").split("/")[-1]
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", original)[:160] or "evidence"
    item = DisputeEvidence.objects.create(
        dispute=dispute,
        uploaded_by=user,
        idempotency_key=key,
        file_name=safe_name,
        content_type=sniffed,
        size_bytes=file.size,
        quarantined_bytes=content,
    )
    match.revision += 1
    match.save(update_fields=["revision"])
    return {
        "outcome": "accepted",
        "matchId": str(match.pk),
        "disputeId": str(dispute.pk),
        "revision": str(match.revision),
        "evidence": evidence_data(item),
    }


@transaction.atomic
def resolve_dispute(dispute_id, operator, *, decision, summary):
    """B10 staff seam; explicitly NO center staff authority."""
    if not operator.is_authenticated or not operator.is_staff or not operator.is_superuser:
        raise PermissionDenied("Platform operator permission required")
    if decision not in {"upheld", "rejected", "adjusted", "voided", "no-action"}:
        raise ValidationError("Unsupported decision")
    if not isinstance(summary, str) or not summary.strip():
        raise ValidationError("Missing moderation summary")
    reference = Dispute.objects.get(pk=dispute_id)
    match = Match.objects.select_for_update().get(pk=reference.match_id)
    dispute = Dispute.objects.select_for_update().get(pk=dispute_id)
    if dispute.status == "resolved":
        if (dispute.decision, dispute.resolution_summary) != (decision, summary.strip()):
            raise ValidationError("Conflicting resolution replay")
        return dispute
    result = MatchResult.objects.get(match=match)
    if decision == "adjusted":
        raise ValidationError("Adjusted scores require a separate explicit reviewed command")
    if decision == "voided":
        match.state = Match.State.CANCELLED
        match.revision += 1
        match.save(update_fields=["state", "revision"])
    else:
        finalize_locked(match, result, operator)
    dispute.status = "resolved"
    dispute.decision = decision
    dispute.resolution_summary = summary.strip()
    dispute.resolved_at = timezone.now()
    dispute.review_locked = True
    dispute.save(
        update_fields=["status", "decision", "resolution_summary", "resolved_at", "review_locked"]
    )
    return dispute


@transaction.atomic
def start_review(dispute_id, operator):
    if not operator.is_authenticated or not operator.is_staff or not operator.is_superuser:
        raise PermissionDenied("Platform operator permission required")
    ref = Dispute.objects.get(pk=dispute_id)
    Match.objects.select_for_update().get(pk=ref.match_id)
    dispute = Dispute.objects.select_for_update().get(pk=dispute_id)
    if dispute.status == "open":
        dispute.status = "under-review"
        dispute.save(update_fields=["status"])
        Match.objects.filter(pk=dispute.match_id).update(revision=dispute.match.revision + 1)
    return dispute
