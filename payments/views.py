import razorpay
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from orders.models import Order
from django.conf import settings
import json
import hmac
import hashlib
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


@login_required
def start_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    razorpay_order = client.order.create({
        "amount": int(order.total_amount * 100),
        "currency": "INR",
        "payment_capture": "1"
    })

    order.razorpay_order_id = razorpay_order["id"]
    order.save()

    return render(request, "payments/pay.html", {
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "order": order,
        "amount": int(order.total_amount * 100),
    })

@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        razorpay_order_id = request.POST.get("razorpay_order_id")
        razorpay_payment_id = request.POST.get("razorpay_payment_id")
        razorpay_signature = request.POST.get("razorpay_signature")

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            })
        except razorpay.errors.SignatureVerificationError:
            return HttpResponse("Payment verification failed", status=400)

        order = Order.objects.get(razorpay_order_id=razorpay_order_id)
        order.is_paid = True
        order.save()

        return redirect("orders:order_success", order_id=order.id)

@csrf_exempt
def razorpay_webhook(request):
    payload = request.body
    signature = request.headers.get('X-Razorpay-Signature')

    generated_signature = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if generated_signature != signature:
        return HttpResponse(status=400)

    data = json.loads(payload)

    if data['event'] == 'payment.captured':
        razorpay_order_id = data['payload']['payment']['entity']['order_id']
        order = Order.objects.get(razorpay_order_id=razorpay_order_id)
        order.is_paid = True
        order.save()

    return HttpResponse(status=200)
