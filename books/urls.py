from django.urls import path
from . import views   

app_name = 'books'

urlpatterns = [
    path('',views.home, name='home'),
    path('list/', views.book_list, name='book_list'),
    path('detail/<int:book_id>/', views.book_detail, name='detail'),
    path("search/", views.search_books, name="book_search"),
    path("autosuggest/", views.autosuggest, name="book_autosuggest"),
    path("cart/", views.view_cart, name="view_cart"),
    path("apply-coupon/",views.apply_coupon, name="apply_coupon"),
    path("add-to-cart/<int:book_id>/", views.add_to_cart, name="add_to_cart"),
    path("increase/<int:book_id>/", views.increase_quantity, name="increase_quantity"),
    path("decrease/<int:book_id>/", views.decrease_quantity, name="decrease_quantity"),
    path('remove-from-cart/<int:book_id>/', views.remove_from_cart, name='remove_from_cart'),
]

