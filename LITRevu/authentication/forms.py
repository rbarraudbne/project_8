from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


class LoginForm(AuthenticationForm):
    """Formulaire de connexion (libellés en français, autocomplete pour WCAG 1.3.5)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Nom d'utilisateur"
        self.fields['username'].widget.attrs.update({'autocomplete': 'username'})
        self.fields['password'].label = 'Mot de passe'
        self.fields['password'].widget.attrs.update({'autocomplete': 'current-password'})


class SignupForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'autocomplete': 'username'})
        self.fields['email'].required = True
        self.fields['email'].widget.attrs.update({'autocomplete': 'email'})
        self.fields['password1'].widget.attrs.update({'autocomplete': 'new-password'})
        self.fields['password2'].widget.attrs.update({'autocomplete': 'new-password'})
