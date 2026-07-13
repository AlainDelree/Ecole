"""Peuple la base avec des données de démo pour tester rapidement.

Idempotent : re-lancer la commande ne duplique pas les objets déjà
présents (utilise `get_or_create` ou vérifie l'existence sur date).
"""

from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from cantine.models import Classe, Enfant, Menu

NOM_GROUPE_CUISINE = "Cuisine"
NOM_GROUPE_COMPTABILITE = "Comptabilite"


# Prix de référence : chaque tuple donne le prix primaire (repas
# complet, en centimes) ; les prix maternelle / adulte / potage sont
# dérivés par _prix_menu_demo pour rester cohérents entre menus.
PLATS_DEMO = [
    ("Spaghetti bolognaise", "Salade verte, parmesan", 550),
    ("Poulet rôti, purée", "Petits pois, jus", 600),
    ("Poisson pané, riz", "Sauce tartare, brocolis", 580),
    ("Vol-au-vent", "Frites maison, salade", 650),
    ("Lasagnes", "Salade mêlée", 570),
    ("Boulettes sauce tomate", "Purée de pommes de terre", 540),
    ("Quiche aux légumes", "Salade verte", 500),
    ("Curry de légumes", "Riz basmati (végé)", 520),
    ("Cabillaud au four", "Pommes de terre vapeur, épinards", 620),
    ("Chili con carne", "Riz, crème sure", 580),
]


def _prix_menu_demo(prix_primaire_cents):
    """Dérive les 4 prix d'un menu à partir du prix primaire.

    - Maternelle : -50 centimes (moins cher, portions plus petites).
    - Adulte : +50 % (personnel/enseignants).
    - Potage seul : moitié du prix primaire.
    """
    return {
        "prix_maternelle_cents": max(0, prix_primaire_cents - 50),
        "prix_primaire_cents": prix_primaire_cents,
        "prix_adulte_cents": round(prix_primaire_cents * 1.5),
        "prix_potage_cents": round(prix_primaire_cents / 2),
    }


