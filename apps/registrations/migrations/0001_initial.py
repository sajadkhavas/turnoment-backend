import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tournaments", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Registration",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(
                    choices=[("confirmed", "Confirmed"), ("cancelled", "Cancelled")],
                    default="confirmed", max_length=12
                )),
                ("team_id", models.CharField(blank=True, max_length=128)),
                ("team_name", models.CharField(blank=True, max_length=240)),
                ("team_role", models.CharField(blank=True, max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tournament", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="registrations", to="tournaments.tournament"
                )),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="tournament_registrations", to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                "constraints": [models.UniqueConstraint(
                    fields=("tournament", "user"), name="b05_registration_one_per_user"
                )],
            },
        ),
    ]
