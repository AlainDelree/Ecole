"""URLs racine du projet Ecole.

L'admin Django reste sous /admin/. Toutes les vues parents sont
dans l'app cantine, montée à la racine.
"""

from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("cantine.urls", namespace="cantine")),
]
