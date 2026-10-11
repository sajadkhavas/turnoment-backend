from django.contrib import admin
from django.urls import include, path

from apps.system.api.views import LiveView, ReadyView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/live/", LiveView.as_view(), name="live"),
    path("health/ready/", ReadyView.as_view(), name="ready"),
    path("api/v1/system/", include("apps.system.api.urls", namespace="system")),
    path("api/v1/", include("apps.accounts.api.urls", namespace="accounts")),
    path("api/v1/me/matches/", __import__("apps.matches.api", fromlist=["MyMatchesView"]).MyMatchesView.as_view()),
    path("api/v1/matches/<uuid:match_id>/result/", __import__("apps.results.api", fromlist=["ResultView"]).ResultView.as_view()),
    path("api/v1/matches/<uuid:match_id>/result/confirm/", __import__("apps.results.api", fromlist=["ConfirmView"]).ConfirmView.as_view()),
    path("api/v1/matches/<uuid:match_id>/dispute/", __import__("apps.disputes.api", fromlist=["DisputeView"]).DisputeView.as_view()),
    path("api/v1/matches/<uuid:match_id>/dispute/<uuid:dispute_id>/evidence/", __import__("apps.disputes.api", fromlist=["EvidenceView"]).EvidenceView.as_view()),
]
