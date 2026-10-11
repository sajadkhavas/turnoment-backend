import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("tournament", models.BooleanField(default=True)),
                ("match", models.BooleanField(default=True)),
                ("challenge", models.BooleanField(default=True)),
                ("revision", models.PositiveIntegerField(default=1)),
                ("user", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="notification_preference",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
