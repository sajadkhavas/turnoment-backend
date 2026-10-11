from django.urls import path

from .api import (
    ChallengeCancelView,
    ChallengeHubView,
    ChallengeResponseView,
    OpponentSearchView,
)

app_name = "challenges"

urlpatterns = [
    path("me/challenges/", ChallengeHubView.as_view(), name="hub"),
    path("me/challenges/opponents/", OpponentSearchView.as_view(), name="opponents"),
    path("me/challenges/<uuid:challenge_id>/response/", ChallengeResponseView.as_view(), name="response"),
    path("me/challenges/<uuid:challenge_id>/cancel/", ChallengeCancelView.as_view(), name="cancel"),
]
