"""Panier de réservation en session (multi-jours, multi-enfants).

Le panier est stocké dans `request.session["panier"]` sous forme
d'une liste d'entrées `{"enfant_id": int, "menu_id": int, "formule": str}`.
Aucun modèle de base de données : il vit le temps de la session parent.

Ce module isole toute la manipulation du panier (ajout, suppression,
hydratation à partir des ORM enfants/menus, purge des entrées devenues
invalides) pour que les vues restent lisibles.
"""

from django.utils import timezone

from .models import Enfant, Menu, Reservation


SESSION_KEY = "panier"


def _liste_brute(session):
    """Retourne une copie mutable de la liste stockée en session."""
    return list(session.get(SESSION_KEY, []))


def _sauvegarder(session, entrees):
    session[SESSION_KEY] = entrees
    session.modified = True


def compter(session):
    """Nombre d'articles actuellement dans le panier."""
    return len(_liste_brute(session))


def couples_presents(session):
    """Retourne l'ensemble des couples ``(enfant_id, menu_id)`` du panier.

    Permet à la vue calendrier de savoir, pour chaque enfant et chaque
    menu affiché, si l'entrée est déjà dans le panier de session — et
    donc d'afficher un état « Déjà dans le panier » plutôt qu'un
    bouton d'ajout identique.
    """
    return {
        (e["enfant_id"], e["menu_id"]) for e in _liste_brute(session)
    }


def ajouter(session, enfant_id, menu_id, formule):
    """Ajoute une entrée au panier ; met à jour la formule si déjà présente.

    Retourne True si une nouvelle entrée a été créée, False si la ligne
    (enfant, menu) existait déjà (seule la formule est alors remplacée).
    """
    entrees = _liste_brute(session)
    enfant_id = int(enfant_id)
    menu_id = int(menu_id)
    for existante in entrees:
        if existante["enfant_id"] == enfant_id and existante["menu_id"] == menu_id:
            existante["formule"] = formule
            _sauvegarder(session, entrees)
            return False
    entrees.append(
        {"enfant_id": enfant_id, "menu_id": menu_id, "formule": formule}
    )
    _sauvegarder(session, entrees)
    return True


def supprimer(session, index):
    """Supprime l'entrée à l'index donné ; renvoie True si suppression effective."""
    entrees = _liste_brute(session)
    if 0 <= index < len(entrees):
        entrees.pop(index)
        _sauvegarder(session, entrees)
        return True
    return False


def vider(session):
    """Vide totalement le panier."""
    if SESSION_KEY in session:
        del session[SESSION_KEY]
        session.modified = True


def lignes_hydratees(session, profil):
    """Charge les entrées du panier et les enrichit avec les objets ORM.

    Filtre silencieusement les entrées devenues invalides :
      - enfant qui n'appartient plus au parent,
      - menu supprimé ou dont la clôture est passée,
      - réservation déjà créée pour ce couple (enfant, menu).

    Renvoie un tuple ``(lignes_valides, indices_perdus)`` — les indices
    perdus permettent à la vue de purger le panier de ces entrées mortes.
    """
    entrees = _liste_brute(session)
    if not entrees:
        return [], []

    enfant_ids = {e["enfant_id"] for e in entrees}
    menu_ids = {e["menu_id"] for e in entrees}
    enfants = {
        e.id: e
        for e in Enfant.objects.select_related("classe").filter(
            id__in=enfant_ids, parent=profil
        )
    }
    menus = {m.id: m for m in Menu.objects.filter(id__in=menu_ids)}
    formules_valides = {code for code, _ in Reservation.FORMULE_CHOICES}
    libelles_formule = dict(Reservation.FORMULE_CHOICES)

    # Réservations déjà existantes pour ces couples : évite les doublons
    # (unique_together) au moment de valider le panier.
    resas_existantes = set(
        Reservation.objects.filter(
            enfant_id__in=enfant_ids,
            menu_id__in=menu_ids,
        ).values_list("enfant_id", "menu_id")
    )
    maintenant = timezone.now()

    lignes = []
    perdues = []
    for index, entree in enumerate(entrees):
        enfant = enfants.get(entree["enfant_id"])
        menu = menus.get(entree["menu_id"])
        formule = entree.get("formule", Reservation.FORMULE_COMPLET)
        if formule not in formules_valides:
            formule = Reservation.FORMULE_COMPLET
        if (
            enfant is None
            or menu is None
            or menu.ferme_a <= maintenant
            or (enfant.id, menu.id) in resas_existantes
        ):
            perdues.append(index)
            continue
        prix_cents = menu.prix_pour(enfant, formule)
        lignes.append(
            {
                "index": index,
                "enfant": enfant,
                "menu": menu,
                "formule": formule,
                "formule_display": libelles_formule[formule],
                "prix_cents": prix_cents,
                "prix_euros": round(prix_cents / 100, 2),
            }
        )
    return lignes, perdues


def purger_invalides(session, indices_perdus):
    """Supprime les entrées identifiées comme invalides par `lignes_hydratees`."""
    if not indices_perdus:
        return
    entrees = _liste_brute(session)
    for i in sorted(indices_perdus, reverse=True):
        if 0 <= i < len(entrees):
            entrees.pop(i)
    _sauvegarder(session, entrees)
