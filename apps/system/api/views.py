from django.conf import settings
from django.core.cache import cache
from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE
from rest_framework.views import APIView


class LiveView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok", "service": settings.SERVICE_NAME})


class ReadyView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        checks = {"database": False, "cache": False}

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                checks["database"] = cursor.fetchone() == (1,)
        except Exception:  # readiness must fail closed without leaking infrastructure errors
            checks["database"] = False

        try:
            key = "turnoment:health:ready"
            cache.set(key, "ok", timeout=5)
            checks["cache"] = cache.get(key) == "ok"
        except Exception:  # readiness must fail closed without leaking infrastructure errors
            checks["cache"] = False

        ready = all(checks.values())
        return Response(
            {"status": "ready" if ready else "not_ready", "checks": checks},
            status=HTTP_200_OK if ready else HTTP_503_SERVICE_UNAVAILABLE,
        )


class MetaView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "service": settings.SERVICE_NAME,
                "api_version": settings.API_VERSION,
                "frontend_baseline_sha": settings.FRONTEND_BASELINE_SHA,
            }
        )
