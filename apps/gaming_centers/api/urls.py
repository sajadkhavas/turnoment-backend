from django.urls import path

from .views import (
    CenterDetailView,
    CenterDirectoryView,
    CenterEquipmentView,
    CenterOpeningHoursView,
    CenterProfileView,
    CenterStaffDetailView,
    CenterStaffView,
    CenterStationView,
    HostApplicationView,
)

app_name = "gaming_centers"

urlpatterns = [
    path("centers/", CenterDirectoryView.as_view(), name="list"),
    path("centers/<slug:public_id>/", CenterDetailView.as_view(), name="detail"),
    path("host-applications/", HostApplicationView.as_view(), name="host-create"),
    path("center-admin/centers/<uuid:center_id>/", CenterProfileView.as_view(), name="profile"),
    path("center-admin/centers/<uuid:center_id>/staff/", CenterStaffView.as_view(), name="staff"),
    path("center-admin/centers/<uuid:center_id>/staff/<uuid:membership_id>/",
         CenterStaffDetailView.as_view(), name="staff-detail"),
    path("center-admin/centers/<uuid:center_id>/equipment/",
         CenterEquipmentView.as_view(), name="equipment"),
    path("center-admin/centers/<uuid:center_id>/stations/",
         CenterStationView.as_view(), name="stations"),
    path("center-admin/centers/<uuid:center_id>/hours/",
         CenterOpeningHoursView.as_view(), name="hours"),
]
