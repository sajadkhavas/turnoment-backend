from concurrent.futures import ThreadPoolExecutor
from datetime import time

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from rest_framework.test import APIClient

from apps.gaming_centers.models import (
    CenterMembership, City, GamingCenter, HostApplication, HostRateBucket,
)
from apps.gaming_centers.services import receive_host_application
from apps.gaming_resources.models import Equipment, GalleryImage, OpeningHour, Station


@pytest.fixture
def center_data(db):
    city = City.objects.create(name="Karaj", slug="karaj")
    center = GamingCenter.objects.create(
        public_id="karaj-arena", city=city, name="Karaj Arena",
        district="Azimieh", summary="A verified venue for all competitive players.",
        description="A modern gaming venue with plenty of stations and fair tournament rules.",
        publication_state=GamingCenter.Publication.PUBLISHED, verified=True,
        business_phone="+989121112233", street_address="Main Road Number 12",
        address_locality="Karaj", display_address="Main Road 12, Karaj",
        map_url="https://maps.example.test/karaj",
    )
    Equipment.objects.create(center=center, label="PlayStation 5", is_public=True)
    Equipment.objects.create(center=center, label="Secret rig", is_public=False)
    GalleryImage.objects.create(
        center=center, position=0, image_url="https://images.example.test/public.jpg"
    )
    OpeningHour.objects.create(
        center=center, weekday=0, opens=time(10, 0), closes=time(22, 0)
    )
    return center


def account(n):
    return get_user_model().objects.create_user(phone=f"+98912123{n:04d}")


def member(center, n, role, active=True):
    user = account(n)
    CenterMembership.objects.create(center=center, user=user, role=role, is_active=active)
    return user


@pytest.mark.django_db
def test_public_directory_and_detail_match_strict_frozen_contract_and_privacy(center_data):
    center = center_data
    response = APIClient().get("/api/v1/centers/?city=karaj")
    assert response.status_code == 200
    assert response.data["schemaVersion"] == 1
    assert response.data["pagination"] == {
        "currentPage": 1, "totalPages": 1, "totalItems": 1, "pageSize": 20
    }
    assert response.data["filters"]["cities"][0]["count"] == 1
    item = response.data["items"][0]
    assert item["publicId"] == center.public_id
    assert item["equipmentLabels"] == ["PlayStation 5"]
    assert item["upcomingTournamentCount"] is None
    assert set(item) == {
        "centerId", "publicId", "publicationState", "name", "verified", "city",
        "district", "summary", "equipmentLabels", "coverImage", "upcomingTournamentCount"
    }
    detail = APIClient().get(f"/api/v1/centers/{center.public_id}/")
    assert detail.status_code == 200
    assert detail.data["openingHours"] == [
        {"dayOfWeek": ["Monday"], "opens": "10:00", "closes": "22:00"}
    ]
    assert detail.data["galleryImages"] == ["https://images.example.test/public.jpg"]
    assert detail.data["publicAddress"] is None
    assert detail.data["publicPhone"] is None
    assert detail.data["mapUrl"] is None
    assert detail.data["tournaments"] == []
    assert not ({"phone", "email", "memberships", "managerName", "staff"} & set(detail.data))
    center.show_phone = center.show_address = center.show_map = True
    center.save()
    disclosed = APIClient().get(f"/api/v1/centers/{center.public_id}/").data
    assert disclosed["publicPhone"] == "+989121112233"
    assert disclosed["publicAddress"]["addressCountry"] == "IR"
    assert disclosed["mapUrl"] == "https://maps.example.test/karaj"


@pytest.mark.django_db
def test_private_center_hidden_from_public_and_invalid_queries_fail_closed(center_data):
    center_data.publication_state = GamingCenter.Publication.DRAFT
    center_data.save()
    assert APIClient().get("/api/v1/centers/").data["items"] == []
    assert APIClient().get("/api/v1/centers/karaj-arena/").status_code == 404
    for suffix in ["?page=0", "?page=abc", "?city=../oops", "?page=9999999999"]:
        assert APIClient().get("/api/v1/centers/" + suffix).status_code == 400
    assert APIClient().get("/api/v1/centers/?page=2").status_code == 404


