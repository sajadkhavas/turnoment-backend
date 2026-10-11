from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import PlayerProfile, User
from apps.disputes.models import Dispute, DisputeEvidence
from apps.disputes.services import resolve_dispute, start_review
from apps.matches.models import Match
from apps.matches.services import advance_match, create_match_for_source
from apps.results.models import FinalizedResultEvent, MatchResult
from apps.results.services import confirm_score, submit_score


@pytest.fixture
def players(db):
    a = User.objects.create_user(phone="09121234567", email="secret@example.test")
    b = User.objects.create_user(phone="09121234568")
    outsider = User.objects.create_user(phone="09121234569")
    PlayerProfile.objects.create(user=a, gamer_tag="Alpha")
    PlayerProfile.objects.create(user=b, gamer_tag="Bravo")
    return a, b, outsider


@pytest.fixture
def match(players):
    a, b, _ = players
    instance = create_match_for_source(
        source_kind="challenge",
        source_id="challenge-b08-1",
        participant_a=a,
        participant_b=b,
        game_id="fc",
        game_name="EA FC",
        competition_title="Free challenge",
        starts_at=timezone.now() - timedelta(hours=2),
        max_score=30,
        allow_draw=False,
    )
    advance_match(instance.pk, "ready")
    advance_match(instance.pk, "awaiting-result")
    instance.refresh_from_db()
    return instance


def result_url(match):
    return f"/api/v1/matches/{match.pk}/result/"


def dispute_url(match):
    return f"/api/v1/matches/{match.pk}/dispute/"


@pytest.mark.django_db
def test_match_source_seam_is_idempotent_and_cannot_change_participants(players):
    a, b, third = players
    kwargs = {
        "source_kind": "tournament",
        "source_id": "round-999",
        "participant_a": a,
        "participant_b": b,
        "game_id": "fc",
        "game_name": "FC",
        "competition_title": "Cup",
        "starts_at": timezone.now(),
        "tournament_slug": "cup",
        "round_label": "Round 1",
    }
    first = create_match_for_source(**kwargs)
    assert create_match_for_source(**kwargs).pk == first.pk
    assert Match.objects.count() == 1
    with pytest.raises(ValidationError):
        create_match_for_source(**{**kwargs, "participant_b": third})
    with pytest.raises(ValidationError):
        create_match_for_source(**{**kwargs, "participant_b": a})


@pytest.mark.django_db
def test_match_state_transition_rejects_skips_and_cancelled_revival(match):
    with pytest.raises(ValidationError):
        advance_match(match.pk, "live")
    assert advance_match(match.pk, "awaiting-result").revision == match.revision
    with pytest.raises(ValidationError):
        advance_match(match.pk, "cancelled")


@pytest.mark.django_db
def test_match_list_is_private_filtered_and_never_exposes_pii(match, players):
    a, b, third = players
    client = APIClient()
    assert client.get("/api/v1/me/matches/").status_code == 403
    client.force_authenticate(user=third)
    assert client.get("/api/v1/me/matches/").data["summary"]["total"] == 0
    client.force_authenticate(user=a)
    response = client.get("/api/v1/me/matches/?state=action-required&kind=challenge")
    assert response.status_code == 200
    assert response.data["pagination"]["totalItems"] == 1
    item = response.data["items"][0]
    assert item["attention"] == "submit-result"
    assert item["opponent"]["displayTag"] == "Bravo"
    assert "secret@example.test" not in str(response.data)
    assert "+989" not in str(response.data)
    assert client.get("/api/v1/me/matches/?page=0").status_code == 400
    assert client.get("/api/v1/me/matches/?state=invalid").status_code == 400


