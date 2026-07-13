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


class Command(BaseCommand):
    help = "Crée des classes, enfants, parents et menus de démonstration."

    def handle(self, *args, **options):
        self.stdout.write("Création des données de démo…")

        # --- Classes -----------------------------------------------------
        noms_classes = ["1re primaire A", "3e primaire A", "5e primaire B"]
        classes = []
        for nom in noms_classes:
            classe, cree = Classe.objects.get_or_create(nom=nom)
            classes.append(classe)
            if cree:
                self.stdout.write(f"  + Classe : {classe.nom}")

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
        enfants_config = [
            ("Lucie", "Dupont", classes[0], parents[0]),
            ("Tom", "Dupont", classes[1], parents[0]),
            ("Emma", "Lemoine", classes[1], parents[1]),
            ("Noah", "Lemoine", classes[2], parents[1]),
            ("Léa", "Lemoine", classes[0], parents[1]),
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
            _, cree = Menu.objects.get_or_create(
                date=jour,
                defaults={
                    "plat_principal": plat,
                    "description": description,
                    "prix_cents": prix,
                    "ferme_a": ferme_a,
                },
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
