from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from orders.models import Order
from wishlist.models import Wishlist
from books.models import Book
from django.views.decorators.http import require_POST

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

@login_required
def profile(request):
    # Get user statistics
    user_orders = Order.objects.filter(user=request.user)
    total_orders = user_orders.count()
    total_spent = sum(order.total_amount for order in user_orders)
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    
    # Get last order
    last_order = user_orders.first() if user_orders.exists() else None
    
    # Get recommendations
    try:
        from recommendations.utils import wishlist_recommendations
        recommended = wishlist_recommendations(request.user)
    except:
        # Fallback: get random books if recommendations fail
        recommended = Book.objects.filter(stock__gt=0).order_by('?')[:6]

    return render(request, 'users/profile.html', {
        'recommended': recommended,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'wishlist_count': wishlist_count,
        'last_order': last_order,
    })

@require_POST
def logout_view(request):
    logout(request)
    return redirect("books:home")