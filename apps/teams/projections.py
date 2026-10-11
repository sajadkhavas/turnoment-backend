"""Private current-player team hub projection matching frozen F14 v1."""

import math
import re

from django.db.models import Count
from rest_framework.exceptions import ValidationError

from .models import TeamMembership

PAGE_SIZE = 12
STABLE_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def player_label(user):
    profile = getattr(user, "player_profile", None)
    if profile and profile.gamer_tag:
        return profile.gamer_tag
    # A stable non-PII placeholder until the user configures their gamer tag.
    return "player-" + user.pk.hex[:12]


def _pagination(page, total):
    pages = max(1, math.ceil(total / PAGE_SIZE))
    return min(page, pages), pages


def _page(query):
    if not isinstance(query, str) or not re.fullmatch(r"[0-9]{1,8}", query):
        raise ValidationError({"page": ["Must be a positive integer."]})
    page = int(query)
    if page < 1:
        raise ValidationError({"page": ["Must be a positive integer."]})
    return page


def team_page(user, params):
    if set(params) - {"team", "page"} or any(len(params.getlist(k)) != 1 for k in params):
        raise ValidationError({"query": ["Unknown or duplicate query parameter."]})
    requested = params.get("team")
    if requested is not None and not STABLE_ID.fullmatch(requested):
        raise ValidationError({"team": ["Invalid stable team identifier."]})
    page = _page(params.get("page", "1"))

    memberships = list(
        TeamMembership.objects.filter(user=user)
        .select_related("team")
        .annotate(member_count=Count("team__memberships"))
        .order_by("joined_at", "id")
    )
    switcher = [
        {"teamId": str(m.team_id), "name": m.team.name,
         "role": m.role, "memberCount": m.member_count}
        for m in memberships
    ]
    captain_count = sum(m.role == TeamMembership.Role.CAPTAIN for m in memberships)
    result = {
        "player": {"playerId": str(user.pk), "gamerTag": player_label(user)},
        "summary": {
            "totalTeams": len(switcher), "captainOf": captain_count,
            "memberOf": len(switcher) - captain_count,
        },
        "memberships": switcher,
        "selectionState": "none" if not switcher else "unavailable",
        "selectedTeam": None,
    }
    chosen = next(
        (m for m in memberships if str(m.team_id) == requested), None
    ) if requested is not None else (memberships[0] if memberships else None)
    if chosen is None:
        return result  # external team IDs are indistinguishable from nonexistent IDs

    roster_qs = (
        TeamMembership.objects.filter(team_id=chosen.team_id)
        .select_related("user", "user__player_profile")
        .order_by("joined_at", "id")
    )
    total = roster_qs.count()
    current, pages = _pagination(page, total)
    roster = [
        {"playerId": str(m.user_id), "gamerTag": player_label(m.user), "role": m.role}
        for m in roster_qs[(current - 1) * PAGE_SIZE:current * PAGE_SIZE]
    ]
    result["selectionState"] = "selected"
    result["selectedTeam"] = {
        "teamId": str(chosen.team_id), "name": chosen.team.name,
        "currentPlayerRole": chosen.role, "memberCount": total,
        "roster": roster,
        "rosterPagination": {
            "currentPage": current, "totalPages": pages, "totalItems": total
        },
    }
    return result
