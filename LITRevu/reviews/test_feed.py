from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Review, Ticket, UserFollows

User = get_user_model()


class FeedTests(TestCase):
    def setUp(self):
        self.me = User.objects.create_user('moi', password='x')
        self.ami = User.objects.create_user('ami', password='x')
        self.inconnu = User.objects.create_user('inconnu', password='x')
        UserFollows.objects.create(user=self.me, followed_user=self.ami)
        self.client.force_login(self.me)

    def feed(self):
        return self.client.get(reverse('home'))

    def test_page_protegee(self):
        self.client.logout()
        r = self.client.get(reverse('home'))
        self.assertRedirects(r, f"{reverse('login')}?next={reverse('home')}")

    def test_flux_vide(self):
        self.assertContains(self.feed(), 'Votre flux est vide')

    def test_billets_miens_et_suivis_seulement(self):
        Ticket.objects.create(title='Mon billet', user=self.me)
        Ticket.objects.create(title='Billet ami', user=self.ami)
        Ticket.objects.create(title='Billet inconnu', user=self.inconnu)
        r = self.feed()
        self.assertContains(r, 'Mon billet')
        self.assertContains(r, 'Billet ami')
        self.assertNotContains(r, 'Billet inconnu')

    def test_critique_d_un_inconnu_sur_mon_billet_visible(self):
        t = Ticket.objects.create(title='Mon billet', user=self.me)
        Review.objects.create(ticket=t, rating=3, headline='Avis inconnu', user=self.inconnu)
        self.assertContains(self.feed(), 'Avis inconnu')

    def test_critique_d_un_inconnu_sur_billet_d_un_autre_invisible(self):
        t = Ticket.objects.create(title='Billet inconnu', user=self.inconnu)
        Review.objects.create(ticket=t, rating=3, headline='Avis caché', user=self.inconnu)
        self.assertNotContains(self.feed(), 'Avis caché')

    def test_critique_d_un_ami_visible_meme_sur_billet_d_un_inconnu(self):
        t = Ticket.objects.create(title='Billet inconnu', user=self.inconnu)
        Review.objects.create(ticket=t, rating=5, headline='Avis ami', user=self.ami)
        self.assertContains(self.feed(), 'Avis ami')

    def test_critique_seule_d_un_ami_affichee_sans_demande(self):
        t = Ticket.objects.create(title='Livre ami', author='Auteur', user=self.ami, is_request=False)
        Review.objects.create(ticket=t, rating=4, headline='Critique libre', user=self.ami)
        page = self.feed().content.decode()
        self.assertIn('Critique libre', page)
        self.assertNotIn('demandé une critique', page)
        self.assertIn('Ticket - ami', page)
        self.assertNotIn('review_create', page)

    def test_ordre_du_plus_recent_au_plus_ancien(self):
        Ticket.objects.create(title='AAA ancien', user=self.me)
        Ticket.objects.create(title='ZZZ recent', user=self.ami)
        page = self.feed().content.decode()
        self.assertLess(page.index('ZZZ recent'), page.index('AAA ancien'))

    def test_bouton_repondre_puis_masque_apres_critique(self):
        t = Ticket.objects.create(title='Billet ami', user=self.ami)
        url = reverse('review_create', args=[t.pk])
        self.assertContains(self.feed(), url)
        Review.objects.create(ticket=t, rating=3, headline='Fait', user=self.me)
        self.assertNotContains(self.feed(), url)

    def test_pas_de_bouton_repondre_sur_billet_non_suivi(self):
        # le billet n'est même pas dans le flux
        t = Ticket.objects.create(title='Billet inconnu', user=self.inconnu)
        self.assertNotContains(self.feed(), reverse('review_create', args=[t.pk]))
