from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    path('', views.home, name='home'),
    path('connexion/', LoginView.as_view(
        template_name='authentication/login.html',
        authentication_form=LoginForm,
        redirect_authenticated_user=True), name='login'),
    path('deconnexion/', LogoutView.as_view(), name='logout'),
    path('inscription/', views.signup, name='signup'),
]
