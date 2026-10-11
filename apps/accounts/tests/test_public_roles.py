import pytest
from rest_framework.test import APIClient

from apps.accounts.models import PlayerProfile, User
from apps.accounts.roles import has_center_role, is_platform_operator
from apps.gaming_centers.models import CenterMembership, City, GamingCenter


@pytest.mark.django_db
def test_unpublished_gamer_tag_is_not_public_profile_username():
    user = User.objects.create_user(phone="09121234567", email="private@example.test")
    PlayerProfile.objects.create(user=user, gamer_tag="player_1", bio="Private bio", city="Karaj")
    response = APIClient().get("/api/v1/players/player_1/public-profile/")
    assert response.status_code == 404
    assert "Private bio" not in str(response.data)
    assert "private@example.test" not in str(response.data)


@pytest.mark.django_db
def test_b04_real_scoped_owner_manager_staff_and_platform_guard():
    user = User.objects.create_user(phone="09121234567")
    city = City.objects.create(name="Karaj", slug="karaj-b02")
    center = GamingCenter.objects.create(
        public_id="test-center-b02", name="Test Venue", city=city,
        district="Karaj", summary="Private scoped membership test center.",
        description="A center created only to test role authorization and boundaries.",
    )
    membership = CenterMembership.objects.create(center=center, user=user, role="staff")
    assert has_center_role(user, membership=membership, center_id=center.id)
    assert not has_center_role(user, membership=membership, center_id=center.id, manager_only=True)
    assert not has_center_role(user, membership=membership, center_id="not-this-center")
    membership.role = "manager"
    assert has_center_role(user, membership=membership, center_id=center.id, manager_only=True)
    membership.role = "owner"
    assert has_center_role(user, membership=membership, center_id=center.id, manager_only=True)
    membership.is_active = False
    assert not has_center_role(user, membership=membership, center_id=center.id)
    user.is_staff = True
    user.save(update_fields=["is_staff"])
    assert not is_platform_operator(user)
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])
    assert is_platform_operator(user)