class Command(BaseCommand):
    help = "Crée des classes, enfants, parents et menus de démonstration."

    def handle(self, *args, **options):
        self.stdout.write("Création des données de démo…")

        # --- Classes -----------------------------------------------------
        # Mix cohérent maternelle / primaire pour tester les tarifs
        # différenciés (au moins une classe de chaque niveau).
        classes_config = [
            ("Maternelle A", Classe.NIVEAU_MATERNELLE),
            ("1re primaire A", Classe.NIVEAU_PRIMAIRE),
            ("3e primaire A", Classe.NIVEAU_PRIMAIRE),
            ("5e primaire B", Classe.NIVEAU_PRIMAIRE),
        ]
        classes = []
        for nom, niveau in classes_config:
            classe, cree = Classe.objects.get_or_create(
                nom=nom,
                defaults={"niveau": niveau},
            )
            # Rétro-compat : si la classe existait avant l'ajout du champ
            # niveau, on la met à jour ici.
            if classe.niveau != niveau:
                classe.niveau = niveau
                classe.save(update_fields=["niveau"])
            classes.append(classe)
            if cree:
                self.stdout.write(f"  + Classe : {classe.nom} ({niveau})")

        # --- Parents (Users + ProfilParents créés via signal) ------------
        parents_config = [
            {
                "username": "parent.dupont@example.be",
                "email": "parent.dupont@example.be",
                "first_name": "Marie",
                "last_name": "Dupont",
                "telephone": "+32 471 11 22 33",
                "password": "demo1234",
            },
            {
                "username": "parent.lemoine@example.be",
                "email": "parent.lemoine@example.be",
                "first_name": "Julien",
                "last_name": "Lemoine",
                "telephone": "+32 472 44 55 66",
                "password": "demo1234",
            },
        ]
        parents = []
        for cfg in parents_config:
            user, cree = User.objects.get_or_create(
                username=cfg["username"],
                defaults={
                    "email": cfg["email"],
                    "first_name": cfg["first_name"],
                    "last_name": cfg["last_name"],
                },
            )
            if cree:
                user.set_password(cfg["password"])
                user.save()
                self.stdout.write(
                    f"  + Parent : {cfg['email']} (mdp = {cfg['password']})"
                )
            profil = user.profil_parent
            profil.telephone = cfg["telephone"]
            profil.save(update_fields=["telephone"])
            parents.append(profil)

        # --- Enfants -----------------------------------------------------
        # classes[0] = maternelle, classes[1..3] = primaire.
        # On garde au moins un enfant en maternelle et plusieurs en
        # primaire pour tester les prix différenciés en démo.
        enfants_config = [
            ("Lucie", "Dupont", classes[0], parents[0]),   # maternelle
            ("Tom", "Dupont", classes[2], parents[0]),     # primaire
            ("Emma", "Lemoine", classes[2], parents[1]),   # primaire
            ("Noah", "Lemoine", classes[3], parents[1]),   # primaire
            ("Léa", "Lemoine", classes[1], parents[1]),    # primaire
        ]
        for prenom, nom, classe, parent in enfants_config:
            _, cree = Enfant.objects.get_or_create(
                prenom=prenom,
                nom=nom,
                parent=parent,
                defaults={"classe": classe},
            )
            if cree:
                self.stdout.write(f"  + Enfant : {prenom} {nom} ({classe.nom})")

        # --- Menus (20 sur les 30 prochains jours ouvrables) -------------
        tz = timezone.get_current_timezone()
        aujourd_hui = date.today()
        crees = 0
        jour = aujourd_hui
        while crees < 20 and jour < aujourd_hui + timedelta(days=45):
            jour += timedelta(days=1)
            # On saute les week-ends (école fermée).
            if jour.weekday() >= 5:
                continue
            plat, description, prix = PLATS_DEMO[crees % len(PLATS_DEMO)]
            # Clôture des réservations à 9h le matin même.
            ferme_a = timezone.make_aware(datetime.combine(jour, time(9, 0)), tz)
            defaults = {
                "plat_principal": plat,
                "description": description,
                "ferme_a": ferme_a,
                **_prix_menu_demo(prix),
            }
            _, cree = Menu.objects.get_or_create(
                date=jour,
                defaults=defaults,
            )
            if cree:
                crees += 1

        # --- Groupe et utilisateur de démo « Cuisine » ------------------
        groupe_cuisine, _ = Group.objects.get_or_create(name=NOM_GROUPE_CUISINE)
        cuisine_user, cree = User.objects.get_or_create(
            username="cuisine",
            defaults={
                "first_name": "Cuisine",
                "last_name": "Démo",
                "email": "",
            },
        )
        if cree:
            cuisine_user.set_password("cuisine1234")
            cuisine_user.save()
            self.stdout.write("  + Utilisateur : cuisine (mdp = cuisine1234)")
        cuisine_user.groups.add(groupe_cuisine)

        # --- Groupe et utilisateur de démo « Comptabilite » -------------
        # Appartenance au groupe uniquement : pas de statut staff, la
        # compta passe désormais par l'interface dédiée, plus par l'admin.
        groupe_compta, _ = Group.objects.get_or_create(
            name=NOM_GROUPE_COMPTABILITE
        )
        compta_user, cree = User.objects.get_or_create(
            username="compta",
            defaults={
                "first_name": "Compta",
                "last_name": "Démo",
                "email": "",
            },
        )
        if cree:
            compta_user.set_password("compta1234")
            compta_user.save()
            self.stdout.write("  + Utilisateur : compta (mdp = compta1234)")
        compta_user.groups.add(groupe_compta)

        self.stdout.write(self.style.SUCCESS(
            f"Données de démo prêtes : {len(classes)} classes, "
            f"{len(parents)} parents, {len(enfants_config)} enfants, "
            f"{Menu.objects.count()} menus au total."
        ))
        self.stdout.write(
            "Comptes parents : parent.dupont@example.be / parent.lemoine@example.be "
            "— mot de passe : demo1234"
        )
        self.stdout.write(
            "Compte cuisine : cuisine — mot de passe : cuisine1234"
        )
        self.stdout.write(
            "Compte compta : compta — mot de passe : compta1234"
        )
