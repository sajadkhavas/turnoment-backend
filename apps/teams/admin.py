from django.contrib import admin

from .models import Team, TeamInvite, TeamMembership


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_by", "created_at")
    search_fields = ("name",)
    readonly_fields = ("id", "created_at")


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ("team", "user", "role", "joined_at")
    readonly_fields = ("id", "joined_at")


@admin.register(TeamInvite)
class TeamInviteAdmin(admin.ModelAdmin):
    list_display = ("team", "recipient", "state", "created_at")
    readonly_fields = ("id", "created_at", "responded_at")
