from django.urls import path

from apps.notifications.push_api import PushConfigurationView, PushSubscriptionView

from .views import InboxView, ReadAllNotificationsView, ReadNotificationView

app_name = "notifications"

urlpatterns = [
    path("me/notifications/push/config/", PushConfigurationView.as_view()),
    path("me/notifications/push/subscription/", PushSubscriptionView.as_view()),
    path("me/notifications/", InboxView.as_view(), name="list"),
    path("me/notifications/read-all/", ReadAllNotificationsView.as_view(), name="read-all"),
    path(
        "me/notifications/<uuid:notification_id>/read/",
        ReadNotificationView.as_view(),
        name="read",
    ),
]