@pytest.mark.django_db
def test_center_scope_staff_permissions_no_escalation(center_data):
    owner = member(center_data, 1, CenterMembership.Role.OWNER)
    manager = member(center_data, 2, CenterMembership.Role.MANAGER)
    staff = member(center_data, 3, CenterMembership.Role.STAFF)
    stranger = account(4)
    second = GamingCenter.objects.create(
        public_id="second-center", city=center_data.city, name="Second Center",
        district="Karaj", summary="Second center minimum length summary.",
        description="Second center description that passes basic bounds rules.",
    )
    for actor in [stranger, staff]:
        c = APIClient()
        c.force_authenticate(actor)
        assert c.patch(
            f"/api/v1/center-admin/centers/{center_data.id}/",
            {"name": "Poison"}, format="json"
        ).status_code == 403
    manager_client = APIClient()
    manager_client.force_authenticate(manager)
    assert manager_client.patch(
        f"/api/v1/center-admin/centers/{second.id}/",
        {"name": "Poison"}, format="json"
    ).status_code == 403
    assert manager_client.patch(
        f"/api/v1/center-admin/centers/{center_data.id}/",
        {"name": "Renamed"}, format="json"
    ).status_code == 200
    assert manager_client.post(
        f"/api/v1/center-admin/centers/{center_data.id}/staff/",
        {"userId": str(stranger.id), "role": "owner"}, format="json"
    ).status_code == 403
    owner_client = APIClient()
    owner_client.force_authenticate(owner)
    new_staff = owner_client.post(
        f"/api/v1/center-admin/centers/{center_data.id}/staff/",
        {"userId": str(stranger.id), "role": "staff"}, format="json"
    )
    assert new_staff.status_code == 201
    assert owner_client.post(
        f"/api/v1/center-admin/centers/{center_data.id}/staff/",
        {"userId": str(stranger.id), "role": "staff"}, format="json"
    ).status_code == 409
    assert owner_client.post(
        f"/api/v1/center-admin/centers/{center_data.id}/staff/",
        {"userId": str(account(5).id), "role": "owner"}, format="json"
    ).status_code == 400
    assert owner_client.patch(
        f"/api/v1/center-admin/centers/{center_data.id}/staff/"
        f"{center_data.memberships.get(user=owner).id}/",
        {"role": "staff", "active": False}, format="json"
    ).status_code == 403
    for user in [owner, manager, staff, stranger]:
        user.refresh_from_db()
        assert not user.is_staff and not user.is_superuser
    c = APIClient()
    c.force_login(staff)
    assert c.get("/admin/").status_code in [302, 403]


@pytest.mark.django_db
def test_resources_hours_are_center_scoped_and_atomic(center_data):
    manager = member(center_data, 22, CenterMembership.Role.MANAGER)
    second = GamingCenter.objects.create(
        public_id="other-center", city=center_data.city, name="Other",
        district="Karaj", summary="Summary at least twenty characters.",
        description="Description has plenty of characters to pass input.",
    )
    foreign_equipment = Equipment.objects.create(center=second, label="Foreign")
    c = APIClient()
    c.force_authenticate(manager)
    base = f"/api/v1/center-admin/centers/{center_data.id}"
    assert c.post(
        base + "/stations/", {"code": "PS5-2", "equipmentId": str(foreign_equipment.id)},
        format="json"
    ).status_code == 404
    valid_equipment = center_data.equipment.get(label="PlayStation 5")
    created = c.post(
        base + "/stations/", {"code": "PS5-2", "equipmentId": str(valid_equipment.id)},
        format="json"
    )
    assert created.status_code == 201
    assert c.post(
        base + "/stations/", {"code": "PS5-2", "equipmentId": str(valid_equipment.id)},
        format="json"
    ).status_code == 409
    assert Station.objects.filter(center=center_data).count() == 1
    invalid_hours = [
        {"weekday": 0, "opens": "10:00", "closes": "20:00", "isPublic": True},
        {"weekday": 0, "opens": "12:00", "closes": "21:00", "isPublic": True},
    ]
    assert c.put(base + "/hours/", invalid_hours, format="json").status_code == 400
    assert center_data.hours.count() == 1
    hours = [{"weekday": 2, "opens": "09:00", "closes": "19:00", "isPublic": True}]
    assert c.put(base + "/hours/", hours, format="json").status_code == 200
    assert list(center_data.hours.values_list("weekday", flat=True)) == [2]


