from django.contrib import admin
from django.urls import include, path

from apps.system.api.views import LiveView, ReadyView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/live/", LiveView.as_view(), name="live"),
    path("health/ready/", ReadyView.as_view(), name="ready"),
    path("api/v1/system/", include("apps.system.api.urls", namespace="system")),
    path("api/v1/", include("apps.accounts.api.urls", namespace="accounts")),
]
