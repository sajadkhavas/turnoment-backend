from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User

from .models import Notification


def emit_notification(
    *, recipient_id, event_key: str, kind: str, title: str, body: str,
    target_kind: str = "", target_id: str = "", occurred_at=None,
):
    """Synchronous replay-safe projection, called only after owning business truth exists.

    All read-state mutations and emission lock the recipient to serialize unread counts.
    A conflicting replay is rejected rather than silently changing delivered content.
    """
    occurred_at = occurred_at or timezone.now()
    with transaction.atomic():
        User.objects.select_for_update().get(pk=recipient_id)
        defaults = dict(
            kind=kind, title=title, body=body, target_kind=target_kind,
            target_id=target_id, occurred_at=occurred_at,
        )
        probe = Notification(recipient_id=recipient_id, event_key=event_key, **defaults)
        probe.full_clean(validate_unique=False, validate_constraints=False)
        notification, created = Notification.objects.get_or_create(
            recipient_id=recipient_id, event_key=event_key, defaults=defaults
        )
        if not created and any(
            getattr(notification, field) != defaults[field]
            for field in ("kind", "title", "body", "target_kind", "target_id")
        ):
            raise ValueError("Conflicting notification event replay")
        return notification, created


def mark_one_read(*, recipient_id, notification_id):
    with transaction.atomic():
        User.objects.select_for_update().get(pk=recipient_id)
        notification = Notification.objects.select_for_update().get(
            pk=notification_id, recipient_id=recipient_id
        )
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at"])
        unread = Notification.objects.filter(recipient_id=recipient_id, read_at__isnull=True).count()
        return notification, unread


def mark_all_read(*, recipient_id):
    with transaction.atomic():
        User.objects.select_for_update().get(pk=recipient_id)
        now = timezone.now()
        updated = Notification.objects.filter(
            recipient_id=recipient_id, read_at__isnull=True
        ).update(read_at=now)
        unread = Notification.objects.filter(recipient_id=recipient_id, read_at__isnull=True).count()
        return updated, now, unread
