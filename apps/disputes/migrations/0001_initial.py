import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("matches", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="Dispute",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("idempotency_key", models.CharField(max_length=200)),
                ("reason", models.CharField(max_length=32)),
                ("statement", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Open"),
                            ("under-review", "Under review"),
                            ("resolved", "Resolved"),
                        ],
                        default="open",
                        max_length=16,
                    ),
                ),
                ("review_locked", models.BooleanField(default=False)),
                ("decision", models.CharField(blank=True, max_length=16)),
                ("resolution_summary", models.TextField(blank=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="raised_disputes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "match",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="dispute",
                        to="matches.match",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DisputeEvidence",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("idempotency_key", models.CharField(max_length=200)),
                ("file_name", models.CharField(max_length=160)),
                ("content_type", models.CharField(max_length=32)),
                ("size_bytes", models.PositiveIntegerField()),
                ("quarantined_bytes", models.BinaryField()),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "dispute",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="evidence",
                        to="disputes.dispute",
                    ),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="dispute_evidence",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="dispute",
            constraint=models.CheckConstraint(
                condition=Q(status="resolved", resolved_at__isnull=False)
                | ~Q(status="resolved", resolved_at__isnull=True),
                name="b08_dispute_resolution_ts",
            ),
        ),
        migrations.AddConstraint(
            model_name="disputeevidence",
            constraint=models.UniqueConstraint(
                fields=("dispute", "uploaded_by", "idempotency_key"),
                name="b08_evidence_retry_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="disputeevidence",
            constraint=models.CheckConstraint(
                condition=Q(size_bytes__gt=0), name="b08_evidence_nonempty"
            ),
        ),
    ]
