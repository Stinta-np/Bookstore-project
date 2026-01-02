from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchVector
from books.models import Book

class Command(BaseCommand):
    help = "Populate search_vector for books"

    def handle(self, *args, **kwargs):
        Book.objects.update(
            search_vector=(
                SearchVector('title', weight='A') +
                SearchVector('description', weight='B') +
                SearchVector('language', weight='C')
            )
        )
        self.stdout.write(self.style.SUCCESS("Search vectors updated"))
