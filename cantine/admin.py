"""Configuration de l'admin Django pour l'app cantine.

L'admin sert d'interface unique aux rôles non-parents pour ce premier
jet : la compta y valide les paiements, la cuisine y consulte les
réservations, les enseignants et la cuisinière pourront y saisir la
présence matin et la validation post-repas (via l'édition d'une
Reservation) en attendant leurs interfaces dédiées.
"""

from django.contrib import admin, messages

from .models import (
    Classe,
    Enfant,
    Menu,
    Paiement,
    ProfilParent,
    Reservation,
)


@admin.register(ProfilParent)
class ProfilParentAdmin(admin.ModelAdmin):
    list_display = ("__str__", "utilisateur", "telephone", "solde_euros")
    search_fields = (
        "utilisateur__username",
        "utilisateur__email",
        "utilisateur__first_name",
        "utilisateur__last_name",
        "telephone",
    )
    readonly_fields = ("solde_euros", "solde_bef")

    @admin.display(description="solde (€)")
    def solde_euros(self, obj):
        return f"{obj.solde_euros:.2f} €"


@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ("nom",)
    search_fields = ("nom",)


@admin.register(Enfant)
class EnfantAdmin(admin.ModelAdmin):
    list_display = ("prenom", "nom", "classe", "parent")
    list_filter = ("classe",)
    search_fields = (
        "prenom",
        "nom",
        "parent__utilisateur__username",
        "parent__utilisateur__last_name",
    )
    autocomplete_fields = ("parent", "classe")


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("date", "plat_principal", "prix_euros", "ferme_a")
    list_filter = ("date",)
    search_fields = ("plat_principal", "description")
    date_hierarchy = "date"

    @admin.display(description="prix (€)")
    def prix_euros(self, obj):
        return f"{obj.prix_euros:.2f} €"


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("enfant", "menu", "statut", "date_reservation")
    list_filter = ("statut", "menu__date", "enfant__classe")
    search_fields = (
        "enfant__prenom",
        "enfant__nom",
        "menu__plat_principal",
    )
    autocomplete_fields = ("enfant", "menu")
    date_hierarchy = "date_reservation"


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = (
        "parent",
        "montant_euros_affiche",
        "reference_virement",
        "statut",
        "date_declaration",
        "date_validation",
    )
    list_filter = ("statut", "date_declaration")
    search_fields = (
        "parent__utilisateur__username",
        "parent__utilisateur__last_name",
        "reference_virement",
    )
    autocomplete_fields = ("parent",)
    date_hierarchy = "date_declaration"
    actions = ("valider_paiements",)

    @admin.display(description="montant (€)")
    def montant_euros_affiche(self, obj):
        return f"{obj.montant_euros:.2f} €"

    @admin.action(description="Valider les paiements sélectionnés (crédite le solde)")
    def valider_paiements(self, request, queryset):
        """Action compta : valide un lot de paiements et crédite les soldes."""
        valides = 0
        ignores = 0
        for paiement in queryset:
            if paiement.valider():
                valides += 1
            else:
                ignores += 1

        if valides:
            self.message_user(
                request,
                f"{valides} paiement(s) validé(s) et solde(s) crédité(s).",
                level=messages.SUCCESS,
            )
        if ignores:
            self.message_user(
                request,
                f"{ignores} paiement(s) déjà validé(s), ignoré(s).",
                level=messages.WARNING,
            )
