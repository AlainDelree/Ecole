"""Configuration ASGI pour le projet Ecole."""

import os

from django.core.asgi import get_asgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecole.settings")

application = get_asgi_application()
