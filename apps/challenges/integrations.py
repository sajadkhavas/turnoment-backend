"""B03/B08/B09 contracts; missing providers fail closed, never fake business truth.

B99 must connect the owning domains: B03 active game/format policy,
B02/B08 opponent eligibility, B08 finalized-valid-match counts,
B09 challenge rating, and B08 synchronous match creation. The B08 creator
MUST run in our current database transaction, keyed uniquely by challenge.id,
and return the existing match_id on replay. Never queue match creation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerChallengeStats:
    finalized_valid_matches: int = 0
    challenge_rating: int | None = None


@dataclass(frozen=True)
class FormatChoice:
    format_id: str
    label: str


@dataclass(frozen=True)
class GameChoice:
    game_id: str
    name: str
    formats: tuple[FormatChoice, ...]


class MatchServiceUnavailable(Exception):
    """Integration dependency unavailable, challenge must stay pending."""


def player_challenge_stats(user) -> PlayerChallengeStats:
    """Count only B08 completed, persisted finalized results; no synthetic unlock."""
    from django.db.models import Q

    from apps.matches.models import Match
    from apps.rankings.models import PlayerRating
    from apps.results.models import FinalizedResultEvent

    if not user.is_authenticated or not user.is_active:
        return PlayerChallengeStats()
    finalized = FinalizedResultEvent.objects.filter(
        Q(player_a_id=user.pk) | Q(player_b_id=user.pk),
        match__state=Match.State.COMPLETED,
    ).count()
    scoped = list(
        PlayerRating.objects.filter(
            user=user, kind=PlayerRating.Kind.CHALLENGE,
            season__is_published=True,
        ).values_list("rating", flat=True)[:2]
    )
    # Never imply one global rating across several seasons or game scopes.
    rating = scoped[0] if len(scoped) == 1 else None
    return PlayerChallengeStats(finalized, rating)


def match_creator_ready() -> bool:
    """Blocked until B99 approves a real in-person start-time contract."""
    return False


def creation_games(user) -> tuple[GameChoice, ...]:
    """Offer only published B03 games with solo-compatible formats.

    Exposing a game never bypasses the finalized-match eligibility gate.
    """
    from apps.games.selectors import published_games

    if not user.is_active:
        return ()
    choices = []
    for game in published_games().prefetch_related("competitive_formats")[:100]:
        formats = tuple(
            FormatChoice(format_id=fmt.key, label=fmt.label)
            for fmt in game.competitive_formats.all()
            if fmt.team_size in (None, 1)
        )
        if formats:
            choices.append(GameChoice(game_id=game.pk, name=game.name, formats=formats))
    return tuple(choices)


def opponent_eligible(challenger, opponent, game_id: str) -> bool:
    """Only active players with a real public tag and 30 finalized B08 games."""
    from apps.accounts.models import PlayerProfile
    from apps.games.models import Game

    if (
        not challenger.is_active or not opponent.is_active
        or challenger.pk == opponent.pk
    ):
        return False
    if not Game.objects.filter(
        pk=game_id, publication_state=Game.Publication.PUBLISHED,
    ).exists():
        return False
    if not PlayerProfile.objects.filter(
        user=opponent, gamer_tag__isnull=False
    ).exclude(gamer_tag="").exists():
        return False
    return player_challenge_stats(opponent).finalized_valid_matches >= 30


def create_match_for_challenge(challenge) -> str:
    raise MatchServiceUnavailable("B08 match creation service not wired")
