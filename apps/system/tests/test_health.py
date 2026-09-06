from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class SystemApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_liveness_is_public(self):
        response = self.client.get("/health/live/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_readiness_checks_database_and_cache(self):
        response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ready")
        self.assertEqual(response.json()["checks"], {"database": True, "cache": True})

    def test_meta_exposes_contract_baseline(self):
        response = self.client.get(reverse("system:meta"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["api_version"], "v1")
        self.assertEqual(
            payload["frontend_baseline_sha"],
            "8d5736d788235e3e99765a5332f79f0cba861482",
        )
