from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("start/<int:order_id>/", views.start_payment, name="start_payment"),
    path("success/", views.payment_success, name="success"),
    path('webhook/',views.razorpay_webhook,name='razorpay_webhook'),
]

