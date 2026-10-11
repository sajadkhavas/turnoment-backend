from django.urls import path

from .views import RulesetDetailView, RulesetListView

app_name = "rulesets"

urlpatterns = [
    path("rulesets/", RulesetListView.as_view(), name="list"),
    path("rulesets/<slug:key>/", RulesetDetailView.as_view(), name="detail"),
]
