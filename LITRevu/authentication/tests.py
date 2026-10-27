from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()
PWD = 'Mdp-solide-4242'


class AuthFlowTests(TestCase):
    def test_modele_personnalise(self):
        self.assertEqual(User._meta.label, 'authentication.User')

    def test_pages_publiques(self):
        for name in ('login', 'signup'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_accueil_protege(self):
        r = self.client.get(reverse('home'))
        self.assertRedirects(r, f"{reverse('login')}?next={reverse('home')}")

    def test_inscription_connecte_et_redirige(self):
        r = self.client.post(reverse('signup'), {
            'username': 'rachelle', 'email': 'r@ex.fr',
            'password1': PWD, 'password2': PWD})
        self.assertRedirects(r, reverse('home'))
        self.assertTrue(User.objects.filter(username='rachelle').exists())

    def test_connexion_deconnexion(self):
        User.objects.create_user('rachelle', password=PWD)
        r = self.client.post(reverse('login'), {'username': 'rachelle', 'password': PWD})
        self.assertRedirects(r, reverse('home'))
        r = self.client.post(reverse('logout'))
        self.assertRedirects(r, reverse('login'))

    def test_mauvais_mot_de_passe(self):
        User.objects.create_user('rachelle', password=PWD)
        r = self.client.post(reverse('login'), {'username': 'rachelle', 'password': 'x'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'role="alert"')

    def test_admin(self):
        User.objects.create_superuser('admin', 'a@ex.fr', PWD)
        self.client.login(username='admin', password=PWD)
        self.assertEqual(self.client.get('/admin/authentication/user/').status_code, 200)
