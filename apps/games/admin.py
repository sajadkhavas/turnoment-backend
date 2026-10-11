from django.contrib import admin

from .models import CompetitiveFormat, Game


class CompetitiveFormatInline(admin.TabularInline):
    model = CompetitiveFormat
    extra = 0


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name", "publication_state", "sort_order")
    list_filter = ("publication_state",)
    search_fields = ("id", "slug", "name", "short_name")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [CompetitiveFormatInline]
