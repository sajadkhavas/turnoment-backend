"""Reusable B01 HTTP assertions without bypassing P01 session authentication."""

from rest_framework.test import APIClient


def session_client(user, *, enforce_csrf_checks: bool = False) -> APIClient:
    client = APIClient(enforce_csrf_checks=enforce_csrf_checks)
    client.force_login(user)
    return client


def assert_contract_error(response, *, status: int, code: str):
    assert response.status_code == status
    assert isinstance(response.data, dict)
    assert response.data["error"]["code"] == code
    assert isinstance(response.data["error"]["message"], str)
    assert response.data["error"]["message"]
