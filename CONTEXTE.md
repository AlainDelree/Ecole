# Ecole — Contexte du projet

Gestion des repas scolaires d'une école primaire belge (~50-200 élèves). Développé par Alain (reconversion Python) sur Ubuntu 24.04. Bridge_Agent orchestre : Claude Chat rédige les issues, CCL (Claude Code Linux) code.

## Flux métier

Le repas d'un enfant suit 5 étapes :

1. **Panier** — le parent choisit des repas (jusqu'à ~1 mois à l'avance) et les empile dans un panier de session.
2. **Paiement** — règlement du panier en une opération sur un écran dédié. Effectué via un **simulateur** en attendant Mollie ; les réservations passent en « confirmée » à la validation.
3. **Confirmation cuisine** — la cuisinière voit les réservations confirmées et prépare ses commandes.
4. **Présence matin** — l'enseignant fait l'appel ; les réservés absents sont désinscrits du jour.
5. **Validation post-repas** — la cuisinière valide les enfants qui ont mangé (statut final « mangée »).

### Paiement (simulateur, Mollie pas encore branché)
Vue `/paiement/simulateur/` → POST `/paiement/confirmer/` → `/paiement/succes/`. Le bouton « Payer maintenant » réussit toujours, crée les réservations. Un `# TODO Mollie` dans `cantine/views.py` marque le point d'insertion de l'API Mollie. Note : Mollie encaisse puis reverse en lots → un rapprochement bancaire sera nécessaire à l'intégration réelle.

### Legacy conservé
`ProfilParent.solde_cents` et le modèle `Paiement` (virements) sont conservés en base (pas de migration destructive), plus utilisés par le nouveau flux mais toujours visibles dans l'admin pour historique.

## Rôles / interfaces
Parents : site web Django (en cours). Comptabilité, Secrétaire, Direction : admin Django (premier jet). Cuisinière, Enseignants : admin Django puis appli dédiée + scan QR (futur). Tout le staff passe par l'admin Django pour l'instant.

## Pile technique
- **Backend** : Django 5, Python 3.12+
- **BDD** : SQLite en dev, PostgreSQL prévu avant prod
- **Frontend** : templates Django + Bootstrap 5 (CDN), pas de build JS
- **Formulaires** : django-crispy-forms + crispy-bootstrap5
- **Paiements** : simulateur (aucun encaissement réel), Mollie prévu (SEPA/Bancontact/cartes)
- **Hébergement** : local en dev, VPS européen (Scaleway/OVH) prévu, RGPD-friendly

## Modèles principaux
- `ProfilParent` (OneToOne User ; `solde_cents` legacy)
- `Classe` ; `Enfant` (FK Classe, ProfilParent)
- `Menu` (un par date, avec limite de réservation)
- `Reservation` (FK Enfant, Menu ; statut en_attente_paiement → confirmee → presence_matin_ok → mangee)
- `Paiement` (FK ProfilParent ; legacy, plus alimenté)

## Conventions
- **Argent en cents (int)**, jamais en float ; conversion en euros à l'affichage seulement.
- **Locale belge** : `LANGUAGE_CODE='fr-be'`, `TIME_ZONE='Europe/Brussels'`.
- **Code et commentaires en français** ; anglais réservé aux mots-clés Python et noms Django.
- **Pas de libs exotiques**, rester mainstream Django.
- **Sécurité** : `SECRET_KEY` en `.env` (python-dotenv), `.env` et `db.sqlite3` gitignorés, `DEBUG=True` en dev seulement.
- **Jamais `git push`** (Alain pousse lui-même). Commits atomiques, messages en français.

## Contexte belge
École primaire (Fédération Wallonie-Bruxelles), enfants ~2,5-12 ans. Dispositif « repas gratuits » supprimé fin 2025 → gestion cantine plus critique. Références de virement structurées belges (OGM/BBA) prévues pour Mollie.

## Structure du dépôt
`manage.py`, `requirements.txt`, `README.md`, `.gitignore`, `CONTEXTE.md`, `.env.example` (versionné). `ecole/` = config Django ; `cantine/` = app métier (models, views, admin, templates, forms, urls, migrations).

## État actuel
Projet créé le 13/07/2026. Dépôt GitHub AlainDelree/Ecole. Périmètre CCL : /home/alain/Ecole. Watcher : configs/ecole.conf. Flux panier → paiement simulé en place.

## Maintenance de ce fichier
Si la tâche que tu exécutes modifie l'architecture, les dépendances, les
conventions de code, ou l'état d'avancement majeur de ce projet, mets à
jour ce CONTEXTE.md en conséquence, dans le même commit.
