from django.db import models
from books.models import Book
from django.utils import timezone

class Discount(models.Model):
    book = models.OneToOneField(
        Book,
        on_delete=models.CASCADE,
        related_name="discount"
    )
    percent = models.PositiveIntegerField(help_text="0 to 90")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def discounted_price(self):
        return self.book.price - (self.book.price * self.percent / 100)

    def __str__(self):
        return f"{self.percent}% OFF - {self.book.title}"

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.PositiveIntegerField()
    min_order_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    def is_valid(self, total):
        now = timezone.now()
        return (
            self.active and
            self.valid_from <= now <= self.valid_to and
            total >= self.min_order_amount
        )

    def __str__(self):
        return self.code
