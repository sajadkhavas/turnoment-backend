import base64
from urllib.parse import urlsplit

from django.conf import settings
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PushSubscription


def valid_subscription(data):
    if not isinstance(data, dict):
        return False
    endpoint = data.get("endpoint")
    keys = data.get("keys")
    if not isinstance(endpoint, str) or len(endpoint) > 2048 or not isinstance(keys, dict):
        return False
    try:
        url = urlsplit(endpoint)
        if (
            url.scheme != "https"
            or url.username
            or url.password
            or url.fragment
            or url.port not in (None, 443)
            or url.hostname not in settings.PUSH_ALLOWED_HOSTS
        ):
            return False
        for key, length in (("p256dh", 65), ("auth", 16)):
            value = keys.get(key)
            if not isinstance(value, str) or len(value) > 200:
                return False
            decoded = base64.b64decode(
                value + "=" * (-len(value) % 4), altchars=b"-_", validate=True
            )
            if len(decoded) != length or (key == "p256dh" and decoded[0] != 4):
                return False
    except (ValueError, TypeError):
        return False
    return True


class PushConfigurationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ready = bool(
            settings.PUSH_VAPID_PUBLIC_KEY
            and settings.PUSH_VAPID_PRIVATE_KEY
            and settings.PUSH_VAPID_SUBJECT
        )
        return Response(
            {"enabled": ready, "publicKey": settings.PUSH_VAPID_PUBLIC_KEY if ready else ""}
        )


class PushSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        if not valid_subscription(request.data):
            return Response({"detail": "Invalid subscription"}, status=400)
        data = request.data
        old = PushSubscription.objects.select_for_update().filter(endpoint=data["endpoint"]).first()
        if old and old.recipient_id != request.user.pk:
            return Response({"detail": "Unsubscribe the previous account first"}, status=409)
        sub, _ = PushSubscription.objects.update_or_create(
            endpoint=data["endpoint"],
            defaults={
                "recipient": request.user,
                "p256dh": data["keys"]["p256dh"],
                "auth": data["keys"]["auth"],
                "active": True,
            },
        )
        return Response({"outcome": "subscribed", "subscriptionId": str(sub.pk)})

    def delete(self, request):
        if not isinstance(request.data, dict) or not isinstance(request.data.get("endpoint"), str):
            return Response({"detail": "Invalid request"}, status=400)
        PushSubscription.objects.filter(
            recipient=request.user,
            endpoint=request.data["endpoint"],
        ).update(active=False)
        return Response({"outcome": "unsubscribed"})