@pytest.mark.django_db
def test_database_constraints_block_cross_scope_duplicates_and_bad_hours(center_data):
    equipment = center_data.equipment.get(label="PlayStation 5")
    with pytest.raises(IntegrityError), transaction.atomic():
        Equipment.objects.create(center=center_data, label="playstation 5")
    with pytest.raises(IntegrityError), transaction.atomic():
        OpeningHour.objects.create(
            center=center_data, weekday=4, opens=time(22), closes=time(10)
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        Station.objects.create(
            center=center_data, equipment=equipment, code="dup"
        )
        Station.objects.create(center=center_data, equipment=equipment, code="dup")


@pytest.mark.django_db
def test_session_auth_center_mutations_enforce_csrf(center_data):
    user = member(center_data, 88, CenterMembership.Role.OWNER)
    c = APIClient(enforce_csrf_checks=True)
    c.force_login(user)
    url = f"/api/v1/center-admin/centers/{center_data.id}/"
    assert c.patch(url, {"name": "Should Fail"}, format="json").status_code == 403
    token = c.get("/api/v1/auth/csrf/").data["csrf_token"]
    assert c.patch(url, {"name": "Allowed"}, format="json",
                   HTTP_X_CSRFTOKEN=token).status_code == 200


HOST_PAYLOAD = {
    "venueName": "Arena Karaj", "managerName": "Test Manager",
    "phone": "۰۹۱۲۱۲۳۴۵۶۷", "city": "Karaj", "area": "Azimieh",
    "stationCount": 8, "games": "FC26 and Tekken", "description": None,
}


@pytest.mark.django_db
def test_host_public_session_independent_idempotency_and_private_receipt():
    url = "/api/v1/host-applications/"
    c = APIClient(enforce_csrf_checks=True)
    first = c.post(url, HOST_PAYLOAD, format="json")
    assert first.status_code == 201
    assert set(first.data) == {"schemaVersion", "applicationId", "state", "submittedAt"}
    assert first.data["state"] == "received"
    assert first.data["submittedAt"].endswith("+00:00")
    assert HostApplication.objects.get().phone == "+989121234567"
    again = c.post(url, HOST_PAYLOAD, format="json")
    assert again.status_code == 201
    assert first.data == again.data
    assert HostApplication.objects.count() == 1
    logged = account(99)
    c.force_login(logged)
    assert c.post(url, HOST_PAYLOAD, format="json").status_code == 201
    assert HostApplication.objects.count() == 1
    assert c.get(url).status_code == 405
    assert c.get(url + first.data["applicationId"] + "/").status_code == 404


@pytest.mark.django_db
def test_host_validation_abuse_limit_and_unknown_field_rejection():
    url = "/api/v1/host-applications/"
    c = APIClient()
    assert c.post(url, {**HOST_PAYLOAD, "arbitrary": "x"}, format="json").status_code == 400
    assert c.post(url, {**HOST_PAYLOAD, "stationCount": True}, format="json").status_code == 400
    assert c.post(url, {**HOST_PAYLOAD, "phone": "abc"}, format="json").status_code == 400
    assert c.post(url, {**HOST_PAYLOAD, "description": ""}, format="json").status_code == 400
    for i in range(5):
        p = {**HOST_PAYLOAD, "venueName": f"New Arena {i}"}
        assert c.post(url, p, format="json").status_code == 201
    rejected = c.post(url, {**HOST_PAYLOAD, "venueName": "Sixth Arena"}, format="json")
    assert rejected.status_code == 429
    assert int(rejected["Retry-After"]) >= 1
    assert HostApplication.objects.count() == 5
    assert HostRateBucket.objects.get().accepted_count == 5


@pytest.mark.django_db(transaction=True)
def test_duplicate_host_submissions_are_atomic_under_concurrency():
    from apps.accounts.phone import normalize_iran_mobile

    valid = dict(HOST_PAYLOAD)
    valid["phone"] = normalize_iran_mobile(valid["phone"])
    with ThreadPoolExecutor(max_workers=5) as pool:
        items = list(pool.map(lambda _: receive_host_application(valid, "127.0.0.55"), range(5)))
    assert len({item.id for item in items}) == 1
    assert HostApplication.objects.count() == 1
    assert HostRateBucket.objects.get().accepted_count == 1
    connection.close()
