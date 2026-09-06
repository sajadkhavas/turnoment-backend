from django.urls import path

from .views import (
    CsrfView,
    LogoutView,
    MeProfileView,
    MeView,
    OtpRequestView,
    OtpVerifyView,
    PublicPlayerView,
)

app_name = "accounts"

urlpatterns = [
    path("auth/csrf/", CsrfView.as_view(), name="csrf"),
    path("auth/otp/request/", OtpRequestView.as_view(), name="otp-request"),
    path("auth/otp/verify/", OtpVerifyView.as_view(), name="otp-verify"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/me/profile/", MeProfileView.as_view(), name="me-profile"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("players/<str:gamer_tag>/", PublicPlayerView.as_view(), name="player-public"),
]
