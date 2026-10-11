import uuid

from django.conf import settings
from django.db import models


class Registration(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(
        "tournaments.Tournament", on_delete=models.PROTECT, related_name="registrations"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tournament_registrations"
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.CONFIRMED
    )
    team_id = models.CharField(max_length=128, blank=True)
    team_name = models.CharField(max_length=240, blank=True)
    team_role = models.CharField(max_length=12, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tournament", "user"], name="b05_registration_one_per_user"
            ),
            models.UniqueConstraint(
                fields=["tournament", "team_id"],
                condition=models.Q(status="confirmed") & ~models.Q(team_id=""),
                name="b05_one_active_team_per_tournament"
            ),
        ]
