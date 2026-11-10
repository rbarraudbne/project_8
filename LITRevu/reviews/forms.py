from django import forms

from .models import Review, Ticket


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('title', 'description', 'image')
        labels = {
            'title': 'Titre',
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
