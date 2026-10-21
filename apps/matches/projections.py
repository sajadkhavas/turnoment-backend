from django.db.models import Q

from apps.accounts.models import PlayerProfile

from .models import Match


def tag(user):
    profile = getattr(user, "player_profile", None)
    return (
        (profile.gamer_tag or profile.display_name)
        if profile and (profile.gamer_tag or profile.display_name)
        else str(user.pk)
    )


def opponent(match, user):
    return match.participant_b if match.participant_a_id == user.pk else match.participant_a


def common(match, user):
    other = opponent(match, user)
    competition = {
        "kind": match.source_kind,
        "competitionId": match.source_id,
        "title": match.competition_title,
        "roundLabel": match.round_label if match.source_kind == "tournament" else None,
    }
    if match.source_kind == "tournament":
        competition["tournamentSlug"] = match.tournament_slug
    return {
        "matchId": str(match.pk),
        "player": {"participantId": str(user.pk), "displayTag": tag(user)},
        "opponent": {"participantId": str(other.pk), "kind": "player", "displayTag": tag(other)},
        "game": {"gameId": match.game_id, "name": match.game_name},
        "competition": competition,
        "venue": (
            {"gamingCenterId": match.venue_id, "name": match.venue_name, "city": match.venue_city}
            if match.venue_id
            else None
        ),
        "startsAt": match.starts_at.isoformat(),
        "timezone": match.timezone,
        "formatLabel": match.format_label,
    }


def visible_matches(user):
    return (
        Match.objects.filter(Q(participant_a=user) | Q(participant_b=user))
        .select_related(
            "participant_a__player_profile", "participant_b__player_profile", "result", "dispute"
        )
        .order_by("-starts_at", "-created_at")
    )


def current_result(match):
    return getattr(match, "result", None)


def current_dispute(match):
    return getattr(match, "dispute", None)


def final_for(match, user):
    from apps.results.projections import final_result

    result = current_result(match)
    return final_result(match, result, user) if result and result.finalized_at else None


def result_state(match):
    if match.state == Match.State.CANCELLED:
        return "void"
    if match.state == Match.State.COMPLETED:
        return "finalized"
    if match.state == Match.State.DISPUTED:
        return "disputed"
    if match.state == Match.State.AWAITING_CONFIRMATION:
        return "awaiting-confirmation"
    if match.state == Match.State.AWAITING_RESULT:
        return "reportable"
    return "not-open"


def dispute_state(match):
    dispute = current_dispute(match)
    return dispute.status if dispute else "none"


def attention(match, user):
    state = result_state(match)
    if state == "reportable":
        return "submit-result"
    if state == "awaiting-confirmation":
        result = current_result(match)
        return "confirm-result" if result and result.reported_by_id != user.pk else "none"
    if state == "disputed":
        return "dispute"
    if match.check_in_state == "open":
        return "check-in"
    return "none"


def match_item(match, user):
    data = common(match, user)
    data.pop("player")
    data.update(
        {
            "lifecycleState": match.state,
            "revision": str(match.revision),
            "canControlLifecycle": bool(
                match.source_kind == Match.Source.CHALLENGE
                and match.has_participant(user)
                and match.state in (Match.State.READY, Match.State.LIVE)
            ),
            "checkInState": match.check_in_state,
            "resultState": result_state(match),
            "disputeState": dispute_state(match),
            "attention": attention(match, user),
            "result": final_for(match, user),
        }
    )
    return data


def current_player(user):
    profile = PlayerProfile.objects.filter(user=user).first()
    return {
        "playerId": str(user.pk),
        "gamerTag": (profile.gamer_tag or profile.display_name if profile else None)
        or str(user.pk),
    }
