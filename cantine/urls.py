"""URLs de l'app cantine (partie parents)."""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


app_name = "cantine"

urlpatterns = [
    path("", views.racine, name="racine"),
    path("accueil/", views.accueil, name="accueil"),
    path("inscription/", views.inscription, name="inscription"),
    path(
        "connexion/",
        auth_views.LoginView.as_view(
            template_name="cantine/connexion.html",
        ),
        name="connexion",
    ),
    path(
        "deconnexion/",
        auth_views.LogoutView.as_view(),
        name="deconnexion",
    ),
    path("calendrier/", views.calendrier, name="calendrier"),
    path(
        "calendrier/reserver/",
        views.reserver_menu,
        name="reserver_menu",
    ),
    path("historique/", views.historique, name="historique"),
    path(
        "declarer-virement/",
        views.declarer_virement,
        name="declarer_virement",
    ),
]
