"""Contextes globaux injectés dans chaque template."""

from . import panier


def infos_panier(request):
    """Expose le nombre d'articles du panier à tous les templates.

    Utile pour afficher le badge « Panier (N) » dans la navbar sans
    devoir passer la valeur depuis chaque vue.
    """
    return {"panier_nb_articles": panier.compter(request.session)}
