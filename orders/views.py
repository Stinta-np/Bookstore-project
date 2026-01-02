from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.timezone import now
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.styles import getSampleStyleSheet

from .models import Order
from django.core.mail import send_mail
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from books.models import Book
from .models import Order, OrderItem
from discounts.models import Coupon
from django.db.models import Sum,Count
from .utils import generate_invoice



@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.warning(request, "Your cart is empty!")
        return redirect('books:book_list')

    books = Book.objects.filter(id__in=cart.keys())
    cart_items = []
    subtotal = 0

    # Build cart items
    for book in books:
        qty = cart[str(book.id)]
        
        # Stock check
        if book.stock < qty:
            messages.error(request, f"Not enough stock for {book.title}. Available: {book.stock}")
            return redirect('books:view_cart')

        item_total = book.price * qty
        subtotal += item_total
        
        cart_items.append({
            'book': book,
            'qty': qty,
            'subtotal': item_total
        })

    # Check for coupon
    discount = 0
    coupon = None
    coupon_id = request.session.get('coupon_id')
    
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, active=True)
            discount = (subtotal * coupon.discount_percent) / 100
        except Coupon.DoesNotExist:
            pass

    total = subtotal - discount

    # Handle form submission
    if request.method == 'POST':
        # Get form data
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address_line1 = request.POST.get('address_line1')
        address_line2= request.POST.get('address_line2','')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        payment_method = request.POST.get('payment_method', 'cod')

        # Create order
        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            email=email,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            pincode=pincode,
            total_amount=total,
            discount_amount=discount,
            coupon=coupon,
            payment_method=payment_method,
            status='PLACED'
        )

        # Create order items and reduce stock
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                book=item['book'],
                quantity=item['qty'],
                price=item['book'].price
            )
            
            # Reduce stock
            item['book'].stock -= item['qty']
            item['book'].save()

        # Clear cart and coupon
        request.session['cart'] = {}
        if 'coupon_id' in request.session:
            del request.session['coupon_id']
        
        # Redirect based on payment method
        if payment_method == 'online':
            # Redirect to payment gateway (if you have one)
            return redirect('payments:start_payment', order_id=order.id)
        else:
            # COD - redirect to success page
            return redirect('orders:success', order_id=order.id)

    return render(request, 'orders/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'discount': discount,
        'total': total,
        'coupon': coupon
    })

@login_required
def my_orders(request):
    orders = (
        Order.objects
        .filter(user=request.user)
        .order_by('-created_at')
        .prefetch_related('items__book')
    )
    return render(request, 'orders/my_orders.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    items = []
    total = 0

    for item in order.items.all():
        subtotal = item.price * item.quantity
        total += subtotal
        items.append({
            'item': item,
            'subtotal': subtotal
        })

    return render(request, 'orders/order_detail.html', {
        'order': order,
        'items': items,
        'total': total
    })

@login_required
def place_order(request):
    cart = request.session.get("cart", {})

    if not cart:
        return redirect("books:view_cart")

    books = Book.objects.filter(id__in=cart.keys())

    total = 0
    for book in books:
        total += book.price * cart[str(book.id)]

    # CREATE ORDER
    order = Order.objects.create(
        user=request.user,
        total_amount=total
    )

    # CREATE ORDER ITEMS
    for book in books:
        OrderItem.objects.create(
            order=order,
            book=book,
            quantity=cart[str(book.id)],
            price=book.price
        )

    # CLEAR CART
    request.session["cart"] = {}

    # PREVENT DOUBLE SUBMIT
    request.session["order_submitted"] = True

    return redirect("orders:order_success", order_id=order.id)


@login_required
def order_success(request, order_id):
    """Order success page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Get recommended books (optional)
    from books.models import Book
    recommended_books = Book.objects.all()[:6]
    
    # Remove any email_sent checks - just render the page
    return render(request, 'orders/order_success.html', {
        'order': order,
        'recommended_books': recommended_books
    })

@login_required
def download_invoice(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    y = height - 50

    # ---------- HEADER ----------
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, y, "BookStore Invoice")
    y -= 40

    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Order ID: #{order.id}")
    y -= 20
    p.drawString(50, y, f"Customer: {order.user.username}")
    y -= 20
    p.drawString(50, y, f"Date: {order.created_at.strftime('%d %b %Y')}")
    y -= 30

    # ---------- ITEMS ----------
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Book")
    p.drawString(300, y, "Qty")
    p.drawString(350, y, "Price")
    y -= 20

    p.setFont("Helvetica", 12)

    for item in order.items.all():
        p.drawString(50, y, item.book.title[:40])
        p.drawString(300, y, str(item.quantity))
        p.drawString(350, y, f"₹{item.price}")
        y -= 20

        if y < 100:
            p.showPage()
            y = height - 50

    # ---------- TOTAL ----------
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, f"Total Amount: ₹{order.total_amount}")

    p.showPage()
    p.save()

    return response


@login_required
def download_invoice(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Invoice - Order #{order.id}", styles['Title']))
    elements.append(Paragraph(f"Customer: {order.user.username}", styles['Normal']))
    elements.append(Paragraph(f"Total: ₹{order.total_amount}", styles['Normal']))

    data = [["Book", "Qty", "Price"]]
    for item in order.items.all():
        data.append([
            item.book.title,
            item.quantity,
            f"₹{item.price}"
        ])

    table = Table(data)
    elements.append(table)

    doc.build(elements)
    return response
