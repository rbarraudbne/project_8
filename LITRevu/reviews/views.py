from itertools import chain

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReviewForm, TicketForm
from .models import Review, Ticket, UserFollows


def can_review(user, ticket):
    """Peut-on répondre à ce billet ?

    - c'est mon billet, ou celui d'un utilisateur que je suis ;
    - je n'ai pas déjà posté de critique sur ce billet.
    """
    allowed = ticket.user_id == user.id or UserFollows.objects.filter(
        user=user, followed_user=ticket.user).exists()
    already = Review.objects.filter(ticket=ticket, user=user).exists()
    return allowed and not already


@login_required
def posts(request):
    """Mes billets et mes critiques, du plus récent au plus ancien."""
    tickets = Ticket.objects.filter(user=request.user)
    reviews = Review.objects.filter(user=request.user).select_related('ticket', 'ticket__user')
    items = sorted(
        chain(
            ((t.time_created, 'ticket', t) for t in tickets),
            ((r.time_created, 'review', r) for r in reviews),
        ),
        key=lambda item: item[0], reverse=True)
    return render(request, 'reviews/posts.html', {'items': items})


# --- Billets -----------------------------------------------------------

@login_required
def ticket_create(request):
    form = TicketForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        ticket = form.save(commit=False)
        ticket.user = request.user
        ticket.save()
        messages.success(request, 'Votre billet a été publié.')
        return redirect('posts')
    return render(request, 'reviews/ticket_form.html', {'form': form, 'edit': False})


@login_required
def ticket_update(request, ticket_id):
    # user=request.user : on ne peut modifier que ses propres billets (404 sinon)
    ticket = get_object_or_404(Ticket, pk=ticket_id, user=request.user)
    form = TicketForm(request.POST or None, request.FILES or None, instance=ticket)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Votre billet a été modifié.')
        return redirect('posts')
    return render(request, 'reviews/ticket_form.html', {'form': form, 'edit': True, 'ticket': ticket})


@login_required
def ticket_delete(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id, user=request.user)
    if request.method == 'POST':
        ticket.delete()
        messages.success(request, 'Votre billet a été supprimé.')
        return redirect('posts')
    return render(request, 'reviews/ticket_confirm_delete.html', {'ticket': ticket})


# --- Critiques ---------------------------------------------------------

@login_required
def review_create(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if not can_review(request.user, ticket):
        messages.error(request, "Vous ne pouvez pas répondre à ce billet.")
        return redirect('home')
    form = ReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.ticket = ticket
        review.user = request.user
        review.save()
        messages.success(request, 'Votre critique a été publiée.')
        return redirect('posts')
    return render(request, 'reviews/review_form.html', {'form': form, 'ticket': ticket, 'edit': False})


@login_required
def review_update(request, review_id):
    review = get_object_or_404(Review, pk=review_id, user=request.user)
    form = ReviewForm(request.POST or None, instance=review)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Votre critique a été modifiée.')
        return redirect('posts')
    return render(request, 'reviews/review_form.html', {'form': form, 'ticket': review.ticket, 'edit': True})


@login_required
def review_delete(request, review_id):
    review = get_object_or_404(Review, pk=review_id, user=request.user)
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Votre critique a été supprimée.')
        return redirect('posts')
    return render(request, 'reviews/review_confirm_delete.html', {'review': review})


@login_required
def review_create_full(request):
    """Crée un billet ET une critique sur ce billet en une seule étape."""
    ticket_form = TicketForm(request.POST or None, request.FILES or None, prefix='ticket')
    review_form = ReviewForm(request.POST or None, prefix='review')
    if request.method == 'POST' and ticket_form.is_valid() and review_form.is_valid():
        with transaction.atomic():  # tout ou rien
            ticket = ticket_form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            review = review_form.save(commit=False)
            review.ticket = ticket
            review.user = request.user
            review.save()
        messages.success(request, 'Votre critique a été publiée.')
        return redirect('posts')
    return render(request, 'reviews/review_create_full.html', {
        'ticket_form': ticket_form, 'review_form': review_form})
