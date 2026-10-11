from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import PlayerProfile, User
from apps.brackets.models import BracketMatch
from apps.brackets.services import publish_round
from apps.checkins.models import CheckIn
from apps.registrations.models import Registration
from apps.registrations.services import register
from apps.tournaments.models import Tournament
from apps.tournaments.services import transition_tournament

BASE = "/api/v1/"


def make_tournament(**kwargs):
    now = timezone.now()
    values = {
        "slug": "karaj-free-cup",
        "title": "Karaj Free Cup",
        "description": "Public fair-play tournament",
        "game_key": "ea-fc-26",
        "game_slug": "ea-fc-26",
        "game_name": "EA FC 26",
        "center_key": "arena-1",
        "center_name": "Arena",
        "center_city": "Karaj",
        "center_district": "Mehrshahr",
        "center_meta": {"cityKey": "karaj"},
        "starts_at": now + timedelta(days=2),
        "registration_closes_at": now + timedelta(days=1),
        "check_in_opens_at": now + timedelta(days=1, hours=23),
        "display_date": "Tomorrow",
        "display_time": "20:00",
        "capacity": 2,
        "lifecycle": Tournament.Lifecycle.OPEN,
        "rules": [
            {
                "id": "fair-play", "title": "Fair play",
                "description": "No cheating", "mandatory": True
            }
        ],
    }
    values.update(kwargs)
    return Tournament.objects.create(**values)


def payload(**kwargs):
    value = {
        "detailVersion": "1", "rulesVersion": "1",
        "acceptedRules": True, "teamId": None
    }
    value.update(kwargs)
    return value


def player(index):
    return User.objects.create_user(phone=f"09121234{index:03d}")


def fake_team_hook(user, tournament):
    return [
        {"id": "team-1", "name": "Blue", "memberCount": 5, "role": "captain"}
    ]


@pytest.mark.django_db
def test_public_discovery_and_detail_shapes_without_private_identity():
    t = make_tournament()
    u = player(1)
    PlayerProfile.objects.create(user=u, gamer_tag="PublicAlias")
    register(identifier=str(t.pk), user=u, payload=payload())
    public = APIClient()
    listing = public.get(BASE + "tournaments/?game=ea-fc-26&city=karaj")
    assert listing.status_code == 200
    assert listing.data["schemaVersion"] == 1
    assert listing.data["pagination"]["totalItems"] == 1
    assert listing.data["items"][0]["capacity"] == {
        "limit": 2, "registered": 1, "remaining": 1
    }
    detail = public.get(BASE + f"tournaments/{t.slug}/")
    assert detail.status_code == 200
    assert detail.data["participants"]["preview"][0]["gamerTag"] == "PublicAlias"
    assert detail.data["registrationPolicy"]["state"] == "open"
    assert "+989" not in str(detail.data)
    assert "paymentUrl" not in str(detail.data)
    assert public.get(BASE + "tournaments/unknown/").status_code == 404


@pytest.mark.django_db
def test_auth_privacy_duplicate_capacity_and_validation():
    t = make_tournament(capacity=1)
    a, b = player(1), player(2)
    anonymous = APIClient()
    uri = BASE + f"tournaments/{t.slug}/"
    assert anonymous.get(uri + "registration/").status_code in (401, 403)
    assert anonymous.post(uri + "registrations/", payload(), format="json").status_code in (
        401, 403
    )
    a_client = APIClient()
    a_client.force_authenticate(a)
    invalid = a_client.post(uri + "registrations/", payload(acceptedRules=False), format="json")
    assert invalid.status_code == 400
    assert invalid.data["outcome"] == "validation_error"
    stale = a_client.post(uri + "registrations/", payload(rulesVersion="outdated"), format="json")
    assert stale.data["outcome"] == "stale"
    confirmed = a_client.post(uri + "registrations/", payload(), format="json")
    assert confirmed.data["outcome"] == "confirmed"
    repeat = a_client.post(uri + "registrations/", payload(), format="json")
    assert repeat.data["outcome"] == "already_registered"
    b_client = APIClient()
    b_client.force_authenticate(b)
    assert b_client.post(uri + "registrations/", payload(), format="json").data == {
        "outcome": "unavailable", "reason": "full"
    }
    t.refresh_from_db()
    assert t.registered_count == 1
    assert Registration.objects.count() == 1
    assert b_client.get(BASE + "me/tournaments/").data["summary"]["total"] == 0
    mine = a_client.get(BASE + "me/tournaments/")
    assert mine.data["summary"]["total"] == 1
    assert mine.data["items"][0]["registrationState"] == "confirmed"


@pytest.mark.django_db
def test_finance_pending_even_when_capacity_available():
    t = make_tournament(entry_fee=10000, fixed_prize=20000)
    u = player(1)
    client = APIClient()
    client.force_authenticate(u)
    uri = BASE + f"tournaments/{t.slug}/"
    d = client.get(uri).data
    assert d["entryFee"] == {"amount": 10000, "currency": "IRR"}
    assert d["fixedPrize"] == {"amount": 20000, "currency": "IRR"}
    assert d["registrationPolicy"]["state"] == "closed"
    assert client.get(uri + "registration/").data["availability"] == "ineligible"
    response = client.post(uri + "registrations/", payload(), format="json")
    assert response.data["backendState"] == "BACKEND_PENDING_FINANCE"
    assert response.data["outcome"] == "unavailable"
    assert Registration.objects.count() == 0
    assert not any("paymentUrl" in str(obj) for obj in (response.data, d))


