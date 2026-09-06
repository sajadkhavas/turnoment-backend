from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import OtpChallenge, OtpRequestState, PlayerProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["phone", "email", "is_active", "is_staff", "date_joined"]
    search_fields = ["phone", "email"]
    readonly_fields = ["date_joined", "last_login"]
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Contact", {"fields": ("email",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )
    filter_horizontal = ["groups", "user_permissions"]


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ["gamer_tag", "display_name", "city", "user", "updated_at"]
    search_fields = ["gamer_tag", "display_name", "user__phone"]
    list_filter = ["city", "interview_opt_in"]


@admin.register(OtpChallenge)
class OtpChallengeAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "phone",
        "purpose",
        "attempts_remaining",
        "created_at",
        "expires_at",
        "consumed_at",
    ]
    search_fields = ["phone"]
    list_filter = ["purpose"]
    readonly_fields = [field.name for field in OtpChallenge._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(OtpRequestState)
class OtpRequestStateAdmin(admin.ModelAdmin):
    list_display = ["phone", "request_count", "last_sent_at", "window_started_at", "updated_at"]
    search_fields = ["phone"]
    readonly_fields = [field.name for field in OtpRequestState._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
