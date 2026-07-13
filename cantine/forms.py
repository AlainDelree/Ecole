"""Formulaires de l'app cantine.

On reste sur des ModelForm / Form Django tout simples : crispy-forms
s'occupe du rendu Bootstrap dans les templates.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class InscriptionParentForm(UserCreationForm):
    """Inscription d'un compte parent.

    On demande prénom / nom / téléphone en plus des champs standards
    de UserCreationForm (username, password1, password2). L'email
    sert d'identifiant : on le duplique dans le champ `username` de
    User pour rester compatible avec l'auth Django par défaut.
    """

    email = forms.EmailField(
        label="Adresse e-mail",
        required=True,
        help_text="Servira aussi d'identifiant de connexion.",
    )
    first_name = forms.CharField(label="Prénom", max_length=150, required=True)
    last_name = forms.CharField(label="Nom", max_length=150, required=True)
    telephone = forms.CharField(
        label="Téléphone", max_length=20, required=False,
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("Un compte existe déjà avec cette adresse.")
        return email

    def save(self, commit=True):
        # On force username = email (l'utilisateur ne voit qu'un seul champ).
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            # Le ProfilParent est créé par signal ; on met juste le téléphone.
            profil = user.profil_parent
            profil.telephone = self.cleaned_data.get("telephone", "")
            profil.save(update_fields=["telephone"])
        return user


class DeclarationVirementForm(forms.Form):
    """Formulaire de déclaration d'un virement par le parent."""

    montant_euros = forms.DecimalField(
        label="Montant (€)",
        min_value=0.01,
        decimal_places=2,
        help_text="Montant exact du virement effectué.",
    )
    reference_virement = forms.CharField(
        label="Référence du virement",
        max_length=100,
        help_text="Communication indiquée sur votre virement (libre ou structurée).",
    )

    def montant_cents(self) -> int:
        """Convertit le montant saisi en centimes (int)."""
        return int(round(self.cleaned_data["montant_euros"] * 100))
