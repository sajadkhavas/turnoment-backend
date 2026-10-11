from django.db import models


class CheckIn(models.Model):
    registration = models.OneToOneField(
        "registrations.Registration", primary_key=True,
        on_delete=models.PROTECT, related_name="checkin"
    )
    checked_at = models.DateTimeField(auto_now_add=True)
