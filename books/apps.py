from django.apps import AppConfig


class BooksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'books'


    def ready(self):
        from django.db.models.signals import post_save
        from .models import Book
        from .signals import update_search_vector
        post_save.connect(update_search_vector, sender=Book)
