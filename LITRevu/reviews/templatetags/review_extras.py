from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
def stars(rating):
    """Affiche une note sous forme d'étoiles, avec un texte pour les lecteurs d'écran."""
    rating = int(rating)
    return format_html(
        '<span class="stars"><span aria-hidden="true">{}{}</span>'
        '<span class="visually-hidden">Note : {} sur 5</span></span>',
        '★' * rating, '☆' * (5 - rating), rating)
