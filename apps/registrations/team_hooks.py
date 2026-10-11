from django.conf import settings
from django.utils.module_loading import import_string


def eligible_teams(user, tournament):
    """B06 integration seam. Fail closed until a real team-membership adapter is installed.

    Adapter signature: (user, tournament) -> iterable of dicts with id, name,
    memberCount and role ('captain' or 'member'). Only captain may register.
    """
    dotted_path = getattr(settings, "TOURNAMENT_TEAM_ELIGIBILITY_HOOK", "")
    if not dotted_path:
        return []
    return list(import_string(dotted_path)(user, tournament))
