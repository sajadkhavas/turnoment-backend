import re

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.models import PlayerProfile, User
from apps.accounts.phone import normalize_iran_mobile

_GAMER_TAG_RE = re.compile(r"^[A-Za-z0-9_.-]{3,24}$")


class OtpRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)

    def validate_phone(self, value: str) -> str:
        try:
            return normalize_iran_mobile(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages[0]) from exc


class OtpVerifySerializer(serializers.Serializer):
    challenge_id = serializers.UUIDField()
    code = serializers.RegexField(r"^\d{6}$")


class PrivatePlayerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerProfile
        fields = [
            "gamer_tag",
            "display_name",
            "city",
            "bio",
            "interview_opt_in",
            "avatar_key",
        ]
        read_only_fields = ["avatar_key"]

    def validate_gamer_tag(self, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if not _GAMER_TAG_RE.fullmatch(value):
            raise serializers.ValidationError(
                "شناسه بازیکن باید ۳ تا ۲۴ کاراکتر و فقط شامل حروف لاتین، عدد، نقطه، خط تیره یا زیرخط باشد."
            )

        queryset = PlayerProfile.objects.filter(gamer_tag__iexact=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("این شناسه بازیکن قبلاً استفاده شده است.")
        return value


class MeSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    platform_roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "email",
            "is_active",
            "date_joined",
            "platform_roles",
            "profile",
        ]
        read_only_fields = fields

    def get_profile(self, obj: User) -> dict:
        profile, _ = PlayerProfile.objects.get_or_create(user=obj)
        return PrivatePlayerProfileSerializer(profile).data

    def get_platform_roles(self, obj: User) -> list[str]:
        return list(obj.groups.order_by("name").values_list("name", flat=True))


class PublicPlayerSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="user_id", read_only=True)

    class Meta:
        model = PlayerProfile
        fields = ["id", "gamer_tag", "display_name", "city", "bio", "avatar_key"]
        read_only_fields = fields
