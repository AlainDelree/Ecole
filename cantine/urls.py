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
    # --- Espace cuisinière ------------------------------------------
    path(
        "cuisine/calendrier/",
        views.cuisine_calendrier,
        name="cuisine_calendrier",
    ),
    path(
        "cuisine/aujourdhui/",
        views.cuisine_aujourdhui,
        name="cuisine_aujourdhui",
    ),
    path(
        "cuisine/jour/<str:date>/",
        views.cuisine_jour,
        name="cuisine_jour",
    ),
    path(
        "cuisine/reservation/<int:reservation_id>/mangee/",
        views.cuisine_marquer_mangee,
        name="cuisine_marquer_mangee",
    ),
    path(
        "cuisine/menus/",
        views.cuisine_menus,
        name="cuisine_menus",
    ),
    path(
        "cuisine/menus/creer/",
        views.cuisine_menu_creer,
        name="cuisine_menu_creer",
    ),
    path(
        "cuisine/menus/<int:pk>/modifier/",
        views.cuisine_menu_modifier,
        name="cuisine_menu_modifier",
    ),
    path(
        "cuisine/menus/<int:pk>/supprimer/",
        views.cuisine_menu_supprimer,
        name="cuisine_menu_supprimer",
    ),
]
