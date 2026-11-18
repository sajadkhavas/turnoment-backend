from django.urls import path

from .public import PublicTeamDetail, PublicTeamList
from .views import (
    CaptainTransferView,
    CenterTeamInviteView,
    CenterTeamView,
    InvitationActionView,
    ManagedCentersView,
    MyTeamInvitesView,
    MyTeamsView,
    TeamCreateView,
    TeamInviteView,
    TeamLeaveView,
)

app_name = "teams"

urlpatterns = [
    path("public/teams/", PublicTeamList.as_view(), name="public-teams"),
    path("public/teams/<uuid:team_id>/", PublicTeamDetail.as_view(), name="public-team"),
    path("me/team-centers/", ManagedCentersView.as_view(), name="team-centers"),
    path("center-teams/<uuid:team_id>/invites/", CenterTeamInviteView.as_view(),
         name="center-team-invite"),
    path("centers/<uuid:center_id>/team/", CenterTeamView.as_view(), name="center-team"),
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
