import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import F, Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("games", "0001_initial"),
        ("gaming_centers", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Season",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                    verbose_name="ID")),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("label", models.CharField(max_length=160)),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField()),
                ("is_published", models.BooleanField(default=False)),
            ],
            options={"ordering": ["-starts_at", "slug"]},
        ),
        migrations.CreateModel(
            name="PublicRankingIdentity",
            fields=[
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,
                    primary_key=True, related_name="ranking_identity", serialize=False,
                    to=settings.AUTH_USER_MODEL)),
                ("username", models.CharField(max_length=64, unique=True)),
                ("is_published", models.BooleanField(default=False)),
                ("search_visibility", models.CharField(choices=[("indexable", "Indexable"),
                    ("noindex", "Noindex")], default="noindex", max_length=12)),
                ("city", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name="ranking_identities", to="gaming_centers.city")),
            ],
        ),
        migrations.CreateModel(
            name="PlayerRating",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True,
                    serialize=False)),
                ("kind", models.CharField(choices=[("tournament", "Tournament"), ("challenge",
                    "Challenge")], max_length=12)),
                ("rating", models.PositiveIntegerField(default=1000)),
                ("played", models.PositiveIntegerField(default=0)),
                ("wins", models.PositiveIntegerField(default=0)),
                ("losses", models.PositiveIntegerField(default=0)),
                ("draws", models.PositiveIntegerField(default=0)),
                ("last_finalized_at", models.DateTimeField(blank=True, null=True)),
                ("game", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    to="games.game")),
                ("season", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    to="rankings.season")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name="competitive_ratings", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="AppliedMatchEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True,
                    serialize=False)),
                ("source_event_id", models.UUIDField(unique=True)),
                ("source_match_id", models.UUIDField(unique=True)),
                ("source_digest", models.CharField(max_length=64)),
                ("kind", models.CharField(choices=[("tournament", "Tournament"), ("challenge",
                    "Challenge")], max_length=12)),
                ("source_id", models.CharField(max_length=128)),
                ("competition_title", models.CharField(max_length=200)),
                ("timezone", models.CharField(default="Asia/Tehran", max_length=64)),
                ("score_a", models.PositiveIntegerField()),
                ("score_b", models.PositiveIntegerField()),
                ("rating_a_before", models.PositiveIntegerField()),
                ("rating_b_before", models.PositiveIntegerField()),
                ("rating_a_after", models.PositiveIntegerField()),
                ("rating_b_after", models.PositiveIntegerField()),
                ("finalized_at", models.DateTimeField()),
                ("applied_at", models.DateTimeField(auto_now_add=True)),
                ("game", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    to="games.game")),
                ("season", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    to="rankings.season")),
                ("user_a", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name="rating_events_a", to=settings.AUTH_USER_MODEL)),
                ("user_b", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name="rating_events_b", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="publicrankingidentity",
            constraint=models.CheckConstraint(
                condition=Q(username__regex=r"^[a-z0-9][a-z0-9_-]{1,63}$"),
                name="b09_username_ascii_pattern",
            ),
        ),
        migrations.AddConstraint(
            model_name="season",
            constraint=models.CheckConstraint(condition=Q(ends_at__gt=F("starts_at")),
                name="b09_season_window"),
        ),
        migrations.AddConstraint(
            model_name="playerrating",
            constraint=models.UniqueConstraint(fields=("user", "game", "season", "kind"),
                name="b09_player_rating_scope"),
        ),
        migrations.AddConstraint(
            model_name="playerrating",
            constraint=models.CheckConstraint(
                condition=Q(played=F("wins") + F("losses") + F("draws")),
                name="b09_rating_record_sum",
            ),
        ),
        migrations.AddConstraint(
            model_name="appliedmatchevent",
            constraint=models.CheckConstraint(condition=~Q(user_a=F("user_b")),
                name="b09_event_distinct_players"),
        ),
        migrations.AddIndex(
            model_name="playerrating",
            index=models.Index(fields=["game", "season", "kind", "-rating", "user"],
                name="b09_leaderboard_idx"),
        ),
        migrations.AddIndex(
            model_name="appliedmatchevent",
            index=models.Index(fields=["user_a", "-finalized_at"], name="b09_event_a_recent_idx"),
        ),
        migrations.AddIndex(
            model_name="appliedmatchevent",
            index=models.Index(fields=["user_b", "-finalized_at"], name="b09_event_b_recent_idx"),
        ),
        migrations.AddIndex(
            model_name="appliedmatchevent",
            index=models.Index(fields=["game", "season", "kind", "-finalized_at"],
                name="b09_event_scope_recent_idx"),
        ),
    ]
