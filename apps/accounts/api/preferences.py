from django.db import transaction
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import NotificationPreference


class SavePreferencesSerializer(serializers.Serializer):
    revision = serializers.CharField(max_length=128)
    optional = serializers.DictField()

    def validate_optional(self, value):
        if set(value) != {"tournament", "match", "challenge"}:
            raise serializers.ValidationError("Exactly three optional preferences are required.")
        if any(type(v) is not bool for v in value.values()):
            raise serializers.ValidationError("Preferences must be booleans.")
        return value


def project(obj):
    return {
        "revision": str(obj.revision),
        "optional": {
            "tournament": obj.tournament,
            "match": obj.match,
            "challenge": obj.challenge,
        },
        "required": {"account": True, "system": True},
    }


class NotificationPreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        value, _ = NotificationPreference.objects.get_or_create(user=request.user)
        return Response(project(value))

    def patch(self, request):
        serializer = SavePreferencesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            value, _ = NotificationPreference.objects.get_or_create(user=request.user)
            value = NotificationPreference.objects.select_for_update().get(pk=value.pk)
            if serializer.validated_data["revision"] != str(value.revision):
                return Response({
                    "outcome": "stale",
                    "message": "تنظیمات در نشست دیگری تغییر کرده است.",
                    "settings": project(value),
                }, status=409)
            optional = serializer.validated_data["optional"]
            if any(getattr(value, key) != flag for key, flag in optional.items()):
                for key, flag in optional.items():
                    setattr(value, key, flag)
                value.revision += 1
                value.save(update_fields=["tournament", "match", "challenge", "revision"])
            return Response({"outcome": "saved", "settings": project(value)})
