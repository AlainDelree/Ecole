"""
Réglages Django pour le projet Ecole.

Ce premier jet vise le développement local :
  - SQLite comme base de données (aucune installation requise),
  - DEBUG activé,
  - SECRET_KEY lue depuis un fichier .env (voir .env.example).

Une bascule vers PostgreSQL et une vraie configuration de prod sera
faite dans une issue ultérieure.
"""

from pathlib import Path

from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).resolve().parent.parent

# Charge les variables d'environnement définies dans .env (à la racine du projet).
load_dotenv(BASE_DIR / ".env")


SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    # On refuse de démarrer sans SECRET_KEY plutôt que d'en générer une
    # jetable en silence : ça évite qu'un admin perde ses sessions à
    # chaque redémarrage sans comprendre pourquoi.
    raise RuntimeError(
        "SECRET_KEY manquante. Copie .env.example en .env et remplis "
        "SECRET_KEY (voir instructions dans le fichier)."
    )

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Tierces
    "crispy_forms",
    "crispy_bootstrap5",
    # Locales
    "cantine.apps.CantineConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ecole.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "ecole.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Belgique francophone : locale, fuseau, formats de date.
LANGUAGE_CODE = "fr-be"
TIME_ZONE = "Europe/Brussels"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Formats de date "à la belge" (jour/mois/année).
DATE_FORMAT = "d/m/Y"
DATETIME_FORMAT = "d/m/Y H:i"
SHORT_DATE_FORMAT = "d/m/Y"


STATIC_URL = "static/"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Redirections d'authentification.
LOGIN_URL = "cantine:connexion"
LOGIN_REDIRECT_URL = "cantine:accueil"
LOGOUT_REDIRECT_URL = "cantine:connexion"


# Crispy Forms : on utilise le pack Bootstrap 5.
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
