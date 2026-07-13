# Ecole — Contexte du projet

Système de gestion des repas scolaires pour une école primaire belge de ~50-200 élèves. Développé par Alain (en reconversion, apprentissage Python en cours) sur ThinkPad Ubuntu 24.04. Bridge_Agent orchestre le développement : Claude Chat rédige les issues, CCL (Claude Code Linux) code.

## Vue d'ensemble du flux métier

Le repas d'un enfant passe par 5 étapes séquentielles :

1. **Réservation** — le parent réserve un repas sur le portail web (jusqu'à ~1 mois à l'avance).
2. **Paiement** — le parent vire de l'argent sur le compte de l'école ; la comptabilité valide la réception du virement dans l'admin. Le solde du parent est crédité à ce moment-là.
3. **Confirmation cuisine** — la cuisinière voit les réservations confirmées et prépare ses commandes en conséquence.
4. **Présence matin** — l'enseignant fait l'appel en classe ; les enfants réservés mais absents sont désinscrits du repas du jour (permet à la cuisinière d'ajuster avant de cuisiner).
5. **Validation post-repas** — la cuisinière valide les enfants qui ont effectivement mangé. C'est *seulement à ce moment-là* que le solde du parent est décompté.

## Rôles utilisateurs

| Rôle | Interface prévue | Statut |
|------|------------------|--------|
| Parents | Site web public (Django) | En cours (première issue) |
| Comptabilité | Admin Django | Premier jet |
| Cuisinière | Admin Django puis appli dédiée + scan QR | Futur |
| Enseignants | Appli mobile + scan QR badge élève | Futur |
| Secrétaire | Admin Django (gestion enfants/classes) | Premier jet |
| Direction | Admin Django (vue d'ensemble) | Premier jet |

Toutes les interfaces staff passent par l'admin Django pour l'instant — on itèrera au fur et à mesure.

## Pile technique

- **Backend** : Django 5 (Python 3.12+)
- **Base de données** : SQLite pour le développement, migration PostgreSQL prévue avant mise en production
- **Frontend** : templates Django + Bootstrap 5 via CDN, pas de build JS
- **Formulaires** : django-crispy-forms + crispy-bootstrap5
- **Paiements** : virement bancaire manuel pour le premier jet, intégration Mollie prévue plus tard (belge, gère SEPA et Bancontact)
- **Hébergement** : local pour le développement, VPS européen (Scaleway ou OVH) prévu pour la production, RGPD-friendly

## Modèles de données (référence)

Les cinq entités principales :

- `ProfilParent` (OneToOne avec User) — solde stocké en **cents (IntegerField)** pour éviter les erreurs de flottants
- `Classe`
- `Enfant` (FK vers Classe et ProfilParent)
- `Menu` (un par date, avec date/heure limite de réservation)
- `Reservation` (FK vers Enfant et Menu, avec statut multi-étapes : en_attente_paiement → confirmee → presence_matin_ok → mangee)
- `Paiement` (FK vers ProfilParent, avec statut declare → valide/rejete)

## Décisions et conventions

- **Argent en cents (int), jamais en float.** Toutes les valeurs monétaires sont des `IntegerField` en centimes. Conversion en euros uniquement à l'affichage.
- **Locale belge** : `LANGUAGE_CODE = 'fr-be'`, `TIME_ZONE = 'Europe/Brussels'`, formats de date belges.
- **Code et commentaires en français.** Docstrings, noms de fonctions, variables métier : tout en français. Anglais uniquement pour les mots-clés Python et les noms Django framework (`models`, `forms`, `views`, `admin`).
- **Pas de librairies exotiques.** Rester dans le mainstream Django. Éviter les dépendances qui compliquent la maintenance à long terme.
- **Sécurité par défaut** : `SECRET_KEY` en variable d'environnement (`.env` + python-dotenv), `.env` et `db.sqlite3` gitignorés, `DEBUG=True` uniquement en dev.
- **Ne jamais faire `git push`.** Règle Bridge_Agent §5 — Alain pousse lui-même après vérification avec `git show`.
- **Commits atomiques**, messages en français clair, un commit par fonctionnalité cohérente.

## Contexte belge

- Public cible : école primaire de la Fédération Wallonie-Bruxelles
- Le contexte réglementaire évolue : dispositif « repas scolaires gratuits » supprimé fin 2025, ce qui rend la gestion cantine côté école plus critique qu'avant
- Paiements par virement SEPA (compte bancaire belge de l'école)
- Format des références de virement : structurés belges (OGM/BBA) prévus pour Mollie plus tard, texte libre pour le premier jet
- Les enfants ont typiquement entre 2,5 et 12 ans (maternelle + primaire)

## Structure du dépôt (attendue après premier jet)

- `manage.py`, `requirements.txt`, `README.md`, `.gitignore`, `CONTEXTE.md`
- `ecole/` — config Django (settings, urls racine)
- `cantine/` — app métier principale (models, views, admin, templates, forms, urls, migrations)
- `.env.example` versionné, `.env` gitignoré

## État actuel (à mettre à jour à chaque issue majeure)

- Projet créé le 13 juillet 2026
- Dépôt GitHub : AlainDelree/Ecole
- Périmètre CCL : /home/alain/Ecole
- Watcher Bridge_Agent : configs/ecole.conf
- **Prochaine étape** : premier jet du site parents (issue en cours)

## Ce que CCL doit toujours garder en tête

- Rester **dans le périmètre** `/home/alain/Ecole` — ne rien toucher ailleurs
- **Lecture seule par défaut**, écriture uniquement si `mode_write` sur l'issue
- **Ne jamais `git push`**
- **Toujours en français** pour tout ce qui n'est pas contrainte technique
- **Argent en cents**, jamais en flottant
- Signaler dans le commentaire de fermeture d'issue tout écart par rapport à la demande initiale
