from django.test import TestCase

# Create your tests here.
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Review, Ticket, UserFollows

User = get_user_model()


class ModelsTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user('a', password='x')
        self.b = User.objects.create_user('b', password='x')

    def test_ticket_et_review(self):
        t = Ticket.objects.create(title='La relativité', user=self.a)
        Review.objects.create(ticket=t, rating=5, headline='Top', user=self.b)
        self.assertEqual(t.review_set.count(), 1)

    def test_follow_unique(self):
        UserFollows.objects.create(user=self.a, followed_user=self.b)
        with self.assertRaises(IntegrityError), transaction.atomic():
            UserFollows.objects.create(user=self.a, followed_user=self.b)
        self.assertEqual(self.b.followed_by.count(), 1)


class AdminTests(TestCase):
    """Vérifie que les modèles sont utilisables depuis l'admin Django."""

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'a@ex.fr', 'x-Admin-4242')
        self.client.force_login(self.admin)
        self.other = User.objects.create_user('b', password='x')

    def test_pages_liste_et_ajout(self):
        for model in ('ticket', 'review', 'userfollows'):
            for page in ('changelist', 'add'):
                url = f'/admin/reviews/{model}/' + ('' if page == 'changelist' else 'add/')
                self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_creer_ticket_puis_critique_via_admin(self):
        r = self.client.post('/admin/reviews/ticket/add/', {
            'title': 'La relativité', 'description': 'Avis ?', 'user': self.admin.pk})
        self.assertEqual(r.status_code, 302)
        ticket = Ticket.objects.get()
        r = self.client.post('/admin/reviews/review/add/', {
            'ticket': ticket.pk, 'rating': 4, 'headline': 'Excellent',
            'body': '', 'user': self.other.pk})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(ticket.review_set.get().rating, 4)

    def test_note_hors_limites_refusee(self):
        t = Ticket.objects.create(title='T', user=self.admin)
        r = self.client.post('/admin/reviews/review/add/', {
            'ticket': t.pk, 'rating': 6, 'headline': 'x', 'user': self.other.pk})
        self.assertEqual(r.status_code, 200)  # formulaire réaffiché avec erreur
        self.assertEqual(Review.objects.count(), 0)

    def test_abonnement_via_admin(self):
        r = self.client.post('/admin/reviews/userfollows/add/', {
            'user': self.admin.pk, 'followed_user': self.other.pk})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.admin.following.count(), 1)


# --- Étape 4 : vues billets / critiques -------------------------------------
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
from django.test import override_settings


class ViewsBase(TestCase):
    def setUp(self):
        self.a = User.objects.create_user('a', password='x')
        self.b = User.objects.create_user('b', password='x')
        self.client.force_login(self.a)


