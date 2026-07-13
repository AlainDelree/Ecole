"""Liste statique d'idées de plats scolaires pour la cuisinière.

Cette liste sert d'aide à la décision au moment de créer un menu :
elle alimente les suggestions cliquables affichées sur le formulaire de
création (`/cuisine/menus/creer/`). Aucun appel réseau, API ou LLM :
tout fonctionne hors-ligne à partir de ces chaînes de caractères.

On mélange plats belges classiques, plats familiaux courants dans les
cantines et quelques options végétariennes. Chaque entrée décrit le
« plat principal » tel qu'il apparaîtra dans le champ texte du menu ;
la cuisinière reste libre de la modifier ou d'en saisir un autre.
"""

# Idées de plats scolaires typiques (env. 50 suggestions).
IDEES_MENUS = [
    # Plats belges / familiaux classiques
    "Spaghetti bolognaise",
    "Vol-au-vent frites",
    "Boulettes sauce tomate purée",
    "Boulettes sauce liégeoise frites",
    "Poulet rôti pommes de terre",
    "Waterzooï de poulet",
    "Carbonnades flamandes frites",
    "Stoemp saucisse",
    "Chicons au gratin",
    "Filet américain frites",
    "Poisson pané légumes",
    "Cabillaud sauce blanche pommes vapeur",
    "Filet de poulet sauce champignons riz",
    "Blanquette de veau riz",
    "Rôti de porc compote purée",
    "Hachis Parmentier",
    "Vol-au-vent riz",
    "Chipolatas purée",
    "Cordon bleu frites",
    "Escalope milanaise pâtes",
    "Bœuf mironton pommes vapeur",
    "Potée aux poireaux",
    "Jambon braisé sauce madère purée",
    # Pâtes, gratins et plats mijotés
    "Gratin de pâtes jambon",
    "Macaroni au fromage et jambon",
    "Lasagnes à la bolognaise",
    "Gratin de chou-fleur béchamel",
    "Riz cantonais",
    "Chili con carne riz",
    "Pain de viande sauce tomate purée",
    "Saucisse de campagne chou rouge",
    "Curry de poulet riz",
    "Couscous poulet",
    "Couscous merguez",
    "Tajine de poulet légumes semoule",
    "Émincé de dinde sauce curry riz",
    # Poissons
    "Filet de saumon riz brocolis",
    "Colin sauce mousseline pommes vapeur",
    "Fish and chips petits pois",
    "Waterzooï de poisson",
    # Options végétariennes
    "Spaghetti sauce tomate végétarienne",
    "Lasagnes aux légumes",
    "Gratin de légumes béchamel",
    "Quiche aux poireaux salade",
    "Omelette aux champignons frites",
    "Boulettes végétariennes sauce tomate riz",
    "Curry de légumes pois chiches riz",
    "Croquettes de fromage salade",
    "Poêlée de légumes et pâtes complètes",
    "Chili sin carne riz",
    "Gratin dauphinois salade",
    "Risotto aux champignons",
]
