"""Décorateurs d'autorisation pour les vues métier."""

from django.contrib.auth.decorators import user_passes_test


NOM_GROUPE_CUISINE = "Cuisine"
NOM_GROUPE_COMPTABILITE = "Comptabilite"


def _est_cuisine(user):
    return (
        user.is_authenticated
        and user.groups.filter(name=NOM_GROUPE_CUISINE).exists()
    )


cuisine_required = user_passes_test(
    _est_cuisine,
    login_url="cantine:connexion",
)
"""Restreint l'accès aux membres du groupe « Cuisine ».

Redirige vers la page de connexion si l'utilisateur n'est pas connecté
ou s'il l'est mais n'appartient pas au groupe.
"""


def _est_comptabilite(user):
    return (
        user.is_authenticated
        and user.groups.filter(name=NOM_GROUPE_COMPTABILITE).exists()
    )


comptabilite_required = user_passes_test(
    _est_comptabilite,
    login_url="cantine:connexion",
)
"""Restreint l'accès aux membres du groupe « Comptabilite ».

Même patron que `cuisine_required` : redirige vers la connexion si
l'utilisateur n'est pas connecté ou n'appartient pas au groupe.
"""
