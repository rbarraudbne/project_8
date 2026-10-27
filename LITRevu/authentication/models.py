from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Utilisateur personnalisé.

    On part d'AbstractUser pour garder username, mot de passe, e-mail, etc.
    Les champs spécifiques au projet (rôle, photo...) se rajoutent ici plus tard.
    """

    def __str__(self):
        return self.username
