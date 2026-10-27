from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import SignupForm


def signup(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)  # connexion automatique après inscription
        return redirect('home')
    return render(request, 'authentication/signup.html', {'form': form})


@login_required
def home(request):
    return render(request, 'home.html')
