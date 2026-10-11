import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Team(models.Model):
    """Private team identity; no public roster endpoint."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_teams"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class TeamMembership(models.Model):
    class Role(models.TextChoices):
        CAPTAIN = "captain", "Captain"
        MEMBER = "member", "Member"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_memberships"
    )
    role = models.CharField(max_length=8, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["team", "user"], name="b06_unique_team_member"),
            models.UniqueConstraint(
                fields=["team"], condition=Q(role="captain"), name="b06_one_team_captain"
            ),
        ]
        indexes = [models.Index(fields=["user", "team"], name="b06_team_member_lookup")]


class TeamInvite(models.Model):
    class State(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        REVOKED = "revoked", "Revoked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="invites")
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_invitations"
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sent_team_invitations"
    )
    state = models.CharField(max_length=12, choices=State.choices, default=State.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "recipient"], condition=Q(state="pending"),
                name="b06_one_pending_team_invite"
            )
        ]
        indexes = [
            models.Index(fields=["recipient", "state"], name="b06_invite_recipient_state")
        ]
