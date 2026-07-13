from django.apps import AppConfig


class CantineConfig(AppConfig):
    """Configuration de l'app cantine.

    Le nom `cantine` couvre tout le domaine repas scolaire : parents,
    enfants, menus, réservations, paiements.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "cantine"
    verbose_name = "Cantine scolaire"

    def ready(self):
        # Import des signaux (création automatique du ProfilParent
        # à la création d'un User).
        from . import signals  # noqa: F401
