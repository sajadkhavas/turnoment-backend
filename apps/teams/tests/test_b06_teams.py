from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from django.db import IntegrityError, connections, transaction
from rest_framework.test import APIClient

from apps.accounts.models import PlayerProfile, User
from apps.teams.models import Team, TeamInvite, TeamMembership
from apps.teams.services import (
    TeamConflict, create_team, invite, respond, tournament_eligible_teams,
    transfer_captain,
)

ME = "/api/v1/me/teams/"
TEAM = "/api/v1/teams/"


def player(num, tag=None):
    user = User.objects.create_user(phone=f"0912{num:07d}")
    PlayerProfile.objects.create(user=user, gamer_tag=tag or f"P{num:07d}")
    return user


def authed(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.mark.django_db
def test_team_projection_selection_private_roster_and_counts():
    owner, teammate, outsider = player(1), player(2), player(3)
    first = create_team(user=owner, name="Alpha")
    second = create_team(user=owner, name="Bravo")
    TeamMembership.objects.create(team=first, user=teammate)
    before = authed(owner).get(ME)
    assert before.status_code == 200
    data = before.data
    assert data["summary"] == {"totalTeams": 2, "captainOf": 2, "memberOf": 0}
    assert data["selectionState"] == "selected"
    assert data["selectedTeam"]["teamId"] == str(first.pk)
    assert data["selectedTeam"]["memberCount"] == 2
    assert data["selectedTeam"]["rosterPagination"] == {
        "currentPage": 1, "totalPages": 1, "totalItems": 2,
    }
    assert {entry["role"] for entry in data["selectedTeam"]["roster"]} == {
        "captain", "member"
    }
    assert "phone" not in str(data)
    assert "email" not in str(data)
    other = authed(teammate).get(ME, {"team": str(second.pk)})
    assert other.status_code == 200
    assert other.data["selectionState"] == "unavailable"
    assert other.data["selectedTeam"] is None
    fake = authed(teammate).get(ME, {"team": str(uuid4())})
    assert fake.data == other.data
    assert authed(outsider).get(ME).data["selectionState"] == "none"
    assert APIClient().get(ME).status_code in (401, 403)


@pytest.mark.django_db
def test_team_query_validation_and_roster_pagination():
    owner = player(4)
    team = create_team(user=owner, name="Large")
    for num in range(10, 24):
        TeamMembership.objects.create(team=team, user=player(num))
    data = authed(owner).get(ME, {"page": "2"}).data["selectedTeam"]
    assert data["memberCount"] == 15
    assert data["rosterPagination"] == {
        "currentPage": 2, "totalPages": 2, "totalItems": 15,
    }
    assert len(data["roster"]) == 3
    assert authed(owner).get(ME, {"page": "200"}).data[
        "selectedTeam"
    ]["rosterPagination"]["currentPage"] == 2
    for query in ({"page": "0"}, {"page": "-1"}, {"page": "abc"}, {"foo": "x"},
                  {"team": "not a uuid!"}):
        assert authed(owner).get(ME, query).status_code == 400
    assert authed(owner).get(ME + "?page=1&page=2").status_code == 400


@pytest.mark.django_db
def test_create_invite_accept_replay_and_scoped_invite_read():
    owner, guest, stranger = player(24), player(25), player(26)
    made = authed(owner).post(TEAM, {"name": "Winners"}, format="json")
    assert made.status_code == 201
    tid = made.data["teamId"]
    denied = authed(stranger).post(
        f"{TEAM}{tid}/invites/", {"playerId": str(guest.pk)}, format="json"
    )
    assert denied.status_code == 403
    endpoint = f"{TEAM}{tid}/invites/"
    first = authed(owner).post(endpoint, {"playerId": str(guest.pk)}, format="json")
    again = authed(owner).post(endpoint, {"playerId": str(guest.pk)}, format="json")
    assert first.status_code == 201
    assert again.status_code == 200
    assert first.data == again.data
    invite_id = first.data["inviteId"]
    assert authed(stranger).get("/api/v1/me/team-invites/").data == {"items": []}
    assert len(authed(guest).get("/api/v1/me/team-invites/").data["items"]) == 1
    url = f"{TEAM}invites/{invite_id}/accept/"
    assert authed(stranger).post(url, {}, format="json").status_code == 404
    accepted = authed(guest).post(url, {}, format="json")
    assert accepted.status_code == 200
    assert accepted.data["state"] == "accepted"
    assert authed(guest).post(url, {}, format="json").data == accepted.data
    assert TeamMembership.objects.filter(team_id=tid, user=guest).count() == 1
    assert authed(guest).get("/api/v1/me/team-invites/").data["items"] == []
    assert authed(owner).post(endpoint, {"playerId": str(guest.pk)}, format="json").status_code == 409


@pytest.mark.django_db
def test_decline_transfer_captain_and_leave_guards():
    owner, guest, outsider = player(27), player(28), player(29)
    team = create_team(user=owner, name="Guardians")
    invited, _ = invite(actor=owner, team_id=team.pk, recipient_id=outsider.pk)
    result = authed(outsider).post(
        f"{TEAM}invites/{invited.pk}/decline/", {}, format="json"
    )
    assert result.data["state"] == "declined"
    assert authed(outsider).post(
        f"{TEAM}invites/{invited.pk}/decline/", {}, format="json"
    ).status_code == 200
    assert authed(outsider).post(
        f"{TEAM}invites/{invited.pk}/accept/", {}, format="json"
    ).status_code == 409
    assert not TeamMembership.objects.filter(team=team, user=outsider).exists()
    assert authed(owner).post(f"{TEAM}{team.pk}/leave/", {}, format="json").status_code == 409
    TeamMembership.objects.create(team=team, user=guest)
    transfer_url = f"{TEAM}{team.pk}/captain/"
    assert authed(outsider).post(
        transfer_url, {"playerId": str(guest.pk)}, format="json"
    ).status_code == 403
    assert authed(owner).post(
        transfer_url, {"playerId": str(outsider.pk)}, format="json"
    ).status_code == 404
    assert authed(owner).post(
        transfer_url, {"playerId": str(guest.pk)}, format="json"
    ).status_code == 200
    assert TeamMembership.objects.filter(team=team, role="captain").count() == 1
    assert TeamMembership.objects.get(team=team, role="captain").user_id == guest.pk
    assert authed(owner).post(f"{TEAM}{team.pk}/leave/", {}, format="json").status_code == 204
    assert TeamMembership.objects.filter(team=team).count() == 1
    assert authed(guest).post(f"{TEAM}{team.pk}/leave/", {}, format="json").status_code == 409


@pytest.mark.django_db
def test_negative_fields_permissions_and_constraints():
    owner, member = player(30), player(31)
    t = create_team(user=owner, name="Valid")
    TeamMembership.objects.create(team=t, user=member)
    assert authed(member).post(
        f"{TEAM}{t.pk}/invites/", {"playerId": str(owner.pk)}, format="json"
    ).status_code == 403
    assert authed(owner).post(TEAM, {"name": ""}, format="json").status_code == 400
    assert authed(owner).post(
        TEAM, {"name": "ok", "role": "captain"}, format="json"
    ).status_code == 400
    assert authed(owner).post(
        f"{TEAM}{t.pk}/invites/", {"playerId": "invalid"}, format="json"
    ).status_code == 400
    assert authed(owner).post(
        f"{TEAM}{t.pk}/invites/", {"playerId": str(member.pk)}, format="json"
    ).status_code == 409
    with pytest.raises(IntegrityError), transaction.atomic():
        TeamMembership.objects.create(team=t, user=member)
    with pytest.raises(IntegrityError), transaction.atomic():
        TeamMembership.objects.create(team=t, user=player(32), role="captain")


@pytest.mark.django_db
def test_tournament_hook_only_returns_captained_team_candidates():
    from types import SimpleNamespace

    owner, mate = player(33), player(34)
    team = create_team(user=owner, name="Eligible")
    TeamMembership.objects.create(team=team, user=mate)
    tournament = SimpleNamespace(mode="team")
    assert tournament_eligible_teams(owner, tournament) == [{
        "id": str(team.pk), "name": team.name, "memberCount": 2, "role": "captain"
    }]
    assert tournament_eligible_teams(mate, tournament) == []
    assert tournament_eligible_teams(owner, SimpleNamespace(mode="solo")) == []


@pytest.mark.django_db
def test_session_write_requires_csrf_cookie_and_token():
    from rest_framework.test import APIClient

    owner = player(35)
    c = APIClient(enforce_csrf_checks=True)
    c.force_login(owner)
    assert c.post(TEAM, {"name": "CSRF"}, format="json").status_code == 403
    token = c.get("/api/v1/auth/csrf/").data["csrf_token"]
    assert c.post(
        TEAM, {"name": "CSRF"}, format="json", HTTP_X_CSRFTOKEN=token
    ).status_code == 201


@pytest.mark.django_db(transaction=True)
def test_concurrent_invite_replay_is_single_row():
    owner, guest = player(36), player(37)
    team = create_team(user=owner, name="Concurrent")

    def run(_):
        connections.close_all()
        try:
            obj, created = invite(
                actor=owner, team_id=team.pk, recipient_id=guest.pk
            )
            return str(obj.pk), created
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        a, b = list(pool.map(run, range(2)))
    assert a[0] == b[0]
    assert {a[1], b[1]} == {True, False}
    assert TeamInvite.objects.filter(team=team, recipient=guest, state="pending").count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_accept_replay_and_one_captain():
    owner, guest = player(38), player(39)
    team = create_team(user=owner, name="Race")
    invited, _ = invite(actor=owner, team_id=team.pk, recipient_id=guest.pk)

    def run(_):
        connections.close_all()
        try:
            return respond(actor=guest, invite_id=invited.pk, accept=True).state
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(run, range(2))) == ["accepted", "accepted"]
    assert TeamMembership.objects.filter(team=team, user=guest).count() == 1
    assert TeamMembership.objects.filter(team=team, role="captain").count() == 1
