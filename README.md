# École — gestion des repas scolaires

Application Django pour gérer les réservations de repas d'une école
(≈ 50 à 200 élèves). Premier jet : **site parents uniquement**.
Les autres rôles (comptabilité, cuisine, enseignants) passent par
l'admin Django pour l'instant.

## Flux global

1. **Parents** — réservent des repas (jusqu'à 30 jours à l'avance) et
   déclarent leurs paiements par virement.
2. **Comptabilité** — valide les paiements reçus via l'admin Django,
   ce qui crédite automatiquement le solde du parent.
3. **Cuisine** — consulte les réservations confirmées.
4. **Enseignants** — confirment la présence de l'enfant le matin.
5. **Cuisinière** — valide le service post-repas, ce qui décompte le
   solde du parent (interface dédiée à venir).

## Pile technique

- Python 3.12+ / Django 5
- SQLite (premier jet — bascule PostgreSQL plus tard)
- Bootstrap 5 via CDN + django-crispy-forms
- Pas de passerelle de paiement pour l'instant

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

## Comptes de démo (après `peupler_demo`)

| E-mail                          | Mot de passe |
|---------------------------------|--------------|
| parent.dupont@example.be        | demo1234     |
| parent.lemoine@example.be       | demo1234     |

Le superuser Django (créé avec `createsuperuser`) sert de compte compta
pour valider les virements dans l'admin.

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

## Prochaines étapes (issues à venir)

- Interfaces dédiées cuisine / enseignants / cuisinière
- Intégration Mollie (paiement par carte plutôt que virement)
- Bascule PostgreSQL + configuration de prod
- Notifications e-mail (paiement validé, présence à confirmer)
