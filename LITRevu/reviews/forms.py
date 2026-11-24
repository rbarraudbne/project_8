from django import forms
from django.contrib.auth import get_user_model

from .models import Review, Ticket, UserFollows


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('title', 'author', 'description', 'image')
        labels = {
            'title': 'Titre',
            'author': 'Auteur',
            'description': 'Description',
            'image': 'Image',
        }
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        label='Note',
        choices=[(i, str(i)) for i in range(6)],
        coerce=int,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Review
        fields = ('headline', 'rating', 'body')
        labels = {'headline': 'Titre', 'body': 'Commentaire'}
        widgets = {'body': forms.Textarea(attrs={'rows': 6})}


class FollowForm(forms.Form):
    """Suivre un utilisateur à partir de son nom d'utilisateur."""

    username = forms.CharField(label="Nom d'utilisateur", max_length=150)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.followed_user = None
        self.fields['username'].widget.attrs.update({
            'autocomplete': 'off',
            'autocapitalize': 'none',
            'spellcheck': 'false',
        })

    def clean_username(self):
        User = get_user_model()
        username = self.cleaned_data['username'].strip()
        try:
            followed = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError(
                f"L'utilisateur « {username} » n'existe pas. "
                "Vérifiez l'orthographe de son nom d'utilisateur."
            )
        if followed == self.user:
            raise forms.ValidationError(
                "Vous ne pouvez pas vous suivre vous-même.")
        already_followed = UserFollows.objects.filter(
            user=self.user, followed_user=followed).exists()
        if already_followed:
            raise forms.ValidationError(
                f"Vous suivez déjà {followed.username}.")
        self.followed_user = followed
        return username
