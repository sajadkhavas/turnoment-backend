from django.core.exceptions import ValidationError
from django.db import transaction

from apps.moderation.admin_site import is_platform_operator

from .models import ModerationCase, ModerationDecision


def record_moderation_case(*, source_type, source_id, title, center_id=""):
    """Integration seam: B04/B08 emit durable review references after their own commit.

    No host/dispute state or private submission content is duplicated here.
    """
    values = {"title": title, "center_id": center_id}
    probe = ModerationCase(source_type=source_type, source_id=source_id, **values)
    probe.full_clean(validate_unique=False, validate_constraints=False)
    with transaction.atomic():
        case, created = ModerationCase.objects.get_or_create(
            source_type=source_type, source_id=source_id, defaults=values
        )
        if not created and (case.title != title or case.center_id != center_id):
            raise ValueError("Conflicting moderation source replay")
        return case, created


class InvalidModerationTransition(ValueError):
    pass


def review_case(*, case_id, actor, to_status, note):
    if not is_platform_operator(actor):
        raise PermissionError("Platform operator required")
    if not note or len(note.strip()) < 10 or len(note.strip()) > 1000:
        raise ValidationError("A review note between 10 and 1000 characters is required")
    if to_status not in (ModerationCase.Status.IN_REVIEW, ModerationCase.Status.CLOSED):
        raise InvalidModerationTransition("Unsupported moderation transition")
    with transaction.atomic():
        case = ModerationCase.objects.select_for_update().get(pk=case_id)
        if case.status == to_status:
            return case, False
        valid = (
            (
                case.status == ModerationCase.Status.OPEN
                and to_status == ModerationCase.Status.IN_REVIEW
            )
            or (
                case.status == ModerationCase.Status.IN_REVIEW
                and to_status == ModerationCase.Status.CLOSED
            )
        )
        if not valid:
            raise InvalidModerationTransition("Case transition is not allowed")
        old = case.status
        case.status = to_status
        case.save(update_fields=["status", "updated_at"])
        ModerationDecision.objects.create(
            case=case, actor=actor, from_status=old,
            to_status=to_status, note=note.strip(),
        )
        return case, True
