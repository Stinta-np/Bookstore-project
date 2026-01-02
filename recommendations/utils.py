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
def wishlist_recommendations(user, limit=6):
    user_books = Wishlist.objects.filter(user=user)\
                                 .values_list("book_id", flat=True)

    similar_users = Wishlist.objects.filter(
        book_id__in=user_books
    ).exclude(user=user).values_list("user_id", flat=True)

    recommended_books = Book.objects.filter(
        wishlisted_by__user_id__in=similar_users
    ).exclude(id__in=user_books).distinct()[:limit]

    return recommended_books



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