@pytest.mark.django_db
def test_result_authorization_csrf_validation_and_stale(match, players):
    a, b, outsider = players
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(a)
    url = result_url(match)
    assert client.get(url).data["submissionState"] == "reportable"
    command = {"revision": str(match.revision), "playerScore": 2, "opponentScore": 1}
    assert (
        client.post(url, command, format="json", HTTP_IDEMPOTENCY_KEY="submission-1").status_code
        == 403
    )
    csrf = client.get("/api/v1/auth/csrf/").data["csrf_token"]
    invalid = client.post(
        url,
        {**command, "opponentScore": 2},
        format="json",
        HTTP_X_CSRFTOKEN=csrf,
        HTTP_IDEMPOTENCY_KEY="submission-1",
    )
    assert invalid.data["outcome"] == "validation_error"
    stale = client.post(
        url,
        {**command, "revision": "old"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf,
        HTTP_IDEMPOTENCY_KEY="submission-2",
    )
    assert stale.data["outcome"] == "stale"
    client.force_authenticate(user=outsider)
    assert client.get(url).status_code == 404
    assert (
        client.post(url, command, format="json", HTTP_IDEMPOTENCY_KEY="submission-3").status_code
        == 404
    )


@pytest.mark.django_db
def test_result_submit_replay_reverse_projection_and_confirmation_once(match, players):
    a, b, _ = players
    first = submit_score(match.pk, a, str(match.revision), 3, 1, "idem-score-one")
    assert first["outcome"] == "accepted"
    assert first["status"] == "awaiting-confirmation"
    replay = submit_score(match.pk, a, str(match.revision), 3, 1, "idem-score-one")
    assert replay["outcome"] == "already_submitted"
    conflict = submit_score(match.pk, a, str(match.revision), 4, 1, "idem-score-one")
    assert conflict["outcome"] == "validation_error"
    assert MatchResult.objects.count() == 1
    match.refresh_from_db()
    assert confirm_score(match.pk, a, str(match.revision), 3, 1)["outcome"] == "unavailable"
    assert confirm_score(match.pk, b, str(match.revision), 3, 1)["outcome"] == "score_mismatch"
    confirmed = confirm_score(match.pk, b, str(match.revision), 1, 3)
    assert confirmed["outcome"] == "finalized"
    assert confirm_score(match.pk, b, str(match.revision), 1, 3)["eventId"] == confirmed["eventId"]
    assert FinalizedResultEvent.objects.count() == 1
    client = APIClient()
    client.force_authenticate(user=b)
    result = client.get(result_url(match)).data
    assert result["finalResult"]["outcome"] == "loss"
    assert result["finalResult"]["ratingDelta"] is None
    assert result["finalResult"]["playerScore"] == 1


@pytest.mark.django_db
def test_dispute_validation_idempotency_privacy_and_evidence_quarantine(match, players):
    a, b, outsider = players
    submit_score(match.pk, a, str(match.revision), 3, 1, "score-dispute-1")
    match.refresh_from_db()
    client = APIClient()
    client.force_authenticate(user=b)
    url = dispute_url(match)
    assert client.get(url).data["disputeState"] == "eligible"
    revision = str(match.revision)
    bad = client.post(
        url,
        {"revision": revision, "reason": "untrusted", "statement": "x"},
        format="json",
        HTTP_IDEMPOTENCY_KEY="dispute-12345",
    )
    assert bad.data["outcome"] == "validation_error"
    good = client.post(
        url,
        {
            "revision": revision,
            "reason": "incorrect-score",
            "statement": "Score was incorrectly reported at venue.",
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY="dispute-12345",
    )
    assert good.data["outcome"] == "accepted"
    dispute_id = good.data["dispute"]["disputeId"]
    assert (
        client.post(
            url,
            {
                "revision": revision,
                "reason": "incorrect-score",
                "statement": "Score was incorrectly reported at venue.",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="dispute-12345",
        ).data["outcome"]
        == "already_open"
    )
    assert Dispute.objects.count() == 1
    from django.core.files.uploadedfile import SimpleUploadedFile

    ev_url = f"/api/v1/matches/{match.pk}/dispute/{dispute_id}/evidence/"
    match.refresh_from_db()
    rev = str(match.revision)
    invalid = client.post(
        ev_url,
        {
            "revision": rev,
            "file": SimpleUploadedFile("fake.png", b"not-a-png", content_type="image/png"),
        },
        HTTP_IDEMPOTENCY_KEY="evidence-123",
    )
    assert invalid.data["outcome"] == "validation_error"
    valid = client.post(
        ev_url,
        {
            "revision": rev,
            "file": SimpleUploadedFile(
                "../photo.png", b"\x89PNG\r\n\x1a\n" + b"x" * 64, content_type="image/png"
            ),
        },
        HTTP_IDEMPOTENCY_KEY="evidence-123",
    )
    assert valid.data["outcome"] == "accepted"
    assert DisputeEvidence.objects.count() == 1
    assert "quarantined_bytes" not in str(client.get(url).data)
    evidence = DisputeEvidence.objects.get()
    assert evidence.quarantined_bytes.startswith(b"\x89PNG")
    client.force_authenticate(user=outsider)
    assert client.get(url).status_code == 404
    assert (
        client.post(ev_url, {"revision": rev}, HTTP_IDEMPOTENCY_KEY="evidence-456").status_code
        == 404
    )


@pytest.mark.django_db
def test_dispute_operator_boundary_and_finalization(match, players):
    a, b, outsider = players
    submit_score(match.pk, a, str(match.revision), 3, 1, "score-dispute-2")
    match.refresh_from_db()
    from apps.disputes.services import create_dispute

    created = create_dispute(
        match.pk,
        b,
        str(match.revision),
        "incorrect-score",
        "I challenge the reported score because it is incorrect.",
        "dispute-key-2",
    )
    dispute_id = created["dispute"]["disputeId"]
    with pytest.raises(PermissionDenied):
        start_review(dispute_id, outsider)
    outsider.is_staff = True
    outsider.save(update_fields=["is_staff"])
    with pytest.raises(PermissionDenied):
        resolve_dispute(dispute_id, outsider, decision="upheld", summary="Reviewed")
    outsider.is_superuser = True
    outsider.save(update_fields=["is_superuser"])
    start_review(dispute_id, outsider)
    resolution = resolve_dispute(dispute_id, outsider, decision="no-action", summary="Verified")
    assert resolution.status == "resolved"
    assert (
        resolve_dispute(dispute_id, outsider, decision="no-action", summary="Verified").pk
        == resolution.pk
    )
    assert FinalizedResultEvent.objects.count() == 1
    client = APIClient()
    client.force_authenticate(user=a)
    page = client.get(dispute_url(match)).data
    assert page["disputeState"] == "resolved"
    assert page["dispute"]["canAddEvidence"] is False
    assert page["result"]["state"] == "finalized"


@pytest.mark.django_db(transaction=True)
def test_parallel_confirmations_publish_exactly_one_finalized_event():
    a = User.objects.create_user(phone="09121234561")
    b = User.objects.create_user(phone="09121234562")
    instance = create_match_for_source(
        source_kind="challenge",
        source_id="parallel-b08",
        participant_a=a,
        participant_b=b,
        game_id="fc",
        game_name="FC",
        competition_title="Free",
        starts_at=timezone.now(),
    )
    advance_match(instance.pk, "ready")
    advance_match(instance.pk, "awaiting-result")
    instance.refresh_from_db()
    submit_score(instance.pk, a, str(instance.revision), 3, 1, "parallel-submission")
    instance.refresh_from_db()
    barrier = Barrier(2)

    def attempt():
        close_old_connections()
        barrier.wait(timeout=10)
        try:
            return confirm_score(instance.pk, b, str(instance.revision), 1, 3)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = [future.result() for future in [pool.submit(attempt), pool.submit(attempt)]]
    assert {x["outcome"] for x in outcomes} == {"finalized", "already_finalized"}
    assert FinalizedResultEvent.objects.count() == 1
    assert MatchResult.objects.get(match=instance).finalized_at is not None
