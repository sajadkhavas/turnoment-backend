"""Explicit external delivery; disabled SMS is never reported as sent."""

import json
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.module_loading import import_string

from .models import NotificationDelivery


class DisabledSmsSender:
    def send(self, *, phone, message, key):
        return False


def target_url(notification):
    routes = {
        "my-matches": "/dashboard/matches",
        "my-challenges": "/dashboard/challenges",
        "my-teams": "/dashboard/teams",
        "my-achievements": "/dashboard/achievements",
        "my-tournaments": "/dashboard/tournaments",
        "player-profile": "/dashboard/profile",
        "result-submission": "/matches/{}/result",
        "match-dispute": "/matches/{}/dispute",
        "tournament-detail": "/tournaments/{}",
    }
    template = routes.get(notification.target_kind, "/dashboard/notifications")
    return template.format(quote(notification.target_id, safe=""))


def dispatch_one():
    with transaction.atomic():
        item = (
            NotificationDelivery.objects.select_for_update(skip_locked=True)
            .filter(state__in=["pending", "retry"], next_attempt_at__lte=timezone.now())
            .order_by("pk")
            .first()
        )
        if item is None:
            return False
        item.attempts += 1
        notification = item.notification
        try:
            if item.channel == "sms":
                if settings.NOTIFICATION_SMS_BACKEND.endswith("DisabledSmsSender"):
                    item.state = "disabled"
                else:
                    sender = import_string(settings.NOTIFICATION_SMS_BACKEND)()
                    sent = sender.send(
                        phone=notification.recipient.phone,
                        message=notification.title + "\n" + notification.body,
                        key=str(item.pk),
                    )
                    if not sent:
                        raise RuntimeError("SMS not acknowledged")
                    item.state = "sent"
            else:
                sub = item.subscription
                if not sub or not sub.active:
                    item.state = "expired"
                elif not settings.PUSH_VAPID_PRIVATE_KEY or not settings.PUSH_VAPID_SUBJECT:
                    item.state = "retry"
                    item.last_error = "push_not_configured"
                    item.next_attempt_at = timezone.now() + timedelta(minutes=5)
                else:
                    from pywebpush import WebPushException, webpush

                    try:
                        webpush(
                            subscription_info={
                                "endpoint": sub.endpoint,
                                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                            },
                            data=json.dumps(
                                {
                                    "title": notification.title,
                                    "body": notification.body,
                                    "url": target_url(notification),
                                    "tag": str(notification.pk),
                                }
                            ),
                            vapid_private_key=settings.PUSH_VAPID_PRIVATE_KEY,
                            vapid_claims={"sub": settings.PUSH_VAPID_SUBJECT},
                            timeout=10,
                            ttl=3600,
                        )
                        item.state = "sent"
                    except WebPushException as exc:
                        if exc.response is not None and exc.response.status_code in (404, 410):
                            sub.active = False
                            sub.save(update_fields=["active"])
                            item.state = "expired"
                        else:
                            raise
            if item.state == "sent":
                item.sent_at = timezone.now()
                item.last_error = ""
        except Exception:
            # Do not persist provider exception text: it can contain endpoints or tokens.
            item.state = "failed" if item.attempts >= 8 else "retry"
            item.last_error = "provider_failed"
            item.next_attempt_at = timezone.now() + timedelta(
                seconds=min(3600, 30 * 2**item.attempts)
            )
        item.save()
        return True
