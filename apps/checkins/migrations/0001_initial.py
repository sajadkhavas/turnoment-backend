from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [("registrations", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="CheckIn",
            fields=[
                ("registration", models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    primary_key=True, related_name="checkin",
                    serialize=False, to="registrations.registration"
                )),
                ("checked_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
