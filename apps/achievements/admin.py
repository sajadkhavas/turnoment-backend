from django.contrib import admin

from .models import (
    AchievementCategory,
    AchievementDefinition,
    AchievementProgress,
    AchievementProgressEvent,
)

admin.site.register(AchievementCategory)
admin.site.register(AchievementDefinition)


@admin.register(AchievementProgress)
class AchievementProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "definition", "current", "unlocked_at")
    readonly_fields = ("user", "definition", "current", "unlocked_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AchievementProgressEvent)
class AchievementProgressEventAdmin(admin.ModelAdmin):
    list_display = ("user", "definition", "event_key", "created_at")
    readonly_fields = ("user", "definition", "event_key", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
