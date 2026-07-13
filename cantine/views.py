"""Vues de l'app cantine (espace parents + espace cuisine).

Les vues parents sont protégées par @login_required, les vues cuisine
par @cuisine_required (appartenance au groupe Django « Cuisine »).
La racine `/` redirige selon l'état d'authentification.
"""

from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decorators import cuisine_required
from .forms import DeclarationVirementForm, InscriptionParentForm
from .models import Enfant, Menu, Paiement, Reservation


# Statuts « à préparer/servir » : tout ce qui n'est ni annulé ni en
# attente de paiement. Utilisé pour compter les repas côté cuisine.
STATUTS_A_PREPARER = [
    Reservation.STATUT_CONFIRMEE,
    Reservation.STATUT_PRESENCE_OK,
    Reservation.STATUT_MANGEE,
]


def racine(request):
    """Aiguillage : accueil si connecté, page de connexion sinon."""
    if request.user.is_authenticated:
        return redirect("cantine:accueil")
    return redirect("cantine:connexion")


def inscription(request):
    """Création d'un compte parent (ProfilParent créé par signal)."""
    if request.user.is_authenticated:
        return redirect("cantine:accueil")

    if request.method == "POST":
        form = InscriptionParentForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                "Bienvenue ! Ton compte est créé, ajoute tes enfants "
                "via l'école ou l'administration.",
            )
            return redirect("cantine:accueil")
    else:
        form = InscriptionParentForm()

    return render(request, "cantine/inscription.html", {"form": form})


@login_required
def accueil(request):
    """Tableau de bord parent : solde, enfants, prochaines réservations."""
    profil = request.user.profil_parent
    enfants = profil.enfants.select_related("classe").all()

    aujourd_hui = timezone.now().date()
    prochaines_reservations = (
        Reservation.objects.filter(
            enfant__parent=profil,
            menu__date__gte=aujourd_hui,
        )
        .select_related("enfant", "menu")
        .order_by("menu__date")[:10]
    )

    return render(
        request,
        "cantine/accueil.html",
        {
            "profil": profil,
            "enfants": enfants,
            "prochaines_reservations": prochaines_reservations,
        },
    )


@login_required
def calendrier(request):
    """Menus des 30 prochains jours avec bouton « Réserver » par enfant."""
    profil = request.user.profil_parent
    enfants = list(profil.enfants.select_related("classe"))

    aujourd_hui = timezone.now().date()
    limite = aujourd_hui + timedelta(days=30)
    menus = Menu.objects.filter(
        date__gte=aujourd_hui, date__lte=limite
    ).order_by("date")

    # Pré-charge les réservations existantes du parent sur cette
    # période pour éviter N+1 requêtes dans le template.
    reservations_existantes = Reservation.objects.filter(
        enfant__parent=profil,
        menu__in=menus,
    ).select_related("enfant", "menu")
    index_resa = {
        (r.enfant_id, r.menu_id): r for r in reservations_existantes
    }

    maintenant = timezone.now()

    # Assemble une structure prête à parcourir dans le template :
    # pour chaque menu, la liste (enfant, reservation_ou_none).
    lignes = []
    for menu in menus:
        etats_enfants = []
        for enfant in enfants:
            resa = index_resa.get((enfant.id, menu.id))
            etats_enfants.append({"enfant": enfant, "reservation": resa})
        lignes.append(
            {
                "menu": menu,
                "cloture_passee": menu.ferme_a <= maintenant,
                "etats_enfants": etats_enfants,
            }
        )

    return render(
        request,
        "cantine/calendrier.html",
        {
            "lignes": lignes,
            "enfants": enfants,
        },
    )


@login_required
@require_POST
def reserver_menu(request):
    """Crée une réservation en_attente_paiement pour (enfant, menu)."""
    profil = request.user.profil_parent
    enfant_id = request.POST.get("enfant_id")
    menu_id = request.POST.get("menu_id")

    enfant = get_object_or_404(Enfant, pk=enfant_id, parent=profil)
    menu = get_object_or_404(Menu, pk=menu_id)

    if menu.ferme_a <= timezone.now():
        messages.error(
            request, "Trop tard : les réservations pour ce menu sont closes."
        )
        return HttpResponseRedirect(reverse("cantine:calendrier"))

    _, cree = Reservation.objects.get_or_create(
        enfant=enfant,
        menu=menu,
        defaults={"statut": Reservation.STATUT_EN_ATTENTE},
    )
    if cree:
        messages.success(
            request,
            f"Réservation enregistrée pour {enfant.prenom} le "
            f"{menu.date:%d/%m/%Y}. Elle sera confirmée dès validation "
            "du paiement.",
        )
    else:
        messages.info(
            request,
            f"Une réservation existait déjà pour {enfant.prenom} le "
            f"{menu.date:%d/%m/%Y}.",
        )
    return HttpResponseRedirect(reverse("cantine:calendrier"))


@login_required
def historique(request):
    """Historique : réservations passées + paiements déclarés/validés."""
    profil = request.user.profil_parent
    aujourd_hui = timezone.now().date()

    reservations_passees = (
        Reservation.objects.filter(
            enfant__parent=profil,
            menu__date__lt=aujourd_hui,
        )
        .select_related("enfant", "menu")
        .order_by("-menu__date")
    )
    paiements = profil.paiements.all().order_by("-date_declaration")

    return render(
        request,
        "cantine/historique.html",
        {
            "reservations_passees": reservations_passees,
            "paiements": paiements,
        },
    )


