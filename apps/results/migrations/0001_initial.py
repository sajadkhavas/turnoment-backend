import uuid

from django.conf import settings
from django.db import migrations, models
from django.db.models import Q
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("matches", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(name="MatchResult", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("idempotency_key", models.CharField(max_length=200)),
            ("score_a", models.PositiveIntegerField()),
            ("score_b", models.PositiveIntegerField()),
            ("reported_at", models.DateTimeField(auto_now_add=True)),
            ("finalized_at", models.DateTimeField(blank=True, null=True)),
            ("confirmed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="confirmed_results", to=settings.AUTH_USER_MODEL)),
            ("match", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="result", to="matches.match")),
            ("reported_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="reported_results", to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="FinalizedResultEvent", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("score_a", models.PositiveIntegerField()),
            ("score_b", models.PositiveIntegerField()),
            ("player_a_id", models.UUIDField()),
            ("player_b_id", models.UUIDField()),
            ("finalized_at", models.DateTimeField()),
            ("match", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="finalization_event", to="matches.match")),
            ("result", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="finalization_event", to="results.matchresult")),
        ]),
        migrations.AddConstraint(model_name="matchresult", constraint=models.CheckConstraint(condition=Q(finalized_at__isnull=True) | Q(confirmed_by__isnull=False), name="b08_confirm_before_final")),
        migrations.AddIndex(model_name="finalizedresultevent", index=models.Index(fields=["finalized_at"], name="b08_final_event_idx")),
    ]
