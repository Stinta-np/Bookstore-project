from django.db import models
from django.urls import reverse
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg
from django.contrib.auth.models import User

# Create your models here.
class Author(models.Model):
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=520, unique=True)
    authors = models.ManyToManyField(Author, related_name='books')
    categories = models.ManyToManyField(Category, related_name='books', blank=True)
    description = models.TextField(blank=True)
    language = models.CharField(max_length=50, default='English')
    published_year = models.IntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    stock = models.IntegerField(default=0)
    rating = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    discount_percent = models.IntegerField(default=0)
    search_vector = SearchVectorField(null=True,editable=False)
    views = models.IntegerField(default=0)
    image = models.ImageField(upload_to="books/",blank=True,null=True)
    class Meta:
        indexes = [
            GinIndex(fields=['search_vector']),
        ]


    def get_absolute_url(self):
        return reverse('books:detail', kwargs={'book_id': self.id})
    
    def discounted_price(self):
        if self.discount_percent > 0:
            return self.price - (self.price * self.discount_percent / 100)
        return self.price

    def __str__(self):
        return self.title
    
@receiver(post_save, sender=Book)
def update_book_search_vector(sender, instance, **kwargs):
    Book.objects.filter(pk=instance.pk).update(
        search_vector=(
            SearchVector('title', weight='A') +
            SearchVector('description', weight='B')
        )
    )

@property
def discounted_price(self):
    return self.price - (self.price * self.discount_percent / 100)

from django.db.models import Avg

@property
def average_rating(self):
    return self.reviews.aggregate(
        Avg('rating')
    )['rating__avg'] or 0

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.book.price * self.quantity
