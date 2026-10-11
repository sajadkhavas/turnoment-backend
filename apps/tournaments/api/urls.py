from django.urls import path

from .views import (
    MyTournamentsView,
    TournamentCheckInView,
    TournamentDetailView,
    TournamentDiscoveryView,
    TournamentRegistrationContextView,
    TournamentRegistrationView,
)

app_name = "tournaments"

urlpatterns = [
    path("tournaments/", TournamentDiscoveryView.as_view(), name="discovery"),
    path("tournaments/<str:identifier>/", TournamentDetailView.as_view(), name="detail"),
    path(
        "tournaments/<str:identifier>/registration/",
        TournamentRegistrationContextView.as_view(), name="registration-context"
    ),
    path(
        "tournaments/<str:identifier>/registrations/",
        TournamentRegistrationView.as_view(), name="registration"
    ),
    path(
        "tournaments/<str:identifier>/check-in/",
        TournamentCheckInView.as_view(), name="check-in"
    ),
    path("me/tournaments/", MyTournamentsView.as_view(), name="my-tournaments"),
]
