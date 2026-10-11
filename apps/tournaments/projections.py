import hashlib
import math
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db.models import F, Q
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


def _city_key(name, metadata):
    key = metadata.get("cityKey")
    if key and isinstance(key, str) and key.isascii() and key.replace("-", "").isalnum():
        return key
    digest = hashlib.sha1(name.encode()).hexdigest()[:12]
    return f"city-{digest}"


def city_key(t):
    return _city_key(t.center_city, t.center_meta)


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
    # Keep pagination/filtering on PostgreSQL; never hydrate the full tournament table.
    # Facets stream distinct metadata rows, keeping only the supported top 100 identities.
    games = {}
    cities = {}
    city_variants = {}
    metadata_rows = Tournament.objects.values(
        "game_key", "game_slug", "game_name", "center_city", "center_meta"
    ).distinct()
    for row in metadata_rows.iterator(chunk_size=1000):
        game_id = row["game_key"]
        if game_id not in games and len(games) < 100:
            games[game_id] = {
                "gameId": game_id, "slug": row["game_slug"],
                "name": row["game_name"],
            }
        city = row["center_city"]
        metadata = row["center_meta"]
        city_id = _city_key(city, metadata)
        if city_id not in cities and len(cities) < 100:
            cities[city_id] = {"value": city_id, "label": city}
        if query.get("city") == city_id:
            city_variants[(city, repr(sorted(metadata.items())))] = (city, metadata)

    qs = Tournament.objects.all()
    if query.get("game"):
        qs = qs.filter(game_key=query["game"])
    if query.get("city"):
        match = Q(pk__in=[])
        for name, metadata in city_variants.values():
            match |= Q(center_city=name, center_meta=metadata)
        qs = qs.filter(match)
    if query.get("verified"):
        qs = qs.filter(center_verified=True)

    day_filter = query.get("date")
    if day_filter:
        today = timezone.now().astimezone(TEHRAN).date()
        days = [today + timedelta(days=offset) for offset in range(7)]
        if day_filter == "today":
            days = days[:1]
        elif day_filter == "tomorrow":
            days = days[1:2]
        elif day_filter == "weekend":
            days = [day for day in days if day.weekday() in {3, 4}]
        selection = Q(pk__in=[])
        for day in days:
            start = datetime.combine(day, time.min, tzinfo=TEHRAN)
            end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=TEHRAN)
            selection |= Q(starts_at__gte=start, starts_at__lt=end)
        qs = qs.filter(selection)

    fmt = query.get("format")
    if fmt == "team":
        qs = qs.filter(mode=Tournament.Mode.TEAM)
    elif fmt == "1v1":
        qs = qs.filter(mode=Tournament.Mode.SOLO)
    elif fmt:
        qs = qs.filter(
            Q(bracket_format_label__icontains=fmt)
            | Q(bracket_format_label__icontains=fmt.replace("-", " "))
        )

    price = query.get("price")
    if price == "free":
        qs = qs.filter(entry_fee=0)
    elif price == "lt300":
        qs = qs.filter(entry_fee__gt=0, entry_fee__lt=3_000_000)
    elif price == "300-500":
        qs = qs.filter(entry_fee__gte=3_000_000, entry_fee__lte=5_000_000)
    elif price == "gt500":
        qs = qs.filter(entry_fee__gt=5_000_000)

    desired = query.get("status")
    if desired:
        eligible = (
            Q(entry_fee=0)
            & Q(lifecycle__in=[Tournament.Lifecycle.OPEN, Tournament.Lifecycle.FILLING])
            & Q(registered_count__lt=F("capacity"))
            & (
                Q(registration_closes_at__isnull=True)
                | Q(registration_closes_at__gt=timezone.now())
            )
        )
        if desired == "open":
            qs = qs.filter(eligible, lifecycle=Tournament.Lifecycle.OPEN)
        elif desired == "filling":
            qs = qs.filter(eligible, lifecycle=Tournament.Lifecycle.FILLING)
        elif desired == "upcoming":
            qs = qs.filter(entry_fee=0, lifecycle=Tournament.Lifecycle.UPCOMING)
        elif desired == "closed":
            qs = qs.exclude(
                Q(entry_fee__gt=0)
                | Q(lifecycle=Tournament.Lifecycle.UPCOMING)
                | eligible
            )

    sort = query.get("sort", "suggested")
    if sort == "limited":
        qs = qs.annotate(
            remaining_slots=F("capacity") - F("registered_count")
        ).order_by("remaining_slots", "id")
    elif sort == "cheapest":
        qs = qs.order_by("entry_fee", "id")
    elif sort == "prize":
        qs = qs.order_by("-fixed_prize", "id")
    else:
        qs = qs.order_by("starts_at", "id")

    total = qs.count()
    pages = max(1, math.ceil(total / PAGE_SIZE))
    page = min(query.get("page", 1), pages)
    current = list(qs[(page - 1) * PAGE_SIZE:page * PAGE_SIZE])
    active = {
        "verified": query.get("verified", False),
        "sort": sort,
        "page": query.get("page", 1),
    }
    for key in ("game", "city", "date", "status", "format", "price"):
        if query.get(key):
            active[key] = query[key]
    return {
        "schemaVersion": 1,
        "filters": {
            "games": list(games.values()),
            "cities": list(cities.values()),
        },
        "activeQuery": active,
        "featuredTournamentId": str(current[0].id) if current else None,
        "items": [discovery_item(t) for t in current],
        "pagination": {
            "currentPage": page, "totalPages": pages,
            "totalItems": total, "pageSize": PAGE_SIZE,
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
