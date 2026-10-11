"""Serialized, private team lifecycle transitions; no tournament or match internals."""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Team, TeamInvite, TeamMembership


class TeamConflict(ValidationError):
    status_code = 409
    default_code = "team_conflict"


def _captain(team, user):
    if not TeamMembership.objects.filter(
        team=team, user=user, role=TeamMembership.Role.CAPTAIN
    ).exists():
        raise PermissionDenied("Team captain permission required.")


@transaction.atomic
def create_team(*, user, name):
    """Creating a team and its only captain is atomic."""
    team = Team.objects.create(name=name, created_by=user)
    TeamMembership.objects.create(team=team, user=user, role=TeamMembership.Role.CAPTAIN)
    return team


@transaction.atomic
def invite(*, actor, team_id, recipient_id):
    team = get_object_or_404(Team.objects.select_for_update(), pk=team_id)
    _captain(team, actor)
    if actor.pk == recipient_id:
        raise TeamConflict("You cannot invite yourself.")
    # Do not reveal private recipient identity in the API response.
    recipient = get_object_or_404(
        get_user_model(), pk=recipient_id, is_active=True
    )
    if TeamMembership.objects.filter(team=team, user=recipient).exists():
        raise TeamConflict("Player is already a member.")
    existing = TeamInvite.objects.filter(
        team=team, recipient=recipient, state=TeamInvite.State.PENDING
    ).first()
    if existing:
        return existing, False
    return TeamInvite.objects.create(
        team=team, recipient=recipient, invited_by=actor
    ), True


@transaction.atomic
def respond(*, actor, invite_id, accept: bool):
    lookup = get_object_or_404(TeamInvite, pk=invite_id, recipient=actor)
    Team.objects.select_for_update().get(pk=lookup.team_id)
    invitation = TeamInvite.objects.select_for_update().get(pk=lookup.pk)
    desired = TeamInvite.State.ACCEPTED if accept else TeamInvite.State.DECLINED
    if invitation.state == desired:
        return invitation  # safe replay
    if invitation.state != TeamInvite.State.PENDING:
        raise TeamConflict("Invitation already resolved.")
    if accept:
        if TeamMembership.objects.filter(team_id=invitation.team_id, user=actor).exists():
            raise TeamConflict("Player is already a member.")
        TeamMembership.objects.create(
            team_id=invitation.team_id, user=actor, role=TeamMembership.Role.MEMBER
        )
    invitation.state = desired
    invitation.responded_at = timezone.now()
    invitation.save(update_fields=["state", "responded_at"])
    return invitation


@transaction.atomic
def transfer_captain(*, actor, team_id, new_captain_id):
    team = get_object_or_404(Team.objects.select_for_update(), pk=team_id)
    _captain(team, actor)
    target = get_object_or_404(
        TeamMembership.objects.select_for_update(), team=team, user_id=new_captain_id
    )
    if target.user_id == actor.pk:
        return target  # replay while still captain
    previous = TeamMembership.objects.select_for_update().get(
        team=team, user=actor, role=TeamMembership.Role.CAPTAIN
    )
    previous.role = TeamMembership.Role.MEMBER
    previous.save(update_fields=["role"])
    target.role = TeamMembership.Role.CAPTAIN
    target.save(update_fields=["role"])
    return target


@transaction.atomic
def leave(*, actor, team_id):
    team = get_object_or_404(Team.objects.select_for_update(), pk=team_id)
    member = get_object_or_404(TeamMembership, team=team, user=actor)
    if member.role == TeamMembership.Role.CAPTAIN:
        raise TeamConflict("Transfer captaincy before leaving.")
    member.delete()


def tournament_eligible_teams(user, tournament):
    """Read-only B05 hook: candidate captained teams, not a registration authorization.

    B99 must validate tournament-specific composition/game eligibility in the
    owning integration service before enabling actual team registration.
    """
    if getattr(tournament, "mode", None) != "team" or not user.is_authenticated:
        return []
    memberships = TeamMembership.objects.filter(
        user=user, role=TeamMembership.Role.CAPTAIN
    ).select_related("team")
    return [
        {
            "id": str(item.team_id),
            "name": item.team.name,
            "memberCount": TeamMembership.objects.filter(team_id=item.team_id).count(),
            "role": item.role,
        }
        for item in memberships
    ]
