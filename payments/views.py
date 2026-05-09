import razorpay
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from orders.models import Order
from django.conf import settings
from django.contrib import messages
import json
import hmac
import hashlib
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


@login_required
def start_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Check if Razorpay credentials are configured
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        messages.error(request, "Payment gateway not configured. Please use COD.")
        return redirect('orders:checkout')

    try:
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        # Convert to paise for Razorpay (multiply by 100)
        amount_in_paise = int(order.total_amount * 100)

        razorpay_order = client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "payment_capture": "1"
        })

        order.razorpay_order_id = razorpay_order["id"]
        order.save()

        return render(request, "payments/pay.html", {
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "order": order,
            "amount": amount_in_paise,  # For Razorpay script (in paise)
        })
    except Exception as e:
        messages.error(request, f"Payment initialization failed: {str(e)}")
        return redirect('orders:checkout')


@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        razorpay_order_id = request.POST.get("razorpay_order_id")
        razorpay_payment_id = request.POST.get("razorpay_payment_id")
        razorpay_signature = request.POST.get("razorpay_signature")

        try:
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

            # Verify payment signature
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            })

            # Update order
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)
            order.paid = True  # Use 'paid' not 'is_paid'
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.payment_method = 'online'
            order.save()

            messages.success(request, "Payment successful!")
            return redirect("orders:success", order_id=order.id)

        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "Payment verification failed!")
            return redirect('books:book_list')
        except Order.DoesNotExist:
            messages.error(request, "Order not found!")
            return redirect('books:book_list')
    
    return redirect('books:book_list')


@csrf_exempt
def razorpay_webhook(request):
    """Handle Razorpay webhook notifications"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    payload = request.body
    signature = request.headers.get('X-Razorpay-Signature', '')

    try:
        generated_signature = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        if generated_signature != signature:
            return HttpResponse("Invalid signature", status=400)

        data = json.loads(payload)

        if data['event'] == 'payment.captured':
            razorpay_order_id = data['payload']['payment']['entity']['order_id']
            razorpay_payment_id = data['payload']['payment']['entity']['id']
            
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)
            order.paid = True
            order.razorpay_payment_id = razorpay_payment_id
            order.save()

        return HttpResponse(status=200)
    
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return HttpResponse(status=400)
