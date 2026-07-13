"""Générateur combinatoire de suggestions de menus scolaires.

Plutôt qu'une liste figée (voir `idees_menus.py`), ce module compose des
plats à la volée à partir de quatre briques : une protéine, un féculent,
un légume et une sauce/accompagnement. Le nombre de combinaisons possibles
dépasse très largement le millier (voir `nombre_combinaisons_possibles`),
ce qui donne une variété quasi inépuisable sans rien maintenir à la main.

Aucun appel réseau, API ou LLM : tout est calculé localement et
instantanément à partir des listes ci-dessous.

Contraintes respectées dans les données :
- Aucun porc dans les protéines.
- Aucun alcool dans les sauces/accompagnements.
- Chaque suggestion associe une base protéique/féculente + un légume au
  minimum : elle est donc toujours équilibrée par construction.
- Chaque protéine est marquée végétarienne ou non (`vegetarien`).
- Chaque ingrédient reste compatible avec un budget scolaire : les
  protéines portent une `categorie_budget` ("economique" ou "standard")
  et les listes excluent d'emblée les produits chers (saumon, fruits de
  mer, viandes nobles). Les féculents, légumes et sauces retenus sont
  tous des basiques économiques ou standards.
"""

import random


# --- Les quatre briques de composition ---------------------------------

# Protéines : ~17 entrées, aucune à base de porc. Chaque dict indique si
# la protéine est végétarienne et sa catégorie de budget.
PROTEINES = [
    # Volailles et viandes blanches / hachées (non végétariennes)
    {"nom": "Poulet", "vegetarien": False, "categorie_budget": "standard"},
    {"nom": "Émincé de dinde", "vegetarien": False, "categorie_budget": "standard"},
    {"nom": "Escalope de volaille", "vegetarien": False, "categorie_budget": "standard"},
    {"nom": "Boulettes de bœuf", "vegetarien": False, "categorie_budget": "standard"},
    {"nom": "Émincé de bœuf", "vegetarien": False, "categorie_budget": "standard"},
    {"nom": "Haché de veau", "vegetarien": False, "categorie_budget": "standard"},
    # Poissons courants (pas de saumon ni de fruits de mer)
    {"nom": "Cabillaud", "vegetarien": False, "categorie_budget": "standard"},
    {"nom": "Colin", "vegetarien": False, "categorie_budget": "economique"},
    {"nom": "Merlu", "vegetarien": False, "categorie_budget": "standard"},
    {"nom": "Poisson pané", "vegetarien": False, "categorie_budget": "economique"},
    {"nom": "Thon", "vegetarien": False, "categorie_budget": "economique"},
    # Options végétariennes (œufs, légumineuses, tofu, fromage)
    {"nom": "Omelette", "vegetarien": True, "categorie_budget": "economique"},
    {"nom": "Œuf dur", "vegetarien": True, "categorie_budget": "economique"},
    {"nom": "Pois chiches", "vegetarien": True, "categorie_budget": "economique"},
    {"nom": "Lentilles", "vegetarien": True, "categorie_budget": "economique"},
    {"nom": "Haricots rouges", "vegetarien": True, "categorie_budget": "economique"},
    {"nom": "Tofu", "vegetarien": True, "categorie_budget": "standard"},
    {"nom": "Galette de légumes", "vegetarien": True, "categorie_budget": "standard"},
    {"nom": "Gratin de fromage", "vegetarien": True, "categorie_budget": "standard"},
]

# Féculents : ~10 basiques économiques.
FECULENTS = [
    "riz",
    "pâtes",
    "pommes de terre vapeur",
    "purée",
    "frites au four",
    "semoule",
    "quinoa",
    "blé",
    "pommes de terre rissolées",
    "pain",
]

# Légumes : ~14 entrées courantes.
LEGUMES = [
    "carottes",
    "brocolis",
    "haricots verts",
    "épinards",
    "courgettes",
    "ratatouille",
    "salade verte",
    "petits pois",
    "chou-fleur",
    "poireaux",
    "tomates",
    "julienne de légumes",
    "poêlée de légumes",
    "betteraves rouges",
]

