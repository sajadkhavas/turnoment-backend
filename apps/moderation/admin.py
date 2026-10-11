from django.contrib import admin

from .models import ModerationCase, ModerationDecision


@admin.register(ModerationCase)
class ModerationCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "source_type", "source_id", "center_id", "status", "opened_at")
    list_filter = ("source_type", "status")
    search_fields = ("source_id", "center_id", "title")
    readonly_fields = tuple(field.name for field in ModerationCase._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ModerationDecision)
class ModerationDecisionAdmin(admin.ModelAdmin):
    list_display = ("id", "case", "actor", "from_status", "to_status", "created_at")
    list_filter = ("from_status", "to_status")
    readonly_fields = tuple(field.name for field in ModerationDecision._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
