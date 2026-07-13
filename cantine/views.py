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

from .decorators import comptabilite_required, cuisine_required
from .forms import DeclarationVirementForm, InscriptionParentForm, MenuForm
from .generateur_menus import generer_suggestions
from .models import Classe, Enfant, Menu, Paiement, Reservation


# Nombre de suggestions générées par pool (mixte / végétarien) et
# proposées au formulaire de création de menu. Le pool est volontairement
# plus large que les 6 boutons affichés pour que « Autres idées » offre
# du renouvellement sans rechargement de page.
NB_SUGGESTIONS_POOL = 30


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
    menus_par_date = {}
    for menu in menus:
        entree = menus_par_date.setdefault(
            menu.date,
            {"date": menu.date, "menus": [], "total": 0},
        )
        entree["menus"].append(menu)
        entree["total"] += menu.nb_repas

    # On rend chaque jour de la période (même sans menu) afin que la
    # cuisinière puisse créer directement le menu manquant du jour.
    jours_ordonnes = []
    for offset in range(31):
        jour = aujourd_hui + timedelta(days=offset)
        jours_ordonnes.append(
            menus_par_date.get(
                jour,
                {"date": jour, "menus": [], "total": 0},
            )
        )

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
def cuisine_menus(request):
    """Liste les menus à venir pour la cuisinière (édition/suppression)."""
    aujourd_hui = timezone.now().date()
    menus = (
        Menu.objects.filter(date__gte=aujourd_hui)
        .annotate(nb_reservations=Count("reservations"))
        .order_by("date")
    )
    return render(
        request,
        "cantine/cuisine_menus.html",
        {"menus": menus, "aujourd_hui": aujourd_hui},
    )


def _plats_recents():
    """Plats servis ces 14 derniers jours (noms normalisés).

    Sert à écarter des suggestions toute combinaison déjà utilisée comme
    `plat_principal` d'un `Menu` récent, sans tenir compte de la casse ni
    des espaces de bord.
    """
    aujourd_hui = timezone.now().date()
    depuis = aujourd_hui - timedelta(days=14)
    return {
        (plat or "").strip().casefold()
        for plat in Menu.objects.filter(
            date__gte=depuis, date__lte=aujourd_hui
        ).values_list("plat_principal", flat=True)
    }


def suggestions_menus():
    """Deux pools de suggestions pour le formulaire de création.

    Le générateur combinatoire (`cantine.generateur_menus`) compose des
    plats équilibrés à la volée (plusieurs milliers de combinaisons
    possibles), en écartant les plats servis ces 14 derniers jours.
    On renvoie deux listes : l'une mixte, l'autre végétarienne, pour que
    le filtre « végétariennes uniquement » du formulaire bascule d'un
    pool à l'autre côté client, sans rechargement ni appel réseau.
    """
    recents = _plats_recents()
    return {
        "mixte": generer_suggestions(
            NB_SUGGESTIONS_POOL, exclure_recents=recents
        ),
        "vegetarien": generer_suggestions(
            NB_SUGGESTIONS_POOL,
            vegetarien_uniquement=True,
            exclure_recents=recents,
        ),
    }


@cuisine_required
def cuisine_menu_creer(request):
    """Formulaire de création d'un menu.

    Accepte un paramètre GET `date` (AAAA-MM-JJ) pour pré-remplir la
    date depuis le calendrier cuisine.
    """
    initial = {}
    date_param = request.GET.get("date")
    if date_param:
        try:
            initial["date"] = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            pass

    if request.method == "POST":
        form = MenuForm(request.POST)
        if form.is_valid():
            menu = form.save()
            messages.success(
                request,
                f"Menu du {menu.date:%d/%m/%Y} créé : {menu.plat_principal}.",
            )
            return redirect("cantine:cuisine_menus")
    else:
        form = MenuForm(initial=initial)

    pools = suggestions_menus()
    return render(
        request,
        "cantine/cuisine_menu_form.html",
        {
            "form": form,
            "menu": None,
            "idees_menus": pools["mixte"],
            "idees_menus_vego": pools["vegetarien"],
        },
    )


