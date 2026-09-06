import uuid

import apps.accounts.managers
import apps.accounts.phone
import django.db.models.deletion
import django.db.models.functions.text
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="OtpRequestState",
            fields=[
                (
                    "phone",
                    models.CharField(
                        max_length=13,
                        primary_key=True,
                        serialize=False,
                        validators=[apps.accounts.phone.validate_iran_mobile],
                    ),
                ),
                ("last_sent_at", models.DateTimeField(blank=True, null=True)),
                ("window_started_at", models.DateTimeField(blank=True, null=True)),
                ("request_count", models.PositiveSmallIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(blank=True, null=True, verbose_name="last login"),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        max_length=13,
                        unique=True,
                        validators=[apps.accounts.phone.validate_iran_mobile],
                    ),
                ),
                ("email", models.EmailField(blank=True, max_length=254, null=True, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={"ordering": ["-date_joined"]},
            managers=[("objects", apps.accounts.managers.UserManager())],
        ),
        migrations.CreateModel(
            name="OtpChallenge",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        db_index=True,
                        max_length=13,
                        validators=[apps.accounts.phone.validate_iran_mobile],
                    ),
                ),
                ("purpose", models.CharField(choices=[("login", "Login")], max_length=24)),
                ("code_hash", models.CharField(max_length=128)),
                ("attempts_remaining", models.PositiveSmallIntegerField(default=5)),
                ("request_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["phone", "-created_at"],
                        name="acct_otp_phone_created_idx",
                    ),
                    models.Index(fields=["expires_at"], name="acct_otp_expires_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="PlayerProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("gamer_tag", models.CharField(blank=True, max_length=24, null=True)),
                ("display_name", models.CharField(blank=True, max_length=80)),
                ("city", models.CharField(blank=True, max_length=80)),
                ("bio", models.CharField(blank=True, max_length=280)),
                ("interview_opt_in", models.BooleanField(default=False)),
                ("avatar_key", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="player_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="playerprofile",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("gamer_tag"),
                condition=models.Q(("gamer_tag__isnull", False)),
                name="accounts_profile_gamer_tag_ci_unique",
            ),
        ),
    ]
