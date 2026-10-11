import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User

URL = "/api/v1/me/settings/notification-preferences/"


@pytest.mark.django_db
def test_owner_read_update_replay_stale_and_privacy():
    one = User.objects.create_user(phone="09121234567")
    two = User.objects.create_user(phone="09121234568")
    a = APIClient()
    b = APIClient()
    assert a.get(URL).status_code == 403
    a.force_authenticate(one)
    b.force_authenticate(two)
    initial = a.get(URL)
    assert initial.status_code == 200
    assert initial.data["required"] == {"account": True, "system": True}
    payload = {"revision": initial.data["revision"], "optional": {
        "tournament": False, "match": True, "challenge": True,
    }}
    saved = a.patch(URL, payload, format="json")
    assert saved.status_code == 200
    assert saved.data["settings"]["revision"] == "2"
    assert a.patch(URL, payload, format="json").status_code == 409
    unrelated = b.get(URL)
    assert unrelated.data["optional"]["tournament"] is True
    assert unrelated.data["revision"] == "1"
    assert "phone" not in str(saved.data)
    assert "email" not in str(saved.data)


@pytest.mark.django_db
def test_invalid_mutation_rejected_and_no_revision_change():
    user = User.objects.create_user(phone="09121234569")
    client = APIClient()
    client.force_authenticate(user)
    revision = client.get(URL).data["revision"]
    for optional in ({"account": False}, {"tournament": 1, "match": True, "challenge": True}):
        response = client.patch(URL, {"revision": revision, "optional": optional}, format="json")
        assert response.status_code == 400
    assert client.get(URL).data["revision"] == revision

@pytest.mark.django_db
def test_session_csrf_is_required_for_settings_patch():
    from rest_framework.test import APIClient

    user = User.objects.create_user(phone="09121234999")
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(user)

    initial = client.get(URL)
    assert initial.status_code == 200
    command = {
        "revision": initial.data["revision"],
        "optional": {"tournament": False, "match": True, "challenge": True},
    }

    no_csrf = client.patch(URL, command, format="json")
    assert no_csrf.status_code == 403
    assert client.get(URL).data["revision"] == initial.data["revision"]

    csrf_response = client.get("/api/v1/auth/csrf/")
    assert csrf_response.status_code == 200
    csrf_token = csrf_response.data["csrf_token"]
    accepted = client.patch(URL, command, format="json", HTTP_X_CSRFTOKEN=csrf_token)
    assert accepted.status_code == 200
    assert accepted.data["outcome"] == "saved"


@pytest.mark.django_db(transaction=True)
def test_concurrent_revision_updates_only_one_wins():
    from concurrent.futures import ThreadPoolExecutor

    from django.db import connections

    user = User.objects.create_user(phone="09121234888")
    client = APIClient()
    client.force_authenticate(user)
    original = client.get(URL)
    assert original.status_code == 200
    revision = original.data["revision"]

    def worker(disable_tournament):
        connections.close_all()
        try:
            requester = APIClient()
            requester.force_authenticate(user)
            data = {
                "revision": revision,
                "optional": {
                    "tournament": disable_tournament, "match": True, "challenge": True
                },
            }
            return requester.patch(URL, data, format="json").status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(worker, (False, True)))

    assert sorted(statuses) == [200, 409]
