import uuid

from django.db import models


class BracketRound(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(
        "tournaments.Tournament", on_delete=models.PROTECT, related_name="bracket_rounds"
    )
    number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=100)

    class Meta:
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(
                fields=["tournament", "number"], name="b05_round_number_unique"
            ),
        ]


class BracketMatch(models.Model):
    class State(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        LIVE = "live", "Live"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    round = models.ForeignKey(
        BracketRound, on_delete=models.PROTECT, related_name="matches"
    )
    position = models.PositiveSmallIntegerField()
    label = models.CharField(max_length=100)
    state = models.CharField(max_length=12, choices=State.choices, default=State.SCHEDULED)
    side_a = models.ForeignKey(
        "registrations.Registration", null=True, blank=True,
        on_delete=models.PROTECT, related_name="bracket_side_a"
    )
    side_b = models.ForeignKey(
        "registrations.Registration", null=True, blank=True,
        on_delete=models.PROTECT, related_name="bracket_side_b"
    )
    score_a = models.PositiveSmallIntegerField(null=True, blank=True)
    score_b = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["round", "position"], name="b05_match_position_unique"
            ),
            models.CheckConstraint(
                condition=~models.Q(side_a=models.F("side_b")) | models.Q(side_a__isnull=True)
                | models.Q(side_b__isnull=True),
                name="b05_no_self_bracket"
            ),
        ]
