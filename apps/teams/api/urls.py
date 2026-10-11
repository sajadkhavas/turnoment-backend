from django.urls import path

from .views import (
    CaptainTransferView,
    InvitationActionView,
    MyTeamInvitesView,
    MyTeamsView,
    TeamCreateView,
    TeamInviteView,
    TeamLeaveView,
)

app_name = "teams"

urlpatterns = [
    path("me/teams/", MyTeamsView.as_view(), name="me-teams"),
    path("me/team-invites/", MyTeamInvitesView.as_view(), name="my-team-invites"),
    path("teams/", TeamCreateView.as_view(), name="team-create"),
    path("teams/<uuid:team_id>/invites/", TeamInviteView.as_view(), name="team-invite"),
    path("teams/invites/<uuid:invite_id>/<str:action>/",
         InvitationActionView.as_view(), name="team-invite-action"),
    path("teams/<uuid:team_id>/captain/", CaptainTransferView.as_view(),
         name="team-captain-transfer"),
    path("teams/<uuid:team_id>/leave/", TeamLeaveView.as_view(), name="team-leave"),
]
