"""Modèles de données de l'app cantine.

Convention monétaire : tous les montants sont stockés en centimes
d'euro dans un `IntegerField`. On évite ainsi les erreurs d'arrondi
propres aux `FloatField`. La conversion en euros se fait à
l'affichage.
"""

from django.conf import settings
from django.db import models


# Taux de conversion euro → franc belge, gelé au 1er janvier 1999.
# Sert uniquement à afficher un clin d'œil dans la navbar, pas à
# faire de la vraie compta.
TAUX_EURO_VERS_FRANC_BELGE = 40.3399


class ProfilParent(models.Model):
    """Extension du User Django pour un compte parent.

    On ne redéfinit pas un modèle User complet ; on l'étend via
    OneToOne. L'email + mot de passe standard de Django assurent
    l'authentification, on ajoute juste le téléphone et le solde.
    """

    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profil_parent",
        verbose_name="utilisateur",
    )
    telephone = models.CharField(
        "téléphone",
        max_length=20,
        blank=True,
    )
    solde_cents = models.IntegerField(
        "solde (centimes)",
        default=0,
        help_text="Solde du parent en centimes d'euro (crédité aux paiements validés).",
    )

    class Meta:
        verbose_name = "profil parent"
        verbose_name_plural = "profils parents"

    def __str__(self):
        prenom = self.utilisateur.first_name or self.utilisateur.username
        nom = self.utilisateur.last_name
        return f"{prenom} {nom}".strip()

    @property
    def solde_euros(self):
        """Solde formaté en euros (float à 2 décimales)."""
        return round(self.solde_cents / 100, 2)

    @property
    def solde_bef(self):
        """Solde converti en francs belges — clin d'œil purement décoratif."""
        return round((self.solde_cents / 100) * TAUX_EURO_VERS_FRANC_BELGE, 2)


class Classe(models.Model):
    """Une classe de l'école, ex. « 3e primaire A »."""

    nom = models.CharField("nom", max_length=50, unique=True)

    class Meta:
        verbose_name = "classe"
        verbose_name_plural = "classes"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Enfant(models.Model):
    """Un enfant scolarisé, rattaché à un parent et à une classe."""

    prenom = models.CharField("prénom", max_length=50)
    nom = models.CharField("nom", max_length=50)
    classe = models.ForeignKey(
        Classe,
        on_delete=models.PROTECT,
        related_name="enfants",
        verbose_name="classe",
    )
    parent = models.ForeignKey(
        ProfilParent,
        on_delete=models.CASCADE,
        related_name="enfants",
        verbose_name="parent",
    )
    allergies = models.TextField(
        "allergies / régime",
        blank=True,
        help_text="Renseigné librement par le parent.",
    )

    class Meta:
        verbose_name = "enfant"
        verbose_name_plural = "enfants"
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.classe})"


class Menu(models.Model):
    """Menu proposé un jour donné.

    Le champ `ferme_a` marque la date/heure limite au-delà de laquelle
    on ne peut plus réserver (la cuisine a besoin d'un chiffre stable
    pour commander).
    """

    date = models.DateField("date du repas", unique=True)
    plat_principal = models.CharField("plat principal", max_length=200)
    description = models.TextField("description / accompagnements", blank=True)
    prix_cents = models.IntegerField(
        "prix (centimes)",
        help_text="Prix du repas en centimes d'euro.",
    )
    ferme_a = models.DateTimeField(
        "clôture des réservations",
        help_text="Date et heure limites pour réserver ce menu.",
    )

    class Meta:
        verbose_name = "menu"
        verbose_name_plural = "menus"
        ordering = ["date"]

    def __str__(self):
        return f"{self.date:%d/%m/%Y} — {self.plat_principal}"

    @property
    def prix_euros(self):
        return round(self.prix_cents / 100, 2)


