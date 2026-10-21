"""Transactional inbox projection; no network traffic in business transactions."""

from django.utils import timezone

from .models import Notification


def notify(recipients, key, kind, title, body, target_kind="", target_id=""):
    # Database uniqueness handles concurrent replay without acquiring user locks
    # after domain locks (which would reverse challenge/user lock ordering).
    for recipient in sorted(set(recipients), key=str):
        Notification.objects.get_or_create(
            recipient_id=recipient,
            event_key=key,
            defaults={
                "kind": kind,
                "title": title,
                "body": body,
                "target_kind": target_kind,
                "target_id": target_id,
                "occurred_at": timezone.now(),
            },
        )
