from django.urls import path

from .views import MyAchievementsView

app_name = "achievements"
urlpatterns = [path("me/achievements/", MyAchievementsView.as_view(), name="me-achievements")]
