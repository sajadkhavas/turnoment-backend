from django.urls import path

from .views import InboxView, ReadAllNotificationsView, ReadNotificationView

app_name = "notifications"

urlpatterns = [
    path("me/notifications/", InboxView.as_view(), name="list"),
    path("me/notifications/read-all/", ReadAllNotificationsView.as_view(), name="read-all"),
    path(
        "me/notifications/<uuid:notification_id>/read/",
        ReadNotificationView.as_view(), name="read",
    ),
]