class TicketViewsTests(ViewsBase):
    def test_anonyme_redirige_vers_connexion(self):
        self.client.logout()
        for name, args in (('posts', ()), ('ticket_create', ()), ('ticket_update', (1,)),
                           ('ticket_delete', (1,)), ('review_create', (1,))):
            r = self.client.get(reverse(name, args=args))
            self.assertEqual(r.status_code, 302, name)
            self.assertIn(reverse('login'), r.headers['Location'])

    def test_creation(self):
        r = self.client.post(reverse('ticket_create'), {'title': 'Livre', 'description': 'Avis ?'})
        self.assertRedirects(r, reverse('posts'))
        t = Ticket.objects.get()
        self.assertEqual(t.user, self.a)

    def test_creation_avec_image(self):
        from io import BytesIO
        from PIL import Image
        buf = BytesIO(); Image.new('RGB', (4, 4)).save(buf, 'PNG')
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp):
            f = SimpleUploadedFile('c.png', buf.getvalue(), content_type='image/png')
            r = self.client.post(reverse('ticket_create'), {'title': 'Livre', 'image': f})
            self.assertRedirects(r, reverse('posts'))
            self.assertTrue(Ticket.objects.get().image.name.startswith('tickets/'))

    def test_titre_obligatoire(self):
        r = self.client.post(reverse('ticket_create'), {'title': ''})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_modification(self):
        t = Ticket.objects.create(title='Ancien', user=self.a)
        r = self.client.post(reverse('ticket_update', args=[t.pk]), {'title': 'Nouveau'})
        self.assertRedirects(r, reverse('posts'))
        t.refresh_from_db()
        self.assertEqual(t.title, 'Nouveau')

    def test_modification_et_suppression_interdites_sur_billet_d_autrui(self):
        t = Ticket.objects.create(title='Autrui', user=self.b)
        self.assertEqual(self.client.get(reverse('ticket_update', args=[t.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('ticket_update', args=[t.pk]), {'title': 'X'}).status_code, 404)
        self.assertEqual(self.client.post(reverse('ticket_delete', args=[t.pk])).status_code, 404)
        t.refresh_from_db()
        self.assertEqual(t.title, 'Autrui')

    def test_suppression_uniquement_en_post(self):
        t = Ticket.objects.create(title='T', user=self.a)
        r = self.client.get(reverse('ticket_delete', args=[t.pk]))
        self.assertEqual(r.status_code, 200)       # simple page de confirmation
        self.assertTrue(Ticket.objects.filter(pk=t.pk).exists())
        r = self.client.post(reverse('ticket_delete', args=[t.pk]))
        self.assertRedirects(r, reverse('posts'))
        self.assertFalse(Ticket.objects.filter(pk=t.pk).exists())

    def test_page_posts_liste_mes_posts_seulement(self):
        Ticket.objects.create(title='Le mien', user=self.a)
        Ticket.objects.create(title='Celui de b', user=self.b)
        r = self.client.get(reverse('posts'))
        self.assertContains(r, 'Le mien')
        self.assertNotContains(r, 'Celui de b')


class ReviewViewsTests(ViewsBase):
    def setUp(self):
        super().setUp()
        self.ticket_b = Ticket.objects.create(title='Billet de b', user=self.b)
        self.data = {'headline': 'Super', 'rating': 5, 'body': 'Génial'}

    def test_pas_de_reponse_si_on_ne_suit_pas(self):
        r = self.client.post(reverse('review_create', args=[self.ticket_b.pk]), self.data)
        self.assertRedirects(r, reverse('home'))
        self.assertEqual(Review.objects.count(), 0)

    def test_reponse_si_on_suit(self):
        UserFollows.objects.create(user=self.a, followed_user=self.b)
        self.assertEqual(self.client.get(reverse('review_create', args=[self.ticket_b.pk])).status_code, 200)
        r = self.client.post(reverse('review_create', args=[self.ticket_b.pk]), self.data)
        self.assertRedirects(r, reverse('posts'))
        review = Review.objects.get()
        self.assertEqual((review.user, review.ticket, review.rating), (self.a, self.ticket_b, 5))

    def test_une_seule_critique_par_billet_et_par_utilisateur(self):
        UserFollows.objects.create(user=self.a, followed_user=self.b)
        self.client.post(reverse('review_create', args=[self.ticket_b.pk]), self.data)
        self.client.post(reverse('review_create', args=[self.ticket_b.pk]), self.data)
        self.assertEqual(Review.objects.count(), 1)

    def test_note_invalide(self):
        UserFollows.objects.create(user=self.a, followed_user=self.b)
        for bad in (6, -1, 'x', ''):
            r = self.client.post(reverse('review_create', args=[self.ticket_b.pk]), {**self.data, 'rating': bad})
            self.assertEqual(r.status_code, 200, bad)
        self.assertEqual(Review.objects.count(), 0)

    def test_modifier_et_supprimer_sa_critique(self):
        rev = Review.objects.create(ticket=self.ticket_b, rating=2, headline='Bof', user=self.a)
        r = self.client.post(reverse('review_update', args=[rev.pk]), {'headline': 'Mieux', 'rating': 4})
        self.assertRedirects(r, reverse('posts'))
        rev.refresh_from_db()
        self.assertEqual((rev.headline, rev.rating), ('Mieux', 4))
        self.assertEqual(self.client.get(reverse('review_delete', args=[rev.pk])).status_code, 200)
        self.assertEqual(Review.objects.count(), 1)
        self.client.post(reverse('review_delete', args=[rev.pk]))
        self.assertEqual(Review.objects.count(), 0)

    def test_critique_d_autrui_intouchable(self):
        rev = Review.objects.create(ticket=self.ticket_b, rating=2, headline='De b', user=self.b)
        for name in ('review_update', 'review_delete'):
            self.assertEqual(self.client.get(reverse(name, args=[rev.pk])).status_code, 404)
            self.assertEqual(self.client.post(reverse(name, args=[rev.pk]), {'headline': 'X', 'rating': 1}).status_code, 404)
        self.assertEqual(Review.objects.get().headline, 'De b')


class ReviewCreateFullTests(ViewsBase):
    def data(self, **kw):
        d = {'ticket-title': 'Livre', 'ticket-description': 'D',
             'review-headline': 'Top', 'review-rating': 5, 'review-body': ''}
        d.update(kw)
        return d

    def test_page_accessible_et_protegee(self):
        self.assertEqual(self.client.get(reverse('review_create_full')).status_code, 200)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('review_create_full')).status_code, 302)

    def test_cree_billet_et_critique(self):
        r = self.client.post(reverse('review_create_full'), self.data())
        self.assertRedirects(r, reverse('posts'))
        ticket, review = Ticket.objects.get(), Review.objects.get()
        self.assertEqual((ticket.user, review.user, review.ticket), (self.a, self.a, ticket))

    def test_rien_n_est_cree_si_un_formulaire_est_invalide(self):
        r = self.client.post(reverse('review_create_full'), self.data(**{'review-rating': 9}))
        self.assertEqual(r.status_code, 200)
        r = self.client.post(reverse('review_create_full'), self.data(**{'ticket-title': ''}))
        self.assertEqual(r.status_code, 200)
        self.assertEqual((Ticket.objects.count(), Review.objects.count()), (0, 0))
