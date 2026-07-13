#!/usr/bin/env python
"""Utilitaire en ligne de commande de Django pour le projet Ecole."""
import os
import sys


def main():
    """Exécute une commande d'administration Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecole.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django ne semble pas installé. As-tu activé le venv et lancé "
            "`pip install -r requirements.txt` ?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
