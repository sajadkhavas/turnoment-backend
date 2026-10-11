from django.urls import path

from .views import CaseDetailView, CasesView, ReviewCaseView

app_name = "moderation"

urlpatterns = [
    path("operator/moderation/", CasesView.as_view(), name="cases"),
    path("operator/moderation/<uuid:case_id>/", CaseDetailView.as_view(), name="detail"),
    path("operator/moderation/<uuid:case_id>/review/", ReviewCaseView.as_view(), name="review"),
]