# Sauces / accompagnements : ~10 entrées, AUCUN alcool (pas de sauce au
# vin, à la bière, au madère, etc.).
SAUCES_ACCOMPAGNEMENTS = [
    "sauce tomate",
    "sauce curry doux",
    "sauce blanche",
    "béchamel",
    "sauce champignons",
    "sauce provençale",
    "jus (gravy)",
    "sauce fromage",
    "vinaigrette",
    "sans sauce",
]


# --- Composition d'un nom lisible --------------------------------------

def _composer_nom(proteine, feculent, legume, sauce):
    """Assemble un nom de plat lisible en français.

    Ex. : ("Poulet", "riz", "brocolis", "sauce curry doux")
        -> "Poulet, riz, brocolis, sauce curry doux".

    La première lettre est mise en majuscule ; les briques sont séparées
    par des virgules dans l'ordre protéine / féculent / légume / sauce.
    """
    parties = [proteine, feculent, legume, sauce]
    nom = ", ".join(parties)
    return nom[:1].upper() + nom[1:]


def _normaliser(nom):
    """Clé de comparaison insensible à la casse et aux espaces de bord."""
    return (nom or "").strip().casefold()


# --- Génération ---------------------------------------------------------

def generer_suggestion_menu(vegetarien_uniquement=False, exclure_recents=None):
    """Tire une suggestion de plat combinatoire.

    Choisit aléatoirement une protéine (uniquement végétarienne si
    `vegetarien_uniquement=True`), un féculent, un légume et une
    sauce/accompagnement, puis compose un nom lisible en français.

    `exclure_recents` peut être un itérable de noms de plats déjà servis
    récemment (même logique d'exclusion sur 14 jours que l'existant) :
    les combinaisons dont le nom normalisé y figure sont évitées. On
    tente plusieurs tirages ; comme il existe des milliers de
    combinaisons et seulement une poignée de plats récents, un tirage
    acceptable est trouvé quasi immédiatement.

    Retourne le nom du plat (str).
    """
    exclus = {_normaliser(p) for p in (exclure_recents or [])}
    proteines = (
        [p for p in PROTEINES if p["vegetarien"]]
        if vegetarien_uniquement
        else PROTEINES
    )

    nom = None
    for _ in range(50):  # bornage anti-boucle infinie
        proteine = random.choice(proteines)
        feculent = random.choice(FECULENTS)
        legume = random.choice(LEGUMES)
        sauce = random.choice(SAUCES_ACCOMPAGNEMENTS)
        nom = _composer_nom(proteine["nom"], feculent, legume, sauce)
        if _normaliser(nom) not in exclus:
            return nom
    # Si tout est « récent » (extrêmement improbable), on renvoie le
    # dernier tirage plutôt que rien.
    return nom


def generer_suggestions(nb=8, vegetarien_uniquement=False, exclure_recents=None):
    """Retourne jusqu'à `nb` suggestions de plats *uniques*.

    Enveloppe pratique pour l'interface : appelle `generer_suggestion_menu`
    en boucle et déduplique les noms. Renvoie une liste de chaînes.
    """
    suggestions = []
    vus = set()
    # On borne le nombre de tentatives pour rester instantané même si le
    # pool demandé approche le nombre de combinaisons disponibles.
    for _ in range(nb * 20):
        if len(suggestions) >= nb:
            break
        nom = generer_suggestion_menu(vegetarien_uniquement, exclure_recents)
        cle = _normaliser(nom)
        if cle and cle not in vus:
            vus.add(cle)
            suggestions.append(nom)
    return suggestions


def nombre_combinaisons_possibles(vegetarien_uniquement=False):
    """Nombre total de plats distincts que le générateur peut composer.

    Produit des tailles des quatre listes. En mode végétarien, seules les
    protéines végétariennes sont comptées.

    Calcul (au 2026-07) :
      - Toutes protéines : 19 × 10 × 14 × 10 = 26 600 combinaisons.
      - Végétariennes    :  8 × 10 × 14 × 10 = 11 200 combinaisons.
    Dans les deux cas, on dépasse très largement l'objectif de 1000.
    """
    nb_proteines = (
        sum(1 for p in PROTEINES if p["vegetarien"])
        if vegetarien_uniquement
        else len(PROTEINES)
    )
    return nb_proteines * len(FECULENTS) * len(LEGUMES) * len(SAUCES_ACCOMPAGNEMENTS)
