from django.shortcuts import render, redirect
from django.contrib.auth import login,logout
from django.contrib.auth.forms import UserCreationForm
from recommendations.utils import wishlist_recommendations

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'users/signup.html', {'form': form})

def profile(request):
    recommended = wishlist_recommendations(request.user)

    return render(request, 'users/profile.html', {
        'recommended': recommended
    })
def logout_view(request):
    logout(request)
    return redirect ("home")