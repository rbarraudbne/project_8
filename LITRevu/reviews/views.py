from itertools import chain

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import FollowForm, ReviewForm, TicketForm
from .models import Review, Ticket, UserFollows


def can_review(user, ticket):
    """Peut-on répondre à ce billet ?

    - c'est une vraie demande de critique (pas un livre saisi avec une
      critique) ;
    - c'est mon billet, ou celui d'un utilisateur que je suis ;
    - aucune critique n'a encore été postée en réponse à ce billet
      (par personne).
    """
    if not ticket.is_request:
        return False
    allowed = ticket.user_id == user.id or UserFollows.objects.filter(
        user=user, followed_user=ticket.user).exists()
    already = Review.objects.filter(ticket=ticket).exists()
    return allowed and not already


@login_required
def posts(request):
    """Mes billets et mes critiques, du plus récent au plus ancien."""
    tickets = Ticket.objects.filter(user=request.user, is_request=True)
    reviews = (Review.objects
               .filter(user=request.user)
               .select_related('ticket', 'ticket__user'))
    items = sorted(
        chain(
            ((t.time_created, 'ticket', t) for t in tickets),
            ((r.time_created, 'review', r) for r in reviews),
        ),
        key=lambda item: item[0],
        reverse=True,
    )
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
    return render(
        request,
        'reviews/ticket_form.html',
        {'form': form, 'edit': False},
    )


@login_required
def ticket_update(request, ticket_id):
    # user=request.user : on ne peut modifier que ses propres billets
    # (404 sinon)
    ticket = get_object_or_404(Ticket, pk=ticket_id, user=request.user)
    form = TicketForm(
        request.POST or None, request.FILES or None, instance=ticket)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Votre billet a été modifié.')
        return redirect('posts')
    return render(
        request,
        'reviews/ticket_form.html',
        {'form': form, 'edit': True, 'ticket': ticket},
    )


@login_required
def ticket_delete(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id, user=request.user)
    if request.method == 'POST':
        ticket.delete()
        messages.success(request, 'Votre billet a été supprimé.')
        return redirect('posts')
    return render(
        request, 'reviews/ticket_confirm_delete.html', {'ticket': ticket})


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
    return render(
        request,
        'reviews/review_form.html',
        {'form': form, 'ticket': ticket, 'edit': False},
    )


@login_required
def review_update(request, review_id):
    review = get_object_or_404(Review, pk=review_id, user=request.user)
    ticket = review.ticket
    if not ticket.is_request:
        # Critique « à partir de zéro » : on modifie aussi le livre / article
        return _review_update_full(request, review, ticket)
    form = ReviewForm(request.POST or None, instance=review)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Votre critique a été modifiée.')
        return redirect('posts')
    return render(
        request,
        'reviews/review_form.html',
        {'form': form, 'ticket': ticket, 'edit': True},
    )


def _review_update_full(request, review, ticket):
    ticket_form = TicketForm(
        request.POST or None,
        request.FILES or None,
        instance=ticket,
        prefix='ticket',
    )
    review_form = ReviewForm(
        request.POST or None, instance=review, prefix='review')
    if (request.method == 'POST'
            and ticket_form.is_valid()
            and review_form.is_valid()):
        with transaction.atomic():
            ticket_form.save()
            review_form.save()
        messages.success(request, 'Votre critique a été modifiée.')
        return redirect('posts')
    return render(
        request,
        'reviews/review_create_full.html',
        {
            'ticket_form': ticket_form,
            'review_form': review_form,
            'edit': True,
        },
    )


@login_required
def review_delete(request, review_id):
    review = get_object_or_404(Review, pk=review_id, user=request.user)
    if request.method == 'POST':
        ticket = review.ticket
        review.delete()
        if not ticket.is_request:
            # le livre saisi avec la critique n'a plus de raison d'exister
            ticket.delete()
        messages.success(request, 'Votre critique a été supprimée.')
        return redirect('posts')
    return render(
        request, 'reviews/review_confirm_delete.html', {'review': review})


@login_required
def review_create_full(request):
    """Crée un billet ET une critique sur ce billet en une seule étape."""
    ticket_form = TicketForm(
        request.POST or None, request.FILES or None, prefix='ticket')
    review_form = ReviewForm(request.POST or None, prefix='review')
    if (request.method == 'POST'
            and ticket_form.is_valid()
            and review_form.is_valid()):
        with transaction.atomic():  # tout ou rien
            ticket = ticket_form.save(commit=False)
            ticket.user = request.user
            ticket.is_request = False  # ce n'est pas une demande de critique
            ticket.save()
            review = review_form.save(commit=False)
            review.ticket = ticket
            review.user = request.user
            review.save()
        messages.success(request, 'Votre critique a été publiée.')
        return redirect('posts')
    return render(
        request,
        'reviews/review_create_full.html',
        {
            'ticket_form': ticket_form,
            'review_form': review_form,
            'edit': False,
        },
    )


# --- Abonnements -------------------------------------------------------

@login_required
def follows(request):
    """Suivre un utilisateur, voir ses abonnements et ses abonnés."""
    form = FollowForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        UserFollows.objects.create(
            user=request.user, followed_user=form.followed_user)
        messages.success(
            request,
            f'Vous suivez maintenant {form.followed_user.username}.',
        )
        return redirect('follows')
    following = (UserFollows.objects
                 .filter(user=request.user)
                 .select_related('followed_user')
                 .order_by('followed_user__username'))
    followers = (UserFollows.objects
                 .filter(followed_user=request.user)
                 .select_related('user')
                 .order_by('user__username'))
    return render(
        request,
        'reviews/follows.html',
        {'form': form, 'following': following, 'followers': followers},
    )


@login_required
@require_POST
def unfollow(request, follow_id):
    # user=request.user : on ne peut supprimer que ses propres abonnements
    follow = get_object_or_404(UserFollows, pk=follow_id, user=request.user)
    follow.delete()
    messages.success(
        request, f'Vous ne suivez plus {follow.followed_user.username}.')
    return redirect('follows')


# --- Flux --------------------------------------------------------------

@login_required
def feed(request):
    """Page d'accueil : billets et critiques de l'utilisateur connecté.

    - billets (demandes) : les miens et ceux des utilisateurs que je suis ;
    - critiques : les miennes, celles des utilisateurs que je suis, et
      toutes celles qui répondent à l'un de mes billets (même d'un
      utilisateur non suivi).
    Le tout du plus récent au plus ancien.
    """
    me = request.user
    followed_ids = (UserFollows.objects
                    .filter(user=me)
                    .values_list('followed_user_id', flat=True))

    tickets = (Ticket.objects
               .filter(is_request=True)
               .filter(Q(user=me) | Q(user_id__in=followed_ids))
               .select_related('user'))
    reviews = (Review.objects
               .filter(Q(user=me)
                       | Q(user_id__in=followed_ids)
                       | Q(ticket__user=me))
               .select_related('user', 'ticket', 'ticket__user'))

    # billets qui ont déjà reçu au moins une critique (de n'importe qui)
    already_reviewed = set(
        Review.objects
        .filter(ticket__in=tickets)
        .values_list('ticket_id', flat=True)
    )
    items = sorted(
        chain(
            ((t.time_created, 'ticket', t, t.pk not in already_reviewed)
             for t in tickets),
            ((r.time_created, 'review', r, False) for r in reviews),
        ),
        key=lambda item: item[0],
        reverse=True,
    )
    return render(request, 'reviews/feed.html', {'items': items})
