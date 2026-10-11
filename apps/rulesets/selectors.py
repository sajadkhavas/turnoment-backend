from django.db.models import Q

from .models import Ruleset


def published_rulesets():
    return Ruleset.objects.filter(
        publication_state=Ruleset.Publication.PUBLISHED
    ).filter(Q(game__isnull=True) | Q(game__publication_state="published")).select_related("game")


def policy_summary(rule):
    return {
        "policyId": str(rule.pk),
        "gameId": rule.game_id,
        "key": rule.key,
        "revision": rule.revision,
        "title": rule.title,
        "summary": rule.summary,
        "effectiveDate": rule.effective_on.isoformat() if rule.effective_on else None,
    }


def policy_detail(rule):
    return {
        "schemaVersion": 1,
        "publicationState": "published",
        **policy_summary(rule),
        "sections": rule.sections,
    }
