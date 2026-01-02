from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from books.models import Book
from .models import Wishlist
from django.http import JsonResponse
from django.contrib.auth.models import User

@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('book')
    return render(request, 'wishlist/wishlist.html', {'items': items})


@login_required
def add_to_wishlist(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    Wishlist.objects.get_or_create(user=request.user, book=book)
    return redirect('wishlist:view')


@login_required
def remove_from_wishlist(request, book_id):
    Wishlist.objects.filter(user=request.user, book_id=book_id).delete()
    return redirect('wishlist:view')


@login_required
def toggle_wishlist(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        book=book
    )

    if not created:
        # Already existed, so remove it
        wishlist_item.delete()
        
        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "status": "removed",
                "message": "Removed from wishlist"
            })
        # Regular request - redirect back
        return redirect(request.META.get('HTTP_REFERER', 'wishlist:view'))

    # Just created - added to wishlist
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            "status": "added",
            "message": "Added to wishlist"
        })
    # Regular request - redirect back
    return redirect(request.META.get('HTTP_REFERER', 'wishlist:view'))

@login_required
def my_wishlist(request):
    items = Wishlist.objects.filter(user=request.user)
    return render(request, "wishlist/wishlist.html", {"items": items})

def public_wishlist(request, username):
    user = get_object_or_404(User, username=username)
    items = Wishlist.objects.filter(user=user, is_public=True)

    return render(
        request,
        "wishlist/public_wishlist.html",
        {"wishlist_user": user, "items": items}
    )

@login_required
def toggle_visibility(request, wishlist_id):
    item = get_object_or_404(
        Wishlist,
        id=wishlist_id,
        user=request.user
    )
    item.is_public = not item.is_public
    item.save()
    return redirect("wishlist:view")
