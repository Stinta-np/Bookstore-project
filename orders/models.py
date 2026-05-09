from django.db import models
from django.contrib.auth.models import User
from books.models import Book
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from discounts.models import Coupon


class Order(models.Model):
    STATUS_CHOICES = [
        ('PLACED', 'Order Placed'),
        ('PACKED', 'Packed'),
        ('SHIPPED', 'Shipped'),
        ('OUT', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # User & Basic Info
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    
    # Delivery Address - WITH DEFAULTS
    full_name = models.CharField(max_length=200, default='Guest')
    phone = models.CharField(max_length=15, default='0000000000')
    email = models.EmailField(default='noreply@bookstore.com')
    address_line1 = models.CharField(max_length=500, default='Not Provided')
    address_line2 = models.CharField(max_length=500, blank=True, default='')
    city = models.CharField(max_length=100, default='Unknown')
    state = models.CharField(max_length=100, default='Unknown')
    pincode = models.CharField(max_length=6, default='000000')
    
    # Order Details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    
    # Payment & Status
    payment_method = models.CharField(max_length=20, default='cod')
    paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLACED')
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity} x {self.book.title}"
    
    @property
    def subtotal(self):
        return self.price * self.quantity

@receiver(post_save, sender=Order)
def order_status_email(sender, instance, created, **kwargs):
    if not created:
        send_mail(
            f'Order #{instance.id} Update',
            f'Your order status is now {instance.get_status_display()}',
            settings.EMAIL_HOST_USER,
            [instance.user.email],
            fail_silently=True
        )
