# École — gestion des repas scolaires

Application Django pour gérer les réservations de repas d'une école
(≈ 50 à 200 élèves). Premier jet : **site parents uniquement**.
Les autres rôles (comptabilité, cuisine, enseignants) passent par
l'admin Django pour l'instant.

## Flux global

1. **Parents** — composent un **panier** de réservations (jusqu'à 30
   jours à l'avance), puis règlent le panier en une opération via un
   **simulateur de paiement** (voir plus bas). Les réservations
   passent immédiatement en statut « confirmée ».
2. **Cuisine** — consulte les réservations confirmées et prépare les
   commandes.
3. **Enseignants** — confirmeront la présence de l'enfant le matin
   (interface dédiée à venir).
4. **Cuisinière** — valide le service post-repas (statut final
   « mangée »).
5. **Comptabilité** — suit les réservations et l'historique via
   l'admin Django et la vue de suivi enfants.

### Paiement : simulateur en attendant Mollie

L'intégration Mollie (SEPA, Bancontact, carte bancaire) n'est **pas
encore branchée**. Le portail utilise pour l'instant un simulateur de
paiement qui affiche le total à payer et confirme les réservations en
un clic, sans encaissement réel. Un commentaire `# TODO Mollie` dans
`cantine/views.py` marque le point où l'appel à l'API Mollie prendra
place. Le rapprochement bancaire (paiements Mollie ↔ compte réel de
l'école) sera à traiter lors de cette intégration future.

L'ancien flux « virement déclaré + validation compta + solde crédité »
a été retiré de l'interface, mais le modèle `Paiement` et le champ
`solde_cents` sont conservés en base — aucune donnée existante n'a
été supprimée.

## Pile technique

- Python 3.12+ / Django 5
- SQLite (premier jet — bascule PostgreSQL plus tard)
- Bootstrap 5 via CDN + django-crispy-forms
- Paiement : simulateur intégré, intégration Mollie prévue

## Installation locale

```bash
git clone <url-du-repo> Ecole
cd Ecole

python -m venv venv
source venv/bin/activate       # sous Windows : venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Éditer .env pour y coller une SECRET_KEY. Pour en générer une :
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

python manage.py migrate
python manage.py createsuperuser
python manage.py peupler_demo   # (optionnel) crée classes, enfants, menus, parents de test

python manage.py runserver
```

- Interface parents : <http://localhost:8000/>
- Admin Django (comptabilité, cuisine, etc.) : <http://localhost:8000/admin/>

## Comptes de démonstration

Les comptes ci-dessous sont créés par `python manage.py peupler_demo`
(sauf le superutilisateur, voir plus bas). Ils permettent de tester
chaque parcours sans créer de compte à la main.

| Identifiant                     | Mot de passe | Rôle           |
|---------------------------------|--------------|----------------|
| parent.dupont@example.be        | demo1234     | Parent               |
| parent.lemoine@example.be       | demo1234     | Parent               |
| cuisine                         | cuisine1234  | Groupe Cuisine       |
| compta                          | compta1234   | Groupe Comptabilite  |

**Superutilisateur (admin)** — *non* créé par `peupler_demo` : il se
crée manuellement à l'installation avec `python manage.py createsuperuser`.
Il donne accès à l'admin Django (<http://localhost:8000/admin/>) pour
consulter les données (dont l'historique des paiements virement
legacy conservé en base).

**Parent** — pour tester le parcours parent (composition du panier,
paiement simulé, historique), connectez-vous avec
`parent.dupont@example.be` (mot de passe `demo1234`) sur le site
public (<http://localhost:8000/>). Ce parent a déjà des enfants
rattachés dans les données de démo.

**Cuisine** — le compte `cuisine` (mot de passe `cuisine1234`) est membre
du groupe Django `Cuisine` et accède aux vues cuisinière
(`/cuisine/calendrier/`, `/cuisine/aujourdhui/`) et à la gestion des menus.

**Comptabilité** — le compte `compta` (mot de passe `compta1234`) est
membre du groupe Django `Comptabilite` (sans statut staff) et accède
au suivi croisé repas par enfant (`/comptabilite/suivi-enfants/`).
Il ne peut ni créer ni modifier les enfants, classes ou menus —
uniquement consulter.

## Structure principale

```
Ecole/
  manage.py
  requirements.txt
  .env.example
  ecole/                  # configuration du projet Django
    settings.py, urls.py, wsgi.py, asgi.py
  cantine/                # app métier (parents, enfants, menus, réservations, paiements)
    models.py, views.py, urls.py, forms.py, admin.py, signals.py
    templates/cantine/
    management/commands/peupler_demo.py
```

## Suggestions de menus (générateur combinatoire)

Le formulaire de création de menu (`/cuisine/menus/creer/`) propose des
idées de plats **générées à la volée** par `cantine/generateur_menus.py`,
plutôt qu'une liste figée. Chaque suggestion combine quatre briques —
protéine + féculent + légume + sauce/accompagnement — ce qui garantit un
plat équilibré, sans porc dans les protéines ni alcool dans les sauces.

Nombre de combinaisons possibles (produit des tailles de listes) :

- Toutes protéines : **19 × 10 × 14 × 10 = 26 600** combinaisons.
- Végétariennes uniquement : **8 × 10 × 14 × 10 = 11 200** combinaisons.

On dépasse donc très largement l'objectif de 1000 suggestions distinctes.
Une case « Suggestions végétariennes uniquement » sur le formulaire limite
l'affichage aux combinaisons végétariennes. Tout est calculé localement,
sans dépendance externe ni appel réseau. La liste statique historique
(`cantine/idees_menus.py`) est conservée à titre de référence mais n'est
plus la source des suggestions.

## Prochaines étapes (issues à venir)

- Interfaces dédiées cuisine / enseignants / cuisinière
- Intégration Mollie réelle en remplacement du simulateur
  (`# TODO Mollie` dans `cantine/views.py`) — implique un
  rapprochement bancaire entre les paiements Mollie et le compte
  bancaire de l'école
- Bascule PostgreSQL + configuration de prod
- Notifications e-mail (paiement encaissé, présence à confirmer)
