from django.contrib import admin
from django.urls import include, path

from apps.disputes.api import DisputeView, EvidenceView
from apps.matches.api import MyMatchesView
from apps.results.api import ConfirmView, ResultView
from apps.system.api.views import LiveView, ReadyView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/live/", LiveView.as_view(), name="live"),
    path("health/ready/", ReadyView.as_view(), name="ready"),
    path("api/v1/system/", include("apps.system.api.urls", namespace="system")),
    path("api/v1/", include("apps.accounts.api.urls", namespace="accounts")),
    path("api/v1/me/matches/", MyMatchesView.as_view()),
    path("api/v1/matches/<uuid:match_id>/result/", ResultView.as_view()),
    path("api/v1/matches/<uuid:match_id>/result/confirm/", ConfirmView.as_view()),
    path("api/v1/matches/<uuid:match_id>/dispute/", DisputeView.as_view()),
    path(
        "api/v1/matches/<uuid:match_id>/dispute/<uuid:dispute_id>/evidence/", EvidenceView.as_view()
    ),
]
