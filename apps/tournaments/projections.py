import hashlib
import math
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from apps.brackets.models import BracketRound
from apps.registrations.models import Registration

from .models import Tournament
from .services import availability

TEHRAN = ZoneInfo("Asia/Tehran")
PAGE_SIZE = 12


def iso(value):
    return value.isoformat()


def money(value):
    return {"amount": value, "currency": "IRR"}


def capacity(t):
    return {
        "limit": t.capacity, "registered": t.registered_count,
        "remaining": t.capacity - t.registered_count
    }


def gamer_tag(reg):
    try:
        profile = reg.user.player_profile
    except AttributeError:
        profile = None
    return (profile.gamer_tag if profile and profile.gamer_tag else f"Player-{reg.user_id!s}"[:15])


def city_key(t):
    key = t.center_meta.get("cityKey")
    if key and isinstance(key, str) and key.isascii() and key.replace("-", "").isalnum():
        return key
    digest = hashlib.sha1(t.center_city.encode()).hexdigest()[:12]
    return f"city-{digest}"


def game(t):
    return {"gameId": t.game_key, "slug": t.game_slug, "name": t.game_name}


def registration_state(t):
    state = availability(t)
    if state == "available":
        return "filling" if t.lifecycle == t.Lifecycle.FILLING else "open"
    if state == "full":
        return "closed"
    if state == "upcoming":
        return "upcoming"
    return "unavailable" if t.finance_pending else "closed"


def discovery_item(t):
    return {
        "tournamentId": str(t.id), "tournamentSlug": t.slug, "title": t.title,
        "game": game(t),
        "venue": {
            "gamingCenterId": t.center_key, "name": t.center_name,
            "verified": t.center_verified, "city": t.center_city,
            "district": t.center_district
        },
        "lifecycleState": t.lifecycle,
        "registrationState": registration_state(t),
        "startsAt": iso(t.starts_at), "timezone": "Asia/Tehran",
        "displayDate": t.display_date, "displayTime": t.display_time,
        "formatLabel": t.format_label, "bracketFormatLabel": t.bracket_format_label,
        "capacity": capacity(t), "entryFee": money(t.entry_fee),
        "fixedPrize": money(t.fixed_prize),
    }


def _date_match(t, day, now):
    local = t.starts_at.astimezone(TEHRAN).date()
    today = now.astimezone(TEHRAN).date()
    if day == "today":
        return local == today
    if day == "tomorrow":
        return local == today + timedelta(days=1)
    if day == "week":
        return today <= local < today + timedelta(days=7)
    if day == "weekend":
        return local.weekday() in {3, 4} and today <= local < today + timedelta(days=7)
    return True


def discovery(query):
    all_items = list(Tournament.objects.all())
    games = {
        t.game_key: game(t) for t in all_items
    }
    cities = {
        city_key(t): {"value": city_key(t), "label": t.center_city}
        for t in all_items
    }
    results = list(all_items)
    if query.get("game"):
        results = [t for t in results if t.game_key == query["game"]]
    if query.get("city"):
        results = [t for t in results if city_key(t) == query["city"]]
    if query.get("verified"):
        results = [t for t in results if t.center_verified]
    if query.get("date"):
        now = timezone.now()
        results = [t for t in results if _date_match(t, query["date"], now)]
    if query.get("status"):
        results = [t for t in results if registration_state(t) == query["status"]]
    if query.get("format"):
        fmt = query["format"]
        results = [
            t for t in results
            if (t.mode == "team" if fmt == "team" else
                t.mode == "solo" if fmt == "1v1" else
                fmt in t.bracket_format_label.lower().replace(" ", "-"))
        ]
    if query.get("price"):
        bands = {
            "free": lambda n: n == 0,
            "lt300": lambda n: 0 < n < 3_000_000,
            "300-500": lambda n: 3_000_000 <= n <= 5_000_000,
            "gt500": lambda n: n > 5_000_000
        }
        results = [t for t in results if bands[query["price"]](t.entry_fee)]
    sort = query.get("sort", "suggested")
    sort_key = {
        "soonest": lambda t: (t.starts_at, str(t.id)),
        "limited": lambda t: (t.capacity - t.registered_count, str(t.id)),
        "cheapest": lambda t: (t.entry_fee, str(t.id)),
        "prize": lambda t: (-t.fixed_prize, str(t.id))
    }.get(sort, lambda t: (t.starts_at, str(t.id)))
    results.sort(key=sort_key)
    total = len(results)
    pages = max(1, math.ceil(total / PAGE_SIZE))
    page = min(query.get("page", 1), pages)
    page_items = results[(page - 1) * PAGE_SIZE:page * PAGE_SIZE]
    active = {
        "verified": query.get("verified", False),
        "sort": sort, "page": query.get("page", 1)
    }
    for key in ("game", "city", "date", "status", "format", "price"):
        if query.get(key):
            active[key] = query[key]
    return {
        "schemaVersion": 1,
        "filters": {
            "games": list(games.values())[:100],
            "cities": list(cities.values())[:100]
        },
        "activeQuery": active,
        "featuredTournamentId": str(page_items[0].id) if page_items else None,
        "items": [discovery_item(t) for t in page_items],
        "pagination": {
            "currentPage": page, "totalPages": pages, "totalItems": total,
            "pageSize": PAGE_SIZE
        },
    }


