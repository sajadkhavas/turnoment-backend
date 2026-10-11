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
        assert client.patch(URL, {"revision": revision, "optional": optional}, format="json").status_code == 400
    assert client.get(URL).data["revision"] == revision
