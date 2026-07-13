"""Signaux Django de l'app cantine.

On crée automatiquement un ProfilParent à chaque nouveau User. Ça
évite les états incohérents (User sans profil) sans avoir à s'en
soucier dans chaque vue d'inscription/admin.
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ProfilParent


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def creer_profil_parent(sender, instance, created, **kwargs):
    """Crée le ProfilParent associé au User dès qu'un User est créé."""
    if created:
        ProfilParent.objects.get_or_create(utilisateur=instance)
