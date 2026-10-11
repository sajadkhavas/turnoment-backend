"""Idempotent, transactional DB primitives. Call within the owner's atomic transition."""

import json
import re

from django.db import transaction

from apps.core.identifiers import public_id

from .models import AuditRecord, DomainEvent

_NAME = re.compile(r"[a-z][a-z0-9_.-]{0,119}", re.ASCII)
_KEY = re.compile(r"[A-Za-z0-9_.:-]{8,200}", re.ASCII)
_PRIVATE_KEYS = frozenset({
    "phone", "email", "password", "secret", "token", "otp", "authorization",
    "cookie", "csrf", "session", "address", "national_id",
})


class IdempotencyConflict(ValueError):
    """Same (source, key) was previously committed for a different operation."""


def _name(value: str, max_length: int) -> str:
    if not isinstance(value, str) or len(value) > max_length or not _NAME.fullmatch(value):
        raise ValueError("Invalid source, event type, action or subject type")
    return value


def _key(value: str) -> str:
    if not isinstance(value, str) or not _KEY.fullmatch(value):
        raise ValueError("Idempotency key must be 8-200 ASCII characters")
    return value


def _safe_mapping(value):
    if not isinstance(value, dict):
        raise ValueError("Event/audit payload must be a JSON object")
    def walk(node):
        if isinstance(node, dict):
            for key, item in node.items():
                if not isinstance(key, str) or key.casefold() in _PRIVATE_KEYS:
                    raise ValueError("Private or invalid payload key")
                walk(item)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(value)
    try:
        encoded = json.dumps(value, ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Payload must be JSON-serializable") from exc
    if len(encoded.encode("utf-8")) > 16384:
        raise ValueError("Payload exceeds 16 KiB")
    return value


def _common(source, subject_type, subject_id, idempotency_key):
    return dict(
        source=_name(source, 80),
        subject_type=_name(subject_type, 80),
        subject_id=public_id(subject_id),
        idempotency_key=_key(idempotency_key),
    )


@transaction.atomic
def emit_event(
    *, source: str, event_type: str, subject_type: str, subject_id: str,
    idempotency_key: str, payload: dict | None = None,
) -> tuple[DomainEvent, bool]:
    """Durably enqueue once. No Celery publish before commit and no fake delivery."""
    fields = _common(source, subject_type, subject_id, idempotency_key)
    defaults = {
        "event_type": _name(event_type, 120),
        "subject_type": fields["subject_type"],
        "subject_id": fields["subject_id"],
        "payload": _safe_mapping(payload if payload is not None else {}),
    }
    event, created = DomainEvent.objects.get_or_create(
        source=fields["source"], idempotency_key=fields["idempotency_key"],
        defaults=defaults,
    )
    if not created and any(getattr(event, key) != value for key, value in defaults.items()):
        raise IdempotencyConflict("Event idempotency key reused with different content")
    return event, created


@transaction.atomic
def record_audit(
    *, source: str, action: str, subject_type: str, subject_id: str,
    idempotency_key: str, actor=None, details: dict | None = None,
) -> tuple[AuditRecord, bool]:
    fields = _common(source, subject_type, subject_id, idempotency_key)
    defaults = {
        "action": _name(action, 120),
        "subject_type": fields["subject_type"],
        "subject_id": fields["subject_id"],
        "actor": actor,
        "details": _safe_mapping(details if details is not None else {}),
    }
    audit, created = AuditRecord.objects.get_or_create(
        source=fields["source"], idempotency_key=fields["idempotency_key"],
        defaults=defaults,
    )
    if not created and (
        any(getattr(audit, key) != value for key, value in defaults.items() if key != "actor")
        or audit.actor_id != (actor.pk if actor else None)
    ):
        raise IdempotencyConflict("Audit idempotency key reused with different content")
    return audit, created
