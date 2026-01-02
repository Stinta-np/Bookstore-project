from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from books.models import Book
from .models import Review
from .forms import ReviewForm

@login_required
def add_review(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    # prevent duplicate review
    if Review.objects.filter(user=request.user, book=book).exists():
        return redirect('books:detail', book_id=book.id)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.book = book
            review.save()

    return redirect('books:detail', book_id=book.id)