class Reservation(models.Model):
    """Réservation d'un menu pour un enfant.

    Le cycle de vie suit le flux métier :
      en_attente_paiement  → parent a cliqué "Réserver"
      confirmee            → paiement crédité, réservation payée
      presence_matin_ok    → l'enseignant a confirmé que l'enfant est là
      mangee               → la cuisinière a validé le service (décompte final)
      annulee              → annulation (par le parent ou l'admin)
    """

    STATUT_EN_ATTENTE = "en_attente_paiement"
    STATUT_CONFIRMEE = "confirmee"
    STATUT_PRESENCE_OK = "presence_matin_ok"
    STATUT_MANGEE = "mangee"
    STATUT_ANNULEE = "annulee"

    STATUT_CHOICES = [
        (STATUT_EN_ATTENTE, "En attente de paiement"),
        (STATUT_CONFIRMEE, "Confirmée"),
        (STATUT_PRESENCE_OK, "Présence matin confirmée"),
        (STATUT_MANGEE, "Mangée"),
        (STATUT_ANNULEE, "Annulée"),
    ]

    enfant = models.ForeignKey(
        Enfant,
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="enfant",
    )
    menu = models.ForeignKey(
        Menu,
        on_delete=models.PROTECT,
        related_name="reservations",
        verbose_name="menu",
    )
    statut = models.CharField(
        "statut",
        max_length=30,
        choices=STATUT_CHOICES,
        default=STATUT_EN_ATTENTE,
    )
    date_reservation = models.DateTimeField("date de réservation", auto_now_add=True)

    class Meta:
        verbose_name = "réservation"
        verbose_name_plural = "réservations"
        unique_together = ("enfant", "menu")
        ordering = ["-menu__date"]

    def __str__(self):
        return f"{self.enfant} — {self.menu} ({self.get_statut_display()})"


class Paiement(models.Model):
    """Virement déclaré par un parent (validé ensuite par la compta).

    Le parent déclare depuis son espace ; la compta valide via l'admin
    Django. La validation déclenche le crédit automatique du solde
    (cf. méthode `valider` ci-dessous et l'action admin dédiée).
    """

    STATUT_DECLARE = "declare"
    STATUT_VALIDE = "valide"
    STATUT_REJETE = "rejete"

    STATUT_CHOICES = [
        (STATUT_DECLARE, "Déclaré"),
        (STATUT_VALIDE, "Validé"),
        (STATUT_REJETE, "Rejeté"),
    ]

    parent = models.ForeignKey(
        ProfilParent,
        on_delete=models.CASCADE,
        related_name="paiements",
        verbose_name="parent",
    )
    montant_cents = models.IntegerField(
        "montant (centimes)",
        help_text="Montant du virement déclaré, en centimes d'euro.",
    )
    reference_virement = models.CharField(
        "référence du virement",
        max_length=100,
        help_text="Communication libre ou structurée indiquée sur le virement.",
    )
    date_declaration = models.DateTimeField("date de déclaration", auto_now_add=True)
    date_validation = models.DateTimeField(
        "date de validation", null=True, blank=True
    )
    statut = models.CharField(
        "statut",
        max_length=20,
        choices=STATUT_CHOICES,
        default=STATUT_DECLARE,
    )
    commentaire_compta = models.TextField("commentaire compta", blank=True)

    class Meta:
        verbose_name = "paiement"
        verbose_name_plural = "paiements"
        ordering = ["-date_declaration"]

    def __str__(self):
        return f"{self.parent} — {self.montant_euros} € ({self.get_statut_display()})"

    @property
    def montant_euros(self):
        return round(self.montant_cents / 100, 2)

    def valider(self, commentaire: str = ""):
        """Passe le paiement à `valide` et crédite le solde du parent.

        Idempotent : appeler cette méthode sur un paiement déjà validé
        ne re-crédite pas le solde (protection contre les doubles
        clics dans l'admin).
        """
        from django.utils import timezone

        if self.statut == self.STATUT_VALIDE:
            return False

        self.statut = self.STATUT_VALIDE
        self.date_validation = timezone.now()
        if commentaire:
            self.commentaire_compta = commentaire
        self.save(update_fields=["statut", "date_validation", "commentaire_compta"])

        # Crédit atomique du solde (F expression pour éviter les
        # race conditions si plusieurs validations en parallèle).
        ProfilParent.objects.filter(pk=self.parent_id).update(
            solde_cents=models.F("solde_cents") + self.montant_cents
        )
        return True
