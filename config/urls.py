from django.contrib import admin
from django.urls import include, path

from apps.disputes.api import DisputeView, EvidenceView
from apps.matches.api import MyMatchesView
from apps.rankings.api import PublicCompetitiveProfileView, PublicRankingView
from apps.results.api import ConfirmView, ResultView
from apps.rivalries.api import MyRivalriesView
from apps.system.api.views import LiveView, ReadyView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/live/", LiveView.as_view(), name="live"),
    path("health/ready/", ReadyView.as_view(), name="ready"),
    path("api/v1/system/", include("apps.system.api.urls", namespace="system")),
    path("api/v1/", include("apps.accounts.api.urls", namespace="accounts")),
    path("api/v1/", include("apps.games.api.urls", namespace="games")),
    path("api/v1/", include("apps.rulesets.api.urls", namespace="rulesets")),
    path("api/v1/", include("apps.gaming_centers.api.urls", namespace="gaming_centers")),
    path("api/v1/", include("apps.tournaments.api.urls", namespace="tournaments")),
    path("api/v1/", include("apps.teams.api.urls", namespace="teams")),
    path("api/v1/", include("apps.achievements.api.urls", namespace="achievements")),
    path("api/v1/", include("apps.challenges.urls", namespace="challenges")),
    path("api/v1/", include("apps.notifications.api.urls", namespace="notifications")),
    path("api/v1/", include("apps.moderation.api.urls", namespace="moderation")),
    path("api/v1/rankings/", PublicRankingView.as_view(), name="public-ranking"),
    path("api/v1/me/rivalries/", MyRivalriesView.as_view(), name="my-rivalries"),
    path(
        "api/v1/players/<str:username>/public-profile/",
        PublicCompetitiveProfileView.as_view(), name="public-competitive-profile",
    ),
    path("api/v1/me/matches/", MyMatchesView.as_view()),
    path("api/v1/matches/<uuid:match_id>/result/", ResultView.as_view()),
    path("api/v1/matches/<uuid:match_id>/result/confirm/", ConfirmView.as_view()),
    path("api/v1/matches/<uuid:match_id>/dispute/", DisputeView.as_view()),
    path(
        "api/v1/matches/<uuid:match_id>/dispute/<uuid:dispute_id>/evidence/",
        EvidenceView.as_view(),
    ),
]
