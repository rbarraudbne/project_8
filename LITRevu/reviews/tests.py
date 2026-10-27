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
