from concurrent.futures import ThreadPoolExecutor

import pytest
from django.contrib import admin
from django.db import close_old_connections
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.moderation.models import ModerationCase, ModerationDecision
from apps.moderation.services import record_moderation_case, review_case


def make_user(phone, **extra):
    return User.objects.create_user(phone=phone, **extra)


@pytest.mark.django_db
def test_platform_access_and_center_staff_admin_denial():
    player = make_user("+989127111111")
    center_staff = make_user("+989127222222", is_staff=True)
    operator = make_user("+989127333333", is_staff=True, is_superuser=True)
    record_moderation_case(
        source_type="dispute", source_id="dispute-1", title="Disputed result", center_id="center-a"
    )
    url = "/api/v1/operator/moderation/"
    client = APIClient()
    assert client.get(url).status_code == 403
    for blocked in (player, center_staff):
        client.force_authenticate(user=blocked)
        assert client.get(url).status_code == 403
        assert client.post(
            url + "00000000-0000-0000-0000-000000000000/review/",
            {"status": "in_review", "note": "Reviewed this case"}, format="json",
        ).status_code == 403
    client.force_authenticate(user=operator)
    assert client.get(url).status_code == 200
    assert client.get(url).data["pagination"]["totalItems"] == 1
    assert admin.site.has_permission(type("Request", (), {"user": center_staff})()) is False
    assert admin.site.has_permission(type("Request", (), {"user": operator})()) is True


@pytest.mark.django_db
def test_scopes_idempotence_transitions_and_audit():
    operator = make_user("+989128111111", is_staff=True, is_superuser=True)
    cases = [
        record_moderation_case(
            source_type="host_application", source_id="h1", title="Host review"
        )[0],
        record_moderation_case(
            source_type="dispute", source_id="d1", title="Dispute review", center_id="center1"
        )[0],
        record_moderation_case(
            source_type="managed_content", source_id="c1",
            title="Content review", center_id="center2"
        )[0],
    ]
    same, created = record_moderation_case(
        source_type="host_application", source_id="h1", title="Host review"
    )
    assert not created and same.pk == cases[0].pk
    with pytest.raises(ValueError):
        record_moderation_case(
            source_type="host_application", source_id="h1", title="Different title"
        )
    client = APIClient()
    client.force_authenticate(user=operator)
    listing = client.get("/api/v1/operator/moderation/?source_type=dispute&center_id=center1")
    assert listing.status_code == 200
    assert listing.data["pagination"]["totalItems"] == 1
    assert listing.data["items"][0]["sourceType"] == "dispute"
    assert client.get("/api/v1/operator/moderation/?source_type=unknown").status_code == 400
    case_url = f"/api/v1/operator/moderation/{cases[1].pk}/"
    assert client.get(case_url).data["status"] == "open"
    review_url = case_url + "review/"
    assert client.post(
        review_url, {"status": "closed", "note": "Cannot skip review"},
        format="json",
    ).status_code == 409
    first = client.post(
        review_url, {"status": "in_review", "note": "Reviewed the match history"},
        format="json",
    )
    assert first.status_code == 200 and first.data["changed"]
    replay = client.post(
        review_url, {"status": "in_review", "note": "Reviewed the match history"},
        format="json",
    )
    assert replay.status_code == 200 and not replay.data["changed"]
    assert ModerationDecision.objects.filter(case=cases[1]).count() == 1
    assert client.post(
        review_url, {"status": "closed", "note": "Evidence examined and logged"},
        format="json",
    ).status_code == 200
    assert ModerationDecision.objects.filter(case=cases[1]).count() == 2
    assert client.get(case_url).data["decisions"][1]["toStatus"] == "closed"
    assert client.post(
        review_url, {"status": "in_review", "note": "Cannot reopen resolved case"},
        format="json",
    ).status_code == 409
    assert client.post(
        review_url, {"status": "closed", "note": "short"},
        format="json",
    ).status_code == 400


@pytest.mark.django_db
def test_operator_cannot_modify_source_domain_state():
    operator = make_user("+989129111111", is_staff=True, is_superuser=True)
    case, _ = record_moderation_case(
        source_type="dispute", source_id="owned-by-B08", title="Dispute"
    )
    client = APIClient()
    client.force_authenticate(user=operator)
    resp = client.post(
        f"/api/v1/operator/moderation/{case.pk}/review/",
        {"status": "in_review", "note": "Checking external evidence"},
        format="json",
    )
    assert resp.status_code == 200
    assert ModerationCase.objects.get(pk=case.pk).source_id == "owned-by-B08"


@pytest.mark.django_db(transaction=True)
def test_concurrent_case_ingestion_idempotent():
    def ingest(_):
        close_old_connections()
        try:
            return record_moderation_case(
                source_type="managed_content", source_id="stable-content-id", title="Content review"
            )[0].pk
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=3) as pool:
        ids = list(pool.map(ingest, range(3)))
    assert len(set(ids)) == 1
    assert ModerationCase.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_moderation_review_has_one_decision():
    actor = make_user("+989129999999", is_staff=True, is_superuser=True)
    case, _ = record_moderation_case(
        source_type="host_application", source_id="host1", title="Host"
    )

    def review(_):
        close_old_connections()
        try:
            return review_case(
                case_id=case.pk, actor=actor, to_status="in_review",
                note="This application was inspected",
            )[1]
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        changed = list(pool.map(review, range(2)))
    assert sorted(changed) == [False, True]
    assert ModerationDecision.objects.filter(case=case).count() == 1
