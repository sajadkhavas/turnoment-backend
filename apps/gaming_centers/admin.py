from django.contrib import admin

from .models import CenterMembership, City, GamingCenter, HostApplication, HostRateBucket


@admin.register(GamingCenter)
class GamingCenterAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "publication_state", "verified")
    list_filter = ("publication_state", "verified")
    search_fields = ("name", "public_id")


@admin.register(HostApplication)
class HostApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "venue_name", "city", "state", "submitted_at")
    readonly_fields = (
        "venue_name", "manager_name", "phone", "city", "area", "station_count",
        "games", "description", "submitted_at", "client_key", "fingerprint", "bucket_start",
    )
    list_filter = ("state",)


admin.site.register(City)
admin.site.register(CenterMembership)
admin.site.register(HostRateBucket)
