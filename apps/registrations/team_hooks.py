from django.conf import settings
from django.utils.module_loading import import_string

from apps.teams.services import tournament_eligible_teams


def eligible_teams(user, tournament):
    dotted_path = getattr(settings, "TOURNAMENT_TEAM_ELIGIBILITY_HOOK", "")
    resolver = import_string(dotted_path) if dotted_path else tournament_eligible_teams
    return list(resolver(user, tournament))
