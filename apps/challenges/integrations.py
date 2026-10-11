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
    return PlayerChallengeStats()


def creation_games(user) -> tuple[GameChoice, ...]:
    return ()


def opponent_eligible(challenger, opponent, game_id: str) -> bool:
    return False


def create_match_for_challenge(challenge) -> str:
    raise MatchServiceUnavailable("B08 match creation service not wired")
