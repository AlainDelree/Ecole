"""Configuration WSGI pour le projet Ecole."""

import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecole.settings")

application = get_wsgi_application()