@cuisine_required
def cuisine_menu_modifier(request, pk):
    """Formulaire d'édition d'un menu existant."""
    menu = get_object_or_404(Menu, pk=pk)

    if request.method == "POST":
        form = MenuForm(request.POST, instance=menu)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Menu du {menu.date:%d/%m/%Y} mis à jour.",
            )
            return redirect("cantine:cuisine_menus")
    else:
        form = MenuForm(instance=menu)

    return render(
        request,
        "cantine/cuisine_menu_form.html",
        {"form": form, "menu": menu},
    )


@cuisine_required
@require_POST
def cuisine_menu_supprimer(request, pk):
    """Supprime un menu s'il n'a aucune réservation liée."""
    menu = get_object_or_404(Menu, pk=pk)
    nb_reservations = menu.reservations.count()
    if nb_reservations:
        messages.error(
            request,
            f"Impossible de supprimer le menu du {menu.date:%d/%m/%Y} : "
            f"{nb_reservations} réservation"
            f"{'s' if nb_reservations > 1 else ''} y "
            f"{'sont' if nb_reservations > 1 else 'est'} rattachée"
            f"{'s' if nb_reservations > 1 else ''}. "
            "Annulez d'abord ces réservations dans l'admin.",
        )
        return redirect("cantine:cuisine_menus")

    date_menu = menu.date
    menu.delete()
    messages.success(
        request,
        f"Menu du {date_menu:%d/%m/%Y} supprimé.",
    )
    return redirect("cantine:cuisine_menus")


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


# ---------------------------------------------------------------------
# Espace comptabilité
# ---------------------------------------------------------------------


# Statuts de paiement autorisés dans le filtre GET de la liste des
# paiements. Toute autre valeur retombe sur « déclarés » par défaut.
FILTRES_PAIEMENT = {
    Paiement.STATUT_DECLARE: "Déclarés",
    Paiement.STATUT_VALIDE: "Validés",
    Paiement.STATUT_REJETE: "Rejetés",
    "tous": "Tous",
}

# Prix de repas de secours (centimes) si aucun menu n'existe encore en
# base : sert de référence au badge « solde faible » du suivi enfants.
PRIX_REPAS_DEFAUT_CENTS = 600

# Fenêtre par défaut (en jours) du suivi croisé repas/paiements.
SUIVI_PERIODE_JOURS_DEFAUT = 30


@comptabilite_required
def comptabilite_paiements(request):
    """Liste des paiements avec filtre par statut (déclarés par défaut).

    Les paiements au statut « déclaré » exposent les actions Valider /
    Rejeter (POST). Le filtre se pilote via `?statut=` (declare, valide,
    rejete ou tous).
    """
    statut = request.GET.get("statut", Paiement.STATUT_DECLARE)
    if statut not in FILTRES_PAIEMENT:
        statut = Paiement.STATUT_DECLARE

    paiements = Paiement.objects.select_related(
        "parent", "parent__utilisateur"
    )
    if statut != "tous":
        paiements = paiements.filter(statut=statut)
    paiements = paiements.order_by("-date_declaration")

    return render(
        request,
        "cantine/comptabilite_paiements.html",
        {
            "paiements": paiements,
            "statut_actif": statut,
            "filtres": FILTRES_PAIEMENT,
        },
    )


@comptabilite_required
@require_POST
def comptabilite_paiement_valider(request, pk):
    """Valide un paiement déclaré (crédite le solde) puis revient à la liste."""
    paiement = get_object_or_404(
        Paiement.objects.select_related("parent", "parent__utilisateur"),
        pk=pk,
    )
    change = paiement.valider()
    if change:
        messages.success(
            request,
            f"Paiement de {paiement.parent} "
            f"({paiement.montant_euros:.2f} €) validé : solde crédité.",
        )
    else:
        messages.info(
            request,
            f"Le paiement de {paiement.parent} était déjà validé : "
            "aucun crédit supplémentaire.",
        )
    return redirect(_retour_paiements(request))


