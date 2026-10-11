import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower

from apps.gaming_centers.models import GamingCenter


class Equipment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey(GamingCenter, on_delete=models.CASCADE, related_name="equipment")
    label = models.CharField(max_length=240)
    is_public = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("label"), "center", name="equip_center_label_ci")
        ]
        ordering = ["label", "id"]


class Station(models.Model):
    class State(models.TextChoices):
        ACTIVE = "active", "Active"
        MAINTENANCE = "maintenance", "Maintenance"
        DISABLED = "disabled", "Disabled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey(GamingCenter, on_delete=models.CASCADE, related_name="stations")
    equipment = models.ForeignKey(
        Equipment, on_delete=models.PROTECT, related_name="stations"
    )
    code = models.CharField(max_length=40)
    state = models.CharField(max_length=12, choices=State.choices, default=State.ACTIVE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["center", "code"], name="station_center_code_unique")
        ]

    def clean(self):
        if self.equipment_id and self.center_id and self.equipment.center_id != self.center_id:
            raise ValidationError("Station equipment belongs to a different center.")


class OpeningHour(models.Model):
    center = models.ForeignKey(GamingCenter, on_delete=models.CASCADE, related_name="hours")
    weekday = models.PositiveSmallIntegerField()
    opens = models.TimeField()
    closes = models.TimeField()
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ["weekday"]
        constraints = [
            models.UniqueConstraint(fields=["center", "weekday"], name="center_unique_weekday"),
            models.CheckConstraint(
                condition=Q(weekday__lte=6), name="center_weekday_range"
            ),
            models.CheckConstraint(
                condition=Q(closes__gt=F("opens")), name="center_hours_order"
            ),
        ]


class GalleryImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    center = models.ForeignKey(GamingCenter, on_delete=models.CASCADE, related_name="gallery")
    image_url = models.URLField(max_length=2048)
    position = models.PositiveSmallIntegerField()
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["center", "image_url"], name="center_gallery_url_unique"),
            models.UniqueConstraint(fields=["center", "position"], name="center_gallery_pos_unique"),
            models.CheckConstraint(condition=Q(position__lte=7), name="center_gallery_pos_range"),
        ]
