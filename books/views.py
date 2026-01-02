from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.db.models import F, Sum
from discounts.models import Coupon
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.postgres.search import SearchQuery, SearchRank

from .models import Book, Category
from .serializers import BookSerializer

from orders.models import OrderItem
from wishlist.models import Wishlist
from recommendations.utils import related_books_by_category

from reviews.forms import ReviewForm
from django.db.models import Avg
from django.contrib.auth.decorators import login_required
from .models import CartItem,Book

# -----------------------------
# HOME PAGE
# -----------------------------
def home(request):
    featured_books = Book.objects.all()[:8]

    best_sellers = (
        OrderItem.objects
        .values('book')
        .annotate(total=Sum('quantity'))
        .order_by('-total')[:8]
    )

    best_seller_books = Book.objects.filter(
        id__in=[item['book'] for item in best_sellers]
    )

    return render(request, 'books/home.html', {
        'featured_books': featured_books,
        'best_sellers': best_seller_books
    })


# -----------------------------
# BOOK LIST + FILTER + SEARCH
# -----------------------------
def book_list(request):
    books = Book.objects.all().order_by('-created_at')

    q = request.GET.get('q', '')
    price_min = request.GET.get('price_min')
    category = request.GET.get('category')

    if q:
        books = books.filter(
            title__icontains=q
        ) | books.filter(
            authors__name__icontains=q
        )
        books = books.distinct()
    

    if price_min and price_min.isdigit():
        books = books.filter(price__gte=int(price_min))

    if category:
        books = books.filter(categories__slug=category)
    for book in books:
        if not book.image:
            book.temp_image = f'https://picsum.photos/seed/{book.id}/300/440'
    
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    return render(request, 'books/book_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'q': q,
        'selected_category': category,
        'books': books,
    })


# -----------------------------
# BOOK DETAIL PAGE
# -----------------------------
def book_detail(request,book_id):
    book = get_object_or_404(Book,id =book_id)

    # increase view count
    book.views += 1
    book.save()

    # -----------------------------
    # Recently viewed (session)
    # -----------------------------
    viewed = request.session.get("recently_viewed", [])

    if book.id in viewed:
        viewed.remove(book.id)

    viewed.insert(0, book.id)
    request.session["recently_viewed"] = viewed[:5]

    recently_viewed_books = (
        Book.objects
        .filter(id__in=viewed)
        .exclude(id=book.id)
    )

    # -----------------------------
    # Similar + Related books
    # -----------------------------
    similar_books = (
        Book.objects
        .filter(categories__in=book.categories.all())
        .exclude(id=book.id)
        .distinct()[:6]
    )

    related = related_books_by_category(book)

    # -----------------------------
    # Wishlist check
    # -----------------------------
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(
            user=request.user,
            book=book
        ).exists()

    # reviews = book.reviews.select_related('user')

    # ----------------------------
    # Review
    # -----------------------------
    reviews = book.reviews.all()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    review_form = ReviewForm()

    return render(request, "books/detail.html", {
        "book": book,
        "similar_books": similar_books,
        "related": related,
        "recently_viewed_books": recently_viewed_books,
        "in_wishlist": in_wishlist,
        "reviews":reviews,
        "avg_rating":avg_rating,
        "review_form":review_form,
    })
    
# -----------------------------
# SEARCH API
# -----------------------------
@api_view(['GET'])
def search_books(request):
    q = request.GET.get("q", "").strip()
    min_price = request.GET.get("price_min")
    max_price = request.GET.get("price_max")
    rating = request.GET.get("rating")
    category = request.GET.get("category")

    books = Book.objects.all()

    if q:
        search_query = SearchQuery(q)
        books = (
            books
            .annotate(rank=SearchRank(F('search_vector'), search_query))
            .filter(search_vector=search_query)
            .order_by('-rank')
        )

    if min_price:
        books = books.filter(price__gte=min_price)

    if max_price:
        books = books.filter(price__lte=max_price)

    if rating:
        books = books.filter(rating__gte=rating)

    if category:
        books = books.filter(categories__slug=category)

    serializer = BookSerializer(books.distinct(), many=True)
    return Response(serializer.data)


# -----------------------------
# AUTOSUGGEST API
# -----------------------------
@api_view(['GET'])
def autosuggest(request):
    q = request.GET.get("q", "")

    if len(q) < 2:
        return Response([])

    titles = (
        Book.objects
        .filter(title__icontains=q)
        .values_list("title", flat=True)
        .distinct()[:7]
    )

    return Response(list(titles))


# -----------------------------
# CART
# -----------------------------

@require_POST
def add_to_cart(request, book_id):
    cart = request.session.get("cart", {})
    cart[str(book_id)] = cart.get(str(book_id), 0) + 1
    request.session["cart"] = cart
    return redirect("books:view_cart")


def view_cart(request):
    cart = request.session.get("cart", {})
    books = Book.objects.filter(id__in=cart.keys())

    cart_items = []
    subtotal = 0

    for book in books:
        qty = cart[str(book.id)]
        # Use discounted_price() method if discount exists
        price = book.discounted_price() if book.discount_percent > 0 else book.price
        item_total = price * qty
        subtotal += item_total
        cart_items.append({
            "book": book,
            "qty": qty,
            "subtotal": item_total,
        })

    discount = 0
    coupon = None

    coupon_id = request.session.get("coupon_id")
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, active=True)
            discount = (subtotal * coupon.discount_percent) / 100
        except Coupon.DoesNotExist:
            pass

    total = subtotal - discount

    return render(request, "books/cart.html", {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "discount": discount,
        "total": total,
        "coupon": coupon,
    })


def remove_from_cart(request, book_id):
    cart = request.session.get('cart', {})

    if str(book_id) in cart:
        del cart[str(book_id)]

    request.session['cart'] = cart
    return redirect("books:view_cart")


@require_POST
def increase_quantity(request, book_id):
    """Increase quantity in session-based cart"""
    cart = request.session.get("cart", {})
    book_id_str = str(book_id)
    
    if book_id_str in cart:
        cart[book_id_str] += 1
        request.session["cart"] = cart
        request.session.modified = True
    
    return redirect("books:view_cart")


@require_POST
def decrease_quantity(request, book_id):
    """Decrease quantity in session-based cart"""
    cart = request.session.get("cart", {})
    book_id_str = str(book_id)
    
    if book_id_str in cart:
        if cart[book_id_str] > 1:
            cart[book_id_str] -= 1
        else:
            # Remove item if quantity becomes 0
            del cart[book_id_str]
        
        request.session["cart"] = cart
        request.session.modified = True
    
    return redirect("books:view_cart")


def apply_coupon(request):
    code = request.POST.get("coupon")
    
    # Calculate cart total from session
    cart = request.session.get("cart", {})
    books = Book.objects.filter(id__in=cart.keys())
    
    cart_total = 0
    for book in books:
        qty = cart[str(book.id)]
        price = book.discounted_price() if book.discount_percent > 0 else book.price
        cart_total += price * qty

    try:
        coupon = Coupon.objects.get(code__iexact=code, active=True)
        if coupon.is_valid(cart_total):
            request.session["coupon_id"] = coupon.id
            # Clear any error messages
            if "coupon_error" in request.session:
                del request.session["coupon_error"]
        else:
            request.session["coupon_error"] = "Coupon not valid for this order amount"
            if "coupon_id" in request.session:
                del request.session["coupon_id"]
    except Coupon.DoesNotExist:
        request.session["coupon_error"] = "Invalid coupon code"
        if "coupon_id" in request.session:
            del request.session["coupon_id"]

    return redirect("books:view_cart")