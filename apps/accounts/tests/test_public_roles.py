import pytest
from rest_framework.test import APIClient

from apps.accounts.models import PlayerProfile, User
from apps.accounts.roles import has_center_role, is_platform_operator


@pytest.mark.django_db
def test_public_projection_is_anonymous_and_pii_safe():
    user = User.objects.create_user(phone="09121234567", email="private@example.com")
    PlayerProfile.objects.create(user=user, gamer_tag="player_1", bio="Hello", city="Karaj")
    client = APIClient()
    response = client.get("/api/v1/players/player_1/public-profile/")
    assert response.status_code == 200
    assert response.data["schemaVersion"] == 1
    assert response.data["username"] == "player_1"
    assert response.data["competitiveSnapshots"] == []
    assert response.data["city"] is None
    assert "private@example.com" not in str(response.data)
    assert "+989121234567" not in str(response.data)
    assert client.get("/api/v1/players/not.found/public-profile/").status_code == 404
    user.is_active = False
    user.save(update_fields=["is_active"])
    assert client.get("/api/v1/players/player_1/public-profile/").status_code == 404


@pytest.mark.django_db
def test_center_role_requires_scoped_active_membership():
    class Membership:
        user_id = None
        center_id = "center-a"
        is_active = True
        role = "center_staff"
    user = User.objects.create_user(phone="09121234567")
    member = Membership()
    member.user_id = user.pk
    assert has_center_role(user, membership=member, center_id="center-a")
    assert not has_center_role(user, membership=member, center_id="center-b")
    assert not has_center_role(user, membership=member, center_id="center-a", manager_only=True)
    assert not is_platform_operator(user)
    member.role = "center_manager"
    assert has_center_role(user, membership=member, center_id="center-a", manager_only=True)
    member.is_active = False
    assert not has_center_role(user, membership=member, center_id="center-a")