def bracket_preview(t):
    rounds = list(
        BracketRound.objects.filter(tournament=t)
        .prefetch_related("matches__side_a__user__player_profile",
                          "matches__side_b__user__player_profile")[:3]
    )
    projected = []
    states = []
    for round_obj in rounds:
        matches = []
        for match in list(round_obj.matches.all())[:4]:
            states.append(match.state)

            def competitor(reg, score):
                if reg is None:
                    return None
                return {
                    "participantId": str(reg.id), "gamerTag": gamer_tag(reg),
                    "seed": None, "score": score
                }

            matches.append({
                "id": str(match.id), "label": match.label, "state": match.state,
                "sideA": competitor(match.side_a, match.score_a),
                "sideB": competitor(match.side_b, match.score_b)
            })
        projected.append({
            "id": str(round_obj.id), "title": round_obj.title, "matches": matches
        })
    state = "not_published"
    if projected:
        state = "live" if "live" in states else (
            "completed" if states and all(s == "completed" for s in states) else "seeded"
        )
    return {
        "state": state, "formatLabel": t.bracket_format_label,
        "participantCount": t.registered_count, "rounds": projected
    }


def detail(t):
    participants = list(
        Registration.objects.filter(tournament=t, status="confirmed")
        .select_related("user", "user__player_profile").order_by("created_at")[:8]
    )
    center = t.center_meta
    state = availability(t)
    return {
        "id": str(t.id), "slug": t.slug, "detailVersion": t.detail_version,
        "title": t.title, "description": t.description,
        "heroImage": t.hero_image or None, "lifecycle": t.lifecycle,
        "game": {
            "id": t.game_key, "name": t.game_name, "platform": t.game_platform,
            "image": t.game_image or None
        },
        "venue": {
            "id": t.center_key, "name": t.center_name,
            "verified": t.center_verified, "rating": center.get("rating"),
            "reviews": center.get("reviews"), "city": t.center_city,
            "district": t.center_district, "image": center.get("image"),
            "equipment": center.get("equipment", [])
        },
        "schedule": {
            "startAt": iso(t.starts_at), "registrationClosesAt": (
                iso(t.registration_closes_at) if t.registration_closes_at else None
            ),
            "checkInOpensAt": iso(t.check_in_opens_at) if t.check_in_opens_at else None,
            "timezone": "Asia/Tehran",
            "displayDate": t.display_date, "displayTime": t.display_time,
        },
        "formatLabel": t.format_label, "bracketFormatLabel": t.bracket_format_label,
        "capacity": capacity(t), "entryFee": money(t.entry_fee),
        "fixedPrize": money(t.fixed_prize),
        "ruleset": {
            "id": t.ruleset_key, "version": t.rules_version, "rules": t.rules
        },
        "participants": {
            "total": t.registered_count,
            "preview": [
                {"id": str(reg.id), "gamerTag": gamer_tag(reg),
                 "seed": None, "status": (
                     "checked_in" if hasattr(reg, "checkin") else "confirmed"
                 )}
                for reg in participants
            ]
        },
        "bracketPreview": bracket_preview(t),
        "registrationPolicy": {
            "state": (
                "full" if state == "full" else "upcoming" if state == "upcoming"
                else "open" if state == "available" else "closed"
            ),
            "mode": t.mode, "rulesVersion": t.rules_version,
            "requiresRulesAcceptance": True
        }
    }


def context(t, user):
    from apps.registrations.team_hooks import eligible_teams

    reg = Registration.objects.filter(tournament=t, user=user, status="confirmed").first()
    try:
        profile = user.player_profile
    except AttributeError:
        profile = None
    return {
        "detailVersion": t.detail_version,
        "tournament": {
            "id": str(t.id), "slug": t.slug, "title": t.title,
            "game": t.game_name, "venue": t.center_name,
            "displayDate": t.display_date, "displayTime": t.display_time,
            "entryFee": money(t.entry_fee), "fixedPrize": money(t.fixed_prize),
        },
        "player": {
            "id": str(user.pk),
            "gamerTag": (
                profile.gamer_tag if profile and profile.gamer_tag else f"Player-{str(user.pk)[:8]}"
            )
        },
        "availability": "already_registered" if reg else availability(t),
        "mode": t.mode,
        "rules": {
            "version": t.rules_version,
            "summary": "با ثبت‌نام، قوانین این نسخه را می‌پذیرید."
        },
        "eligibleTeams": [
            {
                "id": team["id"], "name": team["name"],
                "memberCount": team["memberCount"]
            }
            for team in eligible_teams(user, t)
        ] if t.mode == t.Mode.TEAM and not t.finance_pending else [],
        "currentRegistration": (
            {"id": str(reg.id), "status": "confirmed", "createdAt": iso(reg.created_at)}
            if reg else None
        )
    }
