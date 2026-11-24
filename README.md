# LITRevu
 
LIT Revu est une application web Django permettant de **demander** et de **publier des critiques** de livres et d'articles, et également de suivre d'autres utilisateurs pour voir leurs publications et leurs demandent.
 
Projet OpenClassrooms : *Développez une application web en utilisant Django*.
 
## Fonctionnalités
 
- **Inscription, connexion et déconnexion** (modèle utilisateur personnalisé).
- **Billets** : demander une critique sur un livre ou un article (titre, auteur, description, image facultative). Les billets peuvent être modifiés et supprimés par leur auteur.
- **Critiques** : répondre à un billet (titre, note de 0 à 5, commentaire), ou publier une critique sans demande préalable. De même que les billets, les critiques peuvent être modifiées et supprimées par leur auteur.
- **Abonnements** : suivre un utilisateur grâce à son nom d'utilisateur, voir ses abonnements et ses abonnés, se désabonner.
- **Flux** : page d'accueil qui rassemble, du plus récent au plus ancien :
  - les billets et critiques de l'utilisateur connecté ;
  - ceux des utilisateurs qu'il suit ;
  - les critiques écrites en réponse à ses propres billets, même par des utilisateurs qu'il ne suit pas.
- **Posts** : la liste de ses propres billets et critiques, avec les actions de modification et de suppression.
## Prérequis
 
- Python 3.10 ou plus récent
- `pip`
## Installation
 
1. Récupérer le projet et se placer à sa racine (le dossier qui contient `manage.py`).
2. Créer et activer un environnement virtuel :
```bash
python -m venv venv
 
# Linux / macOS
source venv/bin/activate
 
# Windows (PowerShell)
venv\Scripts\Activate.ps1
```
 
3. Installer les dépendances :
```bash
pip install -r requirements.txt
```
 
4. Créer la base de données :
```bash
python manage.py migrate
```
 
5. (Facultatif) Créer un compte administrateur pour accéder à `/admin/` :
```bash
python manage.py createsuperuser
```
 
## Lancer le site
 
```bash
python manage.py runserver
```
 
Le site est alors disponible sur <http://127.0.0.1:8000/>.
 
| Page | URL |
|---|---|
| Flux (accueil) | `/` |
| Connexion | `/connexion/` |
| Inscription | `/inscription/` |
| Posts | `/posts/` |
| Abonnements | `/abonnements/` |
| Créer un billet (demander une critique) | `/billets/creer/` |
| Créer une critique (sans demande) | `/critiques/creer/` |
| Administration | `/admin/` |
 
Pour essayer l'application, créez plusieurs comptes via la page d'inscription, faites-les se suivre mutuellement depuis la page « Abonnements », puis publiez des billets et des critiques.
 
## Tests
 
```bash
python manage.py test
```
 
Les tests couvrent l'authentification, les modèles, les billets, les critiques, les abonnements et le flux (visibilité des publications, droits de modification et de suppression).
 
## Structure du projet
 
```
merchex/            Configuration Django (settings, urls)
authentication/     Utilisateur personnalisé, inscription, connexion
reviews/            Billets, critiques, abonnements, flux
templates/          Gabarits HTML (base, authentication/, reviews/)
static/             CSS et logo
manage.py
requirements.txt
```
 
### Modèles (`reviews/models.py`)
 
- `Ticket` : `title`, `author`, `description`, `image`, `user`, `is_request`, `time_created`
- `Review` : `ticket`, `rating` (0 à 5), `headline`, `body`, `user`, `time_created`
- `UserFollows` : `user`, `followed_user` (couple unique)
Le modèle utilisateur est `authentication.User` (`AUTH_USER_MODEL`).
 
## Choix de conception
 
- Le champ `author` (auteur du livre ou de l'article) a été ajouté à `Ticket`.
- Une critique publiée sans demande préalable crée tout de même un `Ticket`, car une critique est toujours liée à un billet. Ce billet est marqué `is_request = False` : il n'apparaît pas comme une demande de critique et personne ne peut y répondre. Il est supprimé automatiquement si la critique vient à être supprimée.
- On ne peut répondre qu'aux billets de l'utilisateur connecté ou des utilisateurs qu'il suit, et une seule fois par billet.
- Les suppressions se font uniquement par requête `POST`, et seul le propriétaire peut modifier ou supprimer ses billets et ses critiques.
## Accessibilité
 
Les pages suivent les bonnes pratiques du référentiel WCAG : langue de la page, titres explicites, champs de formulaire avec libellés, messages d'erreur annoncés aux lecteurs d'écran, contrastes suffisants, focus visible, lien d'évitement vers le contenu, textes alternatifs et liens explicites.
 
## Images téléversées
 
Les images des billets sont enregistrées dans le dossier `media/` (créé automatiquement). En développement, elles sont servies par Django lorsque `DEBUG = True`.
 