@login_required
def declarer_virement(request):
    """Formulaire de déclaration d'un virement (statut = declare)."""
    profil = request.user.profil_parent

    if request.method == "POST":
        form = DeclarationVirementForm(request.POST)
        if form.is_valid():
            Paiement.objects.create(
                parent=profil,
                montant_cents=form.montant_cents(),
                reference_virement=form.cleaned_data["reference_virement"],
            )
            messages.success(
                request,
                "Virement déclaré. La comptabilité le validera dès réception.",
            )
            return redirect("cantine:historique")
    else:
        form = DeclarationVirementForm()

    return render(
        request,
        "cantine/declarer_virement.html",
        {"form": form},
    )


# ---------------------------------------------------------------------
# Espace cuisinière
# ---------------------------------------------------------------------


def _parse_date_iso(chaine):
    """Parse une date ISO AAAA-MM-JJ, lève Http404 sinon."""
    try:
        return datetime.strptime(chaine, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise Http404("Date invalide (format attendu : AAAA-MM-JJ).")


@cuisine_required
def cuisine_calendrier(request):
    """Liste des 30 prochains jours pour anticiper les commandes.

    Affiche, pour chaque jour ayant un menu, le plat principal et le
    nombre de repas réservés/confirmés (statuts « à préparer »).
    """
    aujourd_hui = timezone.now().date()
    limite = aujourd_hui + timedelta(days=30)

    menus = (
        Menu.objects.filter(date__gte=aujourd_hui, date__lte=limite)
        .annotate(
            nb_repas=Count(
                "reservations",
                filter=Q(reservations__statut__in=STATUTS_A_PREPARER),
            )
        )
        .order_by("date", "plat_principal")
    )

    # Regroupement par date : plusieurs menus peuvent exister le même
    # jour (rare, mais le modèle Menu a `unique=True` sur date donc en
    # pratique c'est un menu par jour ; on regroupe quand même pour
    # rester tolérant à un futur assouplissement).
    jours = {}
    for menu in menus:
        entree = jours.setdefault(
            menu.date,
            {"date": menu.date, "menus": [], "total": 0},
        )
        entree["menus"].append(menu)
        entree["total"] += menu.nb_repas
    jours_ordonnes = sorted(jours.values(), key=lambda j: j["date"])

    return render(
        request,
        "cantine/cuisine_calendrier.html",
        {
            "jours": jours_ordonnes,
            "aujourd_hui": aujourd_hui,
        },
    )


@cuisine_required
def cuisine_jour(request, date):
    """Détail d'un jour : réservations, allergies, actions « A mangé »."""
    jour = _parse_date_iso(date)

    menus = list(
        Menu.objects.filter(date=jour).order_by("plat_principal")
    )
    if not menus:
        return render(
            request,
            "cantine/cuisine_jour.html",
            {"jour": jour, "aucun_menu": True, "menus_detail": []},
        )

    # Une entrée par menu : réservations à préparer regroupées par
    # texte d'allergies (les enfants sans allergie sont dans le
    # groupe "" — affiché "Aucune allergie" dans le template).
    menus_detail = []
    total_prevus = 0
    total_manges = 0
    for menu in menus:
        reservations = list(
            Reservation.objects.filter(
                menu=menu,
                statut__in=STATUTS_A_PREPARER,
            )
            .select_related("enfant", "enfant__classe")
            .order_by("enfant__nom", "enfant__prenom")
        )
        groupes = {}
        for resa in reservations:
            cle = (resa.enfant.allergies or "").strip()
            groupes.setdefault(cle, []).append(resa)
        # Trie : "sans allergie" d'abord, puis par texte d'allergie.
        groupes_ordonnes = sorted(
            groupes.items(), key=lambda kv: (kv[0] != "", kv[0].lower())
        )
        nb_manges = sum(
            1 for r in reservations if r.statut == Reservation.STATUT_MANGEE
        )
        menus_detail.append({
            "menu": menu,
            "groupes": groupes_ordonnes,
            "nb_reservations": len(reservations),
            "nb_manges": nb_manges,
        })
        total_prevus += len(reservations)
        total_manges += nb_manges

    return render(
        request,
        "cantine/cuisine_jour.html",
        {
            "jour": jour,
            "aucun_menu": False,
            "menus_detail": menus_detail,
            "total_prevus": total_prevus,
            "total_manges": total_manges,
        },
    )


@cuisine_required
def cuisine_aujourdhui(request):
    """Redirige vers /cuisine/jour/<date_du_jour>/."""
    aujourd_hui = timezone.now().date()
    return redirect(
        "cantine:cuisine_jour", date=aujourd_hui.isoformat()
    )


@cuisine_required
@require_POST
def cuisine_marquer_mangee(request, reservation_id):
    """Marque une réservation comme mangée puis revient au jour."""
    resa = get_object_or_404(
        Reservation.objects.select_related("enfant", "menu"),
        pk=reservation_id,
    )
    if resa.statut in (
        Reservation.STATUT_EN_ATTENTE,
        Reservation.STATUT_ANNULEE,
    ):
        messages.error(
            request,
            f"Impossible de marquer {resa.enfant.prenom} comme ayant "
            f"mangé : réservation au statut « {resa.get_statut_display()} ».",
        )
    else:
        change = resa.marquer_mangee()
        if change:
            messages.success(
                request,
                f"{resa.enfant.prenom} {resa.enfant.nom} : repas décompté.",
            )
        else:
            messages.info(
                request,
                f"{resa.enfant.prenom} {resa.enfant.nom} avait déjà "
                "été marqué : aucun décompte supplémentaire.",
            )
    return redirect(
        "cantine:cuisine_jour", date=resa.menu.date.isoformat()
    )
