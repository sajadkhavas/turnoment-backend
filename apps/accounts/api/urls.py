from django.urls import path

from apps.accounts.dashboard import MyDashboardView

from .preferences import NotificationPreferencesView
from .profile_summary import MyProfileSummaryView
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
    path("me/dashboard/", MyDashboardView.as_view(), name="me-dashboard"),
    path("me/profile-summary/", MyProfileSummaryView.as_view(), name="my-profile-summary"),
    path("auth/me/profile/", MeProfileView.as_view(), name="me-profile"),
    path(
        "me/settings/notification-preferences/",
        NotificationPreferencesView.as_view(),
        name="notification-preferences",
    ),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("players/<str:gamer_tag>/", PublicPlayerView.as_view(), name="player-public"),
]