@comptabilite_required
@require_POST
def comptabilite_paiement_rejeter(request, pk):
    """Rejette un paiement déclaré (sans créditer) puis revient à la liste."""
    paiement = get_object_or_404(
        Paiement.objects.select_related("parent", "parent__utilisateur"),
        pk=pk,
    )
    commentaire = (request.POST.get("commentaire_compta") or "").strip()
    change = paiement.rejeter(commentaire=commentaire)
    if change:
        messages.success(
            request,
            f"Paiement de {paiement.parent} "
            f"({paiement.montant_euros:.2f} €) rejeté.",
        )
    else:
        messages.warning(
            request,
            f"Le paiement de {paiement.parent} ne peut plus être rejeté "
            f"(statut actuel : « {paiement.get_statut_display()} »).",
        )
    return redirect(_retour_paiements(request))


def _retour_paiements(request):
    """URL de retour vers la liste des paiements en conservant le filtre."""
    statut = request.POST.get("statut")
    url = reverse("cantine:comptabilite_paiements")
    if statut in FILTRES_PAIEMENT:
        url = f"{url}?statut={statut}"
    return url


@comptabilite_required
def comptabilite_suivi_enfants(request):
    """Suivi croisé repas/paiements par enfant sur une période récente.

    Pour chaque enfant (filtrable par classe via `?classe=`), on compte
    sur les N derniers jours les repas réservés (hors annulés) et
    effectivement mangés, et on affiche le solde du parent avec un
    indicateur d'alerte quand ce solde est bas.
    """
    aujourd_hui = timezone.now().date()
    depuis = aujourd_hui - timedelta(days=SUIVI_PERIODE_JOURS_DEFAUT)

    # Filtre optionnel par classe (paramètre GET numérique).
    classe_id = request.GET.get("classe")
    classe_active = None
    if classe_id:
        classe_active = Classe.objects.filter(pk=classe_id).first()

    # Repas de la période : bornés par la date du menu (menu__date).
    dans_periode = Q(
        reservations__menu__date__gte=depuis,
        reservations__menu__date__lte=aujourd_hui,
    )
    enfants = (
        Enfant.objects.select_related(
            "classe", "parent", "parent__utilisateur"
        )
        .annotate(
            nb_reserves=Count(
                "reservations",
                filter=dans_periode
                & ~Q(reservations__statut=Reservation.STATUT_ANNULEE),
            ),
            nb_manges=Count(
                "reservations",
                filter=dans_periode
                & Q(reservations__statut=Reservation.STATUT_MANGEE),
            ),
        )
        .order_by("classe__nom", "nom", "prenom")
    )
    if classe_active is not None:
        enfants = enfants.filter(classe=classe_active)

    # Prix de repas de référence pour le seuil « solde faible » : celui
    # du menu le plus récent, à défaut une valeur de secours.
    dernier_menu = Menu.objects.order_by("-date").first()
    prix_repas_cents = (
        dernier_menu.prix_cents if dernier_menu else PRIX_REPAS_DEFAUT_CENTS
    )

    lignes = []
    for enfant in enfants:
        solde = enfant.parent.solde_cents
        # Alerte : rouge si solde négatif ; orange si solde faible (entre
        # 0 et le prix d'un repas) alors que des repas ont été mangés.
        if solde < 0:
            alerte = "rouge"
        elif 0 <= solde <= prix_repas_cents and enfant.nb_manges > 0:
            alerte = "orange"
        else:
            alerte = None
        lignes.append(
            {
                "enfant": enfant,
                "solde_euros": round(solde / 100, 2),
                "nb_reserves": enfant.nb_reserves,
                "nb_manges": enfant.nb_manges,
                "alerte": alerte,
            }
        )

    return render(
        request,
        "cantine/comptabilite_suivi_enfants.html",
        {
            "lignes": lignes,
            "classes": Classe.objects.all(),
            "classe_active": classe_active,
            "periode_jours": SUIVI_PERIODE_JOURS_DEFAUT,
            "depuis": depuis,
        },
    )
