from django.urls import path

from .views import LiveView, MetaView, ReadyView

app_name = "system"

urlpatterns = [
    path("meta/", MetaView.as_view(), name="meta"),
    path("health/live/", LiveView.as_view(), name="api-live"),
    path("health/ready/", ReadyView.as_view(), name="api-ready"),
]
