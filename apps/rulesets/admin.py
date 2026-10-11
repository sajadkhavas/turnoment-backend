from django.contrib import admin

from .models import Ruleset


@admin.register(Ruleset)
class RulesetAdmin(admin.ModelAdmin):
    list_display = ("key", "revision", "publication_state", "game", "effective_on")
    list_filter = ("publication_state",)
    search_fields = ("key", "title", "game__slug")
    readonly_fields = ("id", "created_at", "updated_at")
