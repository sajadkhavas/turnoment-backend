from django.urls import path

from .views import GameCatalogView, GameDetailView, PublicHomeView

app_name = "games"

urlpatterns = [
    path("games/", GameCatalogView.as_view(), name="catalog"),
    path("games/<slug:slug>/", GameDetailView.as_view(), name="detail"),
    path("discovery/home/", PublicHomeView.as_view(), name="home"),
]
