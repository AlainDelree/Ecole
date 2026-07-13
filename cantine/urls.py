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
    path("panier/", views.panier_afficher, name="panier_afficher"),
    path(
        "panier/ajouter/",
        views.panier_ajouter,
        name="panier_ajouter",
    ),
    path(
        "panier/retirer/",
        views.panier_retirer,
        name="panier_retirer",
    ),
    path(
        "panier/vider/",
        views.panier_vider,
        name="panier_vider",
    ),
    path(
        "panier/valider/",
        views.panier_valider,
        name="panier_valider",
    ),
    path("historique/", views.historique, name="historique"),
    # --- Paiement (simulateur Mollie) --------------------------------
    path(
        "paiement/simulateur/",
        views.paiement_simulateur,
        name="paiement_simulateur",
    ),
    path(
        "paiement/confirmer/",
        views.paiement_confirmer,
        name="paiement_confirmer",
    ),
    path(
        "paiement/succes/",
        views.paiement_succes,
        name="paiement_succes",
    ),
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
    # --- Espace comptabilité ----------------------------------------
    path(
        "comptabilite/paiements/",
        views.comptabilite_paiements,
        name="comptabilite_paiements",
    ),
    path(
        "comptabilite/paiements/<int:pk>/valider/",
        views.comptabilite_paiement_valider,
        name="comptabilite_paiement_valider",
    ),
    path(
        "comptabilite/paiements/<int:pk>/rejeter/",
        views.comptabilite_paiement_rejeter,
        name="comptabilite_paiement_rejeter",
    ),
    path(
        "comptabilite/suivi-enfants/",
        views.comptabilite_suivi_enfants,
        name="comptabilite_suivi_enfants",
    ),
]
