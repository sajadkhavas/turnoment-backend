from django.db.models import Case, CharField, OuterRef, Subquery, Value, When
from django.db.models.functions import Coalesce, NullIf

from apps.gaming_centers.models import CenterMembership
from apps.matches.models import Match
from apps.tournaments.models import Tournament


def with_result_venue(queryset):
    tournament_venue = Tournament.objects.filter(slug=OuterRef("tournament_slug")).exclude(
        center_key=""
    ).values("center_key")[:1]

    return queryset.annotate(
        result_venue_key=Coalesce(
            Case(When(source_kind=Match.Source.TOURNAMENT, then=Subquery(tournament_venue)),
                 output_field=CharField()),
            NullIf("venue_id", Value("")),
            Value(""),
        )
    )


def is_venue_managed(match):
    if not hasattr(match, "result_venue_key"):
        match.result_venue_key = with_result_venue(Match.objects.filter(pk=match.pk)).values_list(
            "result_venue_key", flat=True
        ).get()
    return bool(match.result_venue_key)


def result_managers(user):
    return CenterMembership.objects.filter(
        user=user, is_active=True,
        role__in=(CenterMembership.Role.OWNER, CenterMembership.Role.MANAGER)
    )
