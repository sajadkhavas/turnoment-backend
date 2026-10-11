from django.db import transaction

from apps.tournaments.models import Tournament
from apps.tournaments.services import availability

from .models import Registration
from .team_hooks import eligible_teams


@transaction.atomic
def register(*, identifier, user, payload):
    # Lock the parent BEFORE inspecting capacity or duplicate membership.
    tournament = Tournament.objects.select_for_update().get(
        slug=identifier
    ) if not _is_uuid(identifier) else Tournament.objects.select_for_update().get(id=identifier)
    if tournament.finance_pending:
        return {
            "outcome": "unavailable", "reason": "ineligible",
            "backendState": "BACKEND_PENDING_FINANCE"
        }
    previous = Registration.objects.filter(tournament=tournament, user=user).first()
    if previous and previous.status == Registration.Status.CONFIRMED:
        return {"outcome": "already_registered", "registrationId": str(previous.id)}
    if (
        payload["detailVersion"] != tournament.detail_version
        or payload["rulesVersion"] != tournament.rules_version
    ):
        return {"outcome": "stale", "detailVersion": tournament.detail_version}
    if not payload["acceptedRules"]:
        return {"outcome": "validation_error", "fields": {"acceptedRules": "Required"}}

    team_id = payload.get("teamId")
    chosen = None
    if tournament.mode == Tournament.Mode.TEAM:
        if not team_id:
            return {"outcome": "validation_error", "fields": {"teamId": "Required"}}
        chosen = next(
            (team for team in eligible_teams(user, tournament)
             if team["id"] == team_id and team["role"] == "captain"),
            None
        )
        if chosen is None:
            return {"outcome": "unavailable", "reason": "ineligible"}
        if Registration.objects.filter(
            tournament=tournament, status=Registration.Status.CONFIRMED,
            team_id=team_id
        ).exclude(user=user).exists():
            return {"outcome": "unavailable", "reason": "ineligible"}
    elif team_id is not None:
        return {"outcome": "validation_error", "fields": {"teamId": "Must be null"}}

    state = availability(tournament)
    if state != "available":
        return {"outcome": "unavailable", "reason": state}

    if previous:
        previous.status = Registration.Status.CONFIRMED
        previous.team_id = team_id or ""
        previous.team_name = chosen["name"] if chosen else ""
        previous.team_role = "captain" if chosen else ""
        previous.save(update_fields=["status", "team_id", "team_name", "team_role"])
        registration = previous
    else:
        registration = Registration.objects.create(
            tournament=tournament, user=user,
            team_id=team_id or "",
            team_name=chosen["name"] if chosen else "",
            team_role="captain" if chosen else "",
        )
    tournament.registered_count += 1
    tournament.save(update_fields=["registered_count"])
    return {
        "outcome": "confirmed",
        "registrationId": str(registration.id),
        "status": "confirmed"
    }


def _is_uuid(value):
    import uuid

    try:
        uuid.UUID(str(value))
    except ValueError:
        return False
    return True
