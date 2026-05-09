from wishlist.models import Wishlist
from orders.models import OrderItem
from books.models import Book
from django.db.models import Sum
from django.contrib.auth.models import User


# 📌 1. RELATED BOOKS (Same category)

def related_books_by_category(book):
    return (
        Book.objects
        .filter(categories__in=book.categories.all())
        .exclude(id=book.id)
        .distinct()
    )



# ❤️ 2. WISHLIST BASED RECOMMENDATIONS
def wishlist_recommendations(user):
    # Get books in user's wishlist
    wishlist_books = Wishlist.objects.filter(user=user).values_list('book_id', flat=True)
    
    if not wishlist_books:
        # If no wishlist, return random books
        return Book.objects.filter(stock__gt=0).order_by('?')[:6]
    
    # Get categories from wishlist books
    wishlist_categories = Book.objects.filter(
        id__in=wishlist_books
    ).values_list('category', flat=True).distinct()
    
    # Get recommendations from same categories, excluding wishlist books
    recommendations = Book.objects.filter(
        category__in=wishlist_categories,
        stock__gt=0
    ).exclude(id__in=wishlist_books).order_by('?')[:6]
    
    # If not enough recommendations, add random books
    if recommendations.count() < 6:
        additional = Book.objects.filter(
            stock__gt=0
        ).exclude(
            id__in=list(wishlist_books) + list(recommendations.values_list('id', flat=True))
        ).order_by('?')[:6 - recommendations.count()]
        
        recommendations = list(recommendations) + list(additional)
    
    return recommendations


# 🛒 3. ORDER BASED RECOMMENDATIONS
def order_based_recommendations(user):
    purchased_categories = OrderItem.objects.filter(
        order__user=user
    ).values_list('book__category', flat=True)

    return Book.objects.filter(
        category__in=purchased_categories
    ).distinct()[:6]


# 🔥 4. BEST SELLERS
def best_seller_books():
    best_sellers = (
        OrderItem.objects
        .values('book')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:5]
    )

    book_ids = [item['book'] for item in best_sellers]
    return Book.objects.filter(id__in=book_ids)

