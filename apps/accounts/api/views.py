from django.contrib.auth import login, logout
from django.db import IntegrityError
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_503_SERVICE_UNAVAILABLE,
)
from rest_framework.views import APIView

from apps.accounts.exceptions import (
    AccountInactive,
    AccountsDomainError,
    OtpRateLimited,
)
from apps.accounts.models import PlayerProfile
from apps.accounts.otp import OtpDeliveryUnavailable
from apps.accounts.services import issue_login_otp, verify_login_otp

from .serializers import (
    MeSerializer,
    OtpRequestSerializer,
    OtpVerifySerializer,
    PrivatePlayerProfileSerializer,
    PublicPlayerSerializer,
)


def _error(code: str, message: str, *, status: int, extra: dict | None = None) -> Response:
    payload = {"error": {"code": code, "message": message}}
    if extra:
        payload["error"].update(extra)
    return Response(payload, status=status)


def _request_ip(request) -> str | None:
    value = request.META.get("REMOTE_ADDR")
    return value or None


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrf_token": get_token(request)}, status=HTTP_200_OK)


@method_decorator(csrf_protect, name="dispatch")
class OtpRequestView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OtpRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            issued = issue_login_otp(
                phone=serializer.validated_data["phone"],
                request_ip=_request_ip(request),
            )
        except OtpRateLimited as exc:
            response = _error(
                exc.code,
                str(exc),
                status=HTTP_429_TOO_MANY_REQUESTS,
                extra={"retry_after": exc.retry_after},
            )
            response["Retry-After"] = str(exc.retry_after)
            return response
        except OtpDeliveryUnavailable:
            return _error(
                "otp_delivery_unavailable",
                "ارسال کد ورود در حال حاضر در دسترس نیست.",
                status=HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "challenge_id": str(issued.challenge.id),
                "expires_in": issued.expires_in,
                "resend_after": issued.resend_after,
            },
            status=HTTP_201_CREATED,
        )


@method_decorator(csrf_protect, name="dispatch")
class OtpVerifyView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OtpVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = verify_login_otp(**serializer.validated_data)
        except AccountInactive as exc:
            return _error(exc.code, str(exc), status=HTTP_403_FORBIDDEN)
        except AccountsDomainError as exc:
            return _error(exc.code, str(exc), status=HTTP_400_BAD_REQUEST)

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return Response(MeSerializer(user).data, status=HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data, status=HTTP_200_OK)


class MeProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile, _ = PlayerProfile.objects.get_or_create(user=request.user)
        serializer = PrivatePlayerProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except IntegrityError:
            return _error(
                "gamer_tag_conflict",
                "این شناسه بازیکن قبلاً استفاده شده است.",
                status=HTTP_400_BAD_REQUEST,
            )
        return Response(serializer.data, status=HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=HTTP_204_NO_CONTENT)


class PublicPlayerView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, gamer_tag: str):
        profile = (
            PlayerProfile.objects.select_related("user")
            .filter(gamer_tag__iexact=gamer_tag, user__is_active=True)
            .first()
        )
        if profile is None:
            return _error(
                "player_not_found",
                "بازیکن پیدا نشد.",
                status=HTTP_404_NOT_FOUND,
            )
        return Response(PublicPlayerSerializer(profile).data, status=HTTP_200_OK)
