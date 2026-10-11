from django.contrib import admin
from django.urls import include, path

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
    path("api/v1/", include("apps.rankings.api_urls", namespace="rankings")),
    path("api/v1/", include("apps.rivalries.api_urls", namespace="rivalries")),
]
