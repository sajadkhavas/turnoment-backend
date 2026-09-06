import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone

from .managers import UserManager
from .phone import validate_iran_mobile


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(
        max_length=13,
        unique=True,
        validators=[validate_iran_mobile],
    )
    email = models.EmailField(unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.phone


class PlayerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="player_profile",
    )
    gamer_tag = models.CharField(max_length=24, null=True, blank=True)
    display_name = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=80, blank=True)
    bio = models.CharField(max_length=280, blank=True)
    interview_opt_in = models.BooleanField(default=False)
    avatar_key = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("gamer_tag"),
                condition=Q(gamer_tag__isnull=False),
                name="accounts_profile_gamer_tag_ci_unique",
            )
        ]

    def __str__(self) -> str:
        return self.gamer_tag or self.user.phone


class OtpChallenge(models.Model):
    class Purpose(models.TextChoices):
        LOGIN = "login", "Login"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(
        max_length=13,
        db_index=True,
        validators=[validate_iran_mobile],
    )
    purpose = models.CharField(max_length=24, choices=Purpose.choices)
    code_hash = models.CharField(max_length=128)
    attempts_remaining = models.PositiveSmallIntegerField(default=5)
    request_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["phone", "-created_at"], name="acct_otp_phone_created_idx"),
            models.Index(fields=["expires_at"], name="acct_otp_expires_idx"),
        ]
        ordering = ["-created_at"]


class OtpRequestState(models.Model):
    phone = models.CharField(
        max_length=13,
        primary_key=True,
        validators=[validate_iran_mobile],
    )
    last_sent_at = models.DateTimeField(null=True, blank=True)
    window_started_at = models.DateTimeField(null=True, blank=True)
    request_count = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.phone
