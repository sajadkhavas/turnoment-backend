from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.challenges.models import Challenge
from apps.matches.services import advance_match, create_match_for_source


@pytest.fixture
def lifecycle_match(db):
    a = User.objects.create_user(phone="09121234001")
    b = User.objects.create_user(phone="09121234002")
    outsider = User.objects.create_user(phone="09121234003")
    pair = sorted((str(a.pk), str(b.pk)))
    challenge = Challenge.objects.create(
        challenger=a, opponent=b, pair_low=pair[0], pair_high=pair[1],
        game_id="fc", game_name="FC", format_id="solo", format_label="Solo",
        expires_at=timezone.now() + timedelta(hours=24),
    )
    match = create_match_for_source(
        source_kind="challenge", source_id=str(challenge.pk),
        participant_a=a, participant_b=b, game_id="fc", game_name="FC",
        competition_title="Challenge", starts_at=timezone.now(),
    )
    challenge.state = "accepted"
    challenge.match_id = str(match.pk)
    challenge.save()
    match = advance_match(match.pk, "ready")
    return match, a, b, outsider


def endpoint(match):
    return f"/api/v1/matches/{match.pk}/lifecycle/"


@pytest.mark.django_db
def test_start_finish_and_duplicate_do_not_skip_or_repeat(lifecycle_match):
    match, a, b, _ = lifecycle_match
    client = APIClient()
    client.force_authenticate(user=a)
    initial = str(match.revision)
    assert client.post(endpoint(match), {
        "command": "finish", "revision": initial,
    }, format="json").data["outcome"] == "unavailable"
    started = client.post(endpoint(match), {
        "command": "start", "revision": initial,
    }, format="json")
    assert started.status_code == 200
    assert started.data["state"] == "live"
    assert client.post(endpoint(match), {
        "command": "start", "revision": initial,
    }, format="json").data["outcome"] == "stale"
    match.refresh_from_db()
    assert match.revision == int(initial) + 1
    client.force_authenticate(user=b)
    finished = client.post(endpoint(match), {
        "command": "finish", "revision": str(match.revision),
    }, format="json")
    assert finished.data["state"] == "awaiting-result"
    match.refresh_from_db()
    assert client.post(endpoint(match), {
        "command": "start", "revision": str(match.revision),
    }, format="json").data["outcome"] == "unavailable"


@pytest.mark.django_db
def test_private_invalid_and_tournament_commands(lifecycle_match):
    match, a, _, outsider = lifecycle_match
    client = APIClient()
    body = {"command": "start", "revision": str(match.revision)}
    assert client.post(endpoint(match), body, format="json").status_code == 403
    client.force_authenticate(user=outsider)
    assert client.post(endpoint(match), body, format="json").status_code == 404
    client.force_authenticate(user=a)
    for invalid in (
        {"command": "cancel", "revision": "2"},
        {"command": "start", "revision": 2},
        {"command": "start", "revision": ""},
    ):
        assert client.post(endpoint(match), invalid, format="json").status_code == 400
    match.source_kind = "tournament"
    match.save(update_fields=["source_kind"])
    assert client.post(endpoint(match), body, format="json").data["outcome"] == "unavailable"
    match.refresh_from_db()
    assert match.state == "ready"


@pytest.mark.django_db
def test_session_requires_csrf(lifecycle_match):
    match, a, _, _ = lifecycle_match
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(a)
    body = {"command": "start", "revision": str(match.revision)}
    assert client.post(endpoint(match), body, format="json").status_code == 403
    csrf = client.get("/api/v1/auth/csrf/").data["csrf_token"]
    response = client.post(
        endpoint(match), body, format="json", HTTP_X_CSRFTOKEN=csrf,
    )
    assert response.data["outcome"] == "accepted"


@pytest.mark.django_db
def test_unbound_challenge_match_cannot_start(lifecycle_match):
    match, a, _, _ = lifecycle_match
    challenge = Challenge.objects.get(match_id=str(match.pk))
    challenge.state = "pending"
    challenge.match_id = None
    challenge.save()
    client = APIClient()
    client.force_authenticate(user=a)
    response = client.post(endpoint(match), {
        "command": "start", "revision": str(match.revision),
    }, format="json")
    assert response.data["outcome"] == "unavailable"
    match.refresh_from_db()
    assert match.state == "ready"
