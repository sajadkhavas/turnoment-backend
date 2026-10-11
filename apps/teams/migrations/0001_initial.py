import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Team",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4,
                    editable=False, serialize=False)),
                ("name", models.CharField(max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_teams", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
        migrations.CreateModel(
            name="TeamMembership",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4,
                    editable=False, serialize=False)),
                ("role", models.CharField(max_length=8, choices=[("captain", "Captain"),
                    ("member", "Member")], default="member")),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("team", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name="memberships", to="teams.team")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name="team_memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [models.Index(fields=["user", "team"], name="b06_team_member_lookup")],
                "constraints": [
                    models.UniqueConstraint(fields=("team", "user"), name="b06_unique_team_member"),
                    models.UniqueConstraint(fields=("team",), condition=models.Q(("role",
                        "captain")), name="b06_one_team_captain"),
                ],
            },
        ),
        migrations.CreateModel(
            name="TeamInvite",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4,
                    editable=False, serialize=False)),
                ("state", models.CharField(max_length=12, choices=[("pending",
                    "Pending"), ("accepted", "Accepted"), ("declined", "Declined"),
                        ("revoked", "Revoked")], default="pending")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("responded_at", models.DateTimeField(null=True, blank=True)),
                ("invited_by",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                        related_name="sent_team_invitations", to=settings.AUTH_USER_MODEL)),
                ("recipient",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                        related_name="team_invitations", to=settings.AUTH_USER_MODEL)),
                ("team", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name="invites", to="teams.team")),
            ],
            options={
                "indexes": [models.Index(fields=["recipient", "state"],
                    name="b06_invite_recipient_state")],
                "constraints": [models.UniqueConstraint(fields=("team", "recipient"),
                    condition=models.Q(("state", "pending")), name="b06_one_pending_team_invite")],
            },
        ),
    ]