@pytest.mark.django_db
def test_checkin_idempotency_and_scoped_access():
    now = timezone.now()
    t = make_tournament(
        lifecycle=Tournament.Lifecycle.CHECK_IN,
        starts_at=now + timedelta(hours=2),
        check_in_opens_at=now - timedelta(minutes=5)
    )
    u, other = player(1), player(2)
    reg = Registration.objects.create(tournament=t, user=u)
    t.registered_count = 1
    t.save(update_fields=["registered_count"])
    uri = BASE + f"tournaments/{t.slug}/check-in/"
    foreign = APIClient()
    foreign.force_authenticate(other)
    assert foreign.post(uri).data["reason"] == "not_registered"
    assert foreign.get(uri).data["reason"] == "not_registered"
    client = APIClient()
    client.force_authenticate(u)
    first = client.post(uri)
    repeat = client.post(uri)
    assert first.data["outcome"] == "completed"
    assert repeat.data["checkedAt"] == first.data["checkedAt"]
    assert CheckIn.objects.filter(registration=reg).count() == 1
    assert client.get(BASE + "me/tournaments/").data["items"][0]["checkInState"] == "completed"


@pytest.mark.django_db
@override_settings(
    TOURNAMENT_TEAM_ELIGIBILITY_HOOK="apps.tournaments.tests.test_b05.fake_team_hook"
)
def test_team_hook_captain_only_and_tournament_scoped():
    t = make_tournament(mode=Tournament.Mode.TEAM)
    u = player(1)
    c = APIClient()
    c.force_authenticate(u)
    uri = BASE + f"tournaments/{t.slug}/"
    assert c.get(uri + "registration/").data["eligibleTeams"][0]["id"] == "team-1"
    assert c.post(uri + "registrations/", payload(), format="json").data[
        "outcome"
    ] == "validation_error"
    assert c.post(
        uri + "registrations/", payload(teamId="foreign-team"), format="json"
    ).data["reason"] == "ineligible"
    assert c.post(
        uri + "registrations/", payload(teamId="team-1"), format="json"
    ).data["outcome"] == "confirmed"
    assert c.get(BASE + "me/tournaments/").data["items"][0]["participation"] == {
        "kind": "team", "teamId": "team-1", "teamName": "Blue", "role": "captain"
    }


@pytest.mark.django_db
def test_unconfigured_team_adapter_fails_closed():
    t = make_tournament(mode=Tournament.Mode.TEAM)
    u = player(1)
    c = APIClient()
    c.force_authenticate(u)
    assert c.post(
        BASE + f"tournaments/{t.slug}/registrations/",
        payload(teamId="team-1"), format="json"
    ).data["reason"] == "ineligible"


@pytest.mark.django_db
def test_bracket_creation_rejects_cross_tournament_and_duplicate_round():
    t = make_tournament(lifecycle=Tournament.Lifecycle.CLOSED)
    other = make_tournament(slug="other-free-cup")
    a, b = player(1), player(2)
    first = Registration.objects.create(tournament=t, user=a)
    outsider = Registration.objects.create(tournament=other, user=b)
    with pytest.raises(ValueError, match="Cross-tournament"):
        publish_round(
            tournament=t, number=1, title="First",
            pairings=[(first.pk, outsider.pk)]
        )
    assert BracketMatch.objects.count() == 0
    with pytest.raises(ValueError, match="Same player"):
        publish_round(
            tournament=t, number=1, title="First",
            pairings=[(first.pk, first.pk)]
        )
    round_obj = publish_round(
        tournament=t, number=1, title="First",
        pairings=[(first.pk, None)]
    )
    assert round_obj.matches.count() == 1
    with pytest.raises(IntegrityError):
        publish_round(
            tournament=t, number=1, title="Duplicate",
            pairings=[(first.pk, None)]
        )
    assert APIClient().get(
        BASE + f"tournaments/{t.slug}/"
    ).data["bracketPreview"]["state"] == "seeded"


@pytest.mark.django_db
def test_lifecycle_transition_rejects_skips_and_is_replay_safe():
    t = make_tournament()
    with pytest.raises(ValueError, match="Invalid"):
        transition_tournament(t.id, Tournament.Lifecycle.LIVE)
    changed = transition_tournament(t.id, Tournament.Lifecycle.CLOSED)
    assert changed.lifecycle == Tournament.Lifecycle.CLOSED
    assert transition_tournament(t.id, Tournament.Lifecycle.CLOSED).pk == t.pk


@pytest.mark.django_db
def test_session_auth_csrf_is_enforced_for_registration():
    t = make_tournament()
    u = player(1)
    c = APIClient(enforce_csrf_checks=True)
    c.force_login(u)
    uri = BASE + f"tournaments/{t.slug}/registrations/"
    assert c.post(uri, payload(), format="json").status_code == 403
    token = c.get(BASE + "auth/csrf/").data["csrf_token"]
    accepted = c.post(
        uri, payload(), format="json", HTTP_X_CSRFTOKEN=token
    )
    assert accepted.status_code == 200
    assert accepted.data["outcome"] == "confirmed"


@pytest.mark.django_db
def test_capacity_database_constraint():
    t = make_tournament(capacity=1)
    t.registered_count = 2
    with pytest.raises(IntegrityError):
        t.save(update_fields=["registered_count"])
