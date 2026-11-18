from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import UserFollows

User = get_user_model()


class FollowsTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user('a', password='x')
        self.b = User.objects.create_user('b', password='x')
        self.client.force_login(self.a)

    def test_page_protegee(self):
        self.client.logout()
        r = self.client.get(reverse('follows'))
        self.assertRedirects(r, f"{reverse('login')}?next={reverse('follows')}")

    def test_suivre_un_utilisateur(self):
        r = self.client.post(reverse('follows'), {'username': 'b'})
        self.assertRedirects(r, reverse('follows'))
        self.assertTrue(UserFollows.objects.filter(user=self.a, followed_user=self.b).exists())

    def test_utilisateur_inexistant_affiche_un_message(self):
        r = self.client.post(reverse('follows'), {'username': 'fantome'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "L&#x27;utilisateur « fantome » n&#x27;existe pas")
        self.assertContains(r, 'role="alert"')
        self.assertEqual(UserFollows.objects.count(), 0)

    def test_on_ne_peut_pas_se_suivre_soi_meme(self):
        r = self.client.post(reverse('follows'), {'username': 'a'})
        self.assertContains(r, 'vous suivre vous-même')
        self.assertEqual(UserFollows.objects.count(), 0)

    def test_pas_de_doublon(self):
        UserFollows.objects.create(user=self.a, followed_user=self.b)
        r = self.client.post(reverse('follows'), {'username': 'b'})
        self.assertContains(r, 'déjà')
        self.assertEqual(UserFollows.objects.count(), 1)

    def test_listes_abonnements_et_abonnes(self):
        UserFollows.objects.create(user=self.a, followed_user=self.b)
        c = User.objects.create_user('c', password='x')
        UserFollows.objects.create(user=c, followed_user=self.a)
        r = self.client.get(reverse('follows'))
        self.assertEqual([f.followed_user for f in r.context['following']], [self.b])
        self.assertEqual([f.user for f in r.context['followers']], [c])

    def test_desabonnement_en_post_uniquement(self):
        f = UserFollows.objects.create(user=self.a, followed_user=self.b)
        self.assertEqual(self.client.get(reverse('unfollow', args=[f.pk])).status_code, 405)
        self.assertTrue(UserFollows.objects.filter(pk=f.pk).exists())
        r = self.client.post(reverse('unfollow', args=[f.pk]))
        self.assertRedirects(r, reverse('follows'))
        self.assertFalse(UserFollows.objects.filter(pk=f.pk).exists())

    def test_on_ne_supprime_pas_l_abonnement_d_un_autre(self):
        c = User.objects.create_user('c', password='x')
        f = UserFollows.objects.create(user=self.b, followed_user=c)
        self.assertEqual(self.client.post(reverse('unfollow', args=[f.pk])).status_code, 404)
        self.assertTrue(UserFollows.objects.filter(pk=f.pk).exists())
