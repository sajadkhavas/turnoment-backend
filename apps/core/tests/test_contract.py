import pytest
from django.conf import settings
from django.middleware.csrf import get_token
from django.test import override_settings
from django.urls import path
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.core.api.views import CoreAPIView, CoreGenericAPIView
from apps.core.identifiers import public_id, uuid_public_id
from apps.core.testing import assert_contract_error, session_client


class SecuredView(CoreAPIView):
    def get(self, request):
        return Response({"id": str(request.user.id)})

    def post(self, request):
        return Response({"accepted": True})


class ValidationView(CoreAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        raise ValidationError({"nickname": ["Required."]})


class ListView(CoreGenericAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = User.objects.order_by("id")

    def get(self, request):
        page = self.paginate_queryset(self.get_queryset())
        return self.get_paginated_response([str(user.id) for user in page])


class CsrfBootstrapView(CoreAPIView):
    def get(self, request):
        return Response({"csrf_token": get_token(request)})


urlpatterns = [
    path("api/v1/core-test/secured/", SecuredView.as_view()),
    path("api/v1/core-test/validation/", ValidationView.as_view()),
    path("api/v1/core-test/list/", ListView.as_view()),
    path("api/v1/core-test/csrf/", CsrfBootstrapView.as_view()),
]


def test_identifier_contract_from_frozen_frontend():
    from uuid import uuid4

    assert public_id("abc_ABC-123") == "abc_ABC-123"
    assert public_id("x" * 128) == "x" * 128
    assert public_id(uuid_public_id(uuid4()))
    for invalid in ["", "leading space", "é", "abc.", "x" * 129, None, 123, "a/b"]:
        with pytest.raises(ValidationError):
            public_id(invalid)
    with pytest.raises(TypeError):
        uuid_public_id("not-a-uuid")


@pytest.mark.django_db
@override_settings(ROOT_URLCONF=__name__)
def test_core_error_envelope_validation_and_unauthenticated():
    assert_contract_error(
        APIClient().get("/api/v1/core-test/secured/"), status=403, code="not_authenticated",
    )
    response = APIClient().get("/api/v1/core-test/validation/")
    assert_contract_error(response, status=400, code="validation_error")
    assert response.data["error"]["fields"] == {"nickname": ["Required."]}


@pytest.mark.django_db
@override_settings(ROOT_URLCONF=__name__)
def test_core_permission_session_and_csrf_preserved():
    user = User.objects.create_user(phone="09123456789")
    client = session_client(user, enforce_csrf_checks=True)
    assert client.get("/api/v1/core-test/secured/").status_code == 200
    rejected = client.post("/api/v1/core-test/secured/", {}, format="json")
    assert_contract_error(rejected, status=403, code="permission_denied")
    token = client.get("/api/v1/core-test/csrf/").data["csrf_token"]
    accepted = client.post(
        "/api/v1/core-test/secured/", {}, format="json", HTTP_X_CSRFTOKEN=token,
    )
    assert accepted.status_code == 200
    assert settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] == [
        "rest_framework.authentication.SessionAuthentication"
    ]
    assert settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] == [
        "rest_framework.permissions.IsAuthenticated"
    ]


@pytest.mark.django_db
@override_settings(ROOT_URLCONF=__name__)
def test_pagination_matches_frozen_page_shape_and_rejects_bad_input():
    for n in range(3):
        User.objects.create_user(phone=f"0912000000{n}")
    url = "/api/v1/core-test/list/?pageSize=2"
    page = APIClient().get(url)
    assert page.status_code == 200
    assert set(page.data) == {"schemaVersion", "items", "pagination"}
    assert page.data["schemaVersion"] == 1
    assert len(page.data["items"]) == 2
    assert page.data["pagination"] == {
        "currentPage": 1, "totalPages": 2, "totalItems": 3, "pageSize": 2,
    }
    second = APIClient().get(url + "&page=2")
    assert second.status_code == 200
    assert len(second.data["items"]) == 1
    for invalid in ("0", "-1", "101", "oops", "1.5", " 2"):
        response = APIClient().get(f"/api/v1/core-test/list/?pageSize={invalid}")
        assert_contract_error(response, status=400, code="validation_error")


@pytest.mark.django_db
@override_settings(ROOT_URLCONF=__name__)
def test_pagination_rejects_out_of_range_page():
    response = APIClient().get("/api/v1/core-test/list/?page=99")
    assert_contract_error(response, status=404, code="not_found")
