from django.urls import path
from . import views
from .views import toggle_wishlist

app_name = 'wishlist'

urlpatterns = [
    path('wishlist/',views.wishlist_view, name='view'),
    path('add/<int:book_id>/', views.add_to_wishlist, name='add'),
    path('remove/<int:book_id>/', views.remove_from_wishlist, name='remove'),
    path('toggle/<int:book_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('my/',views.my_wishlist,name='my'),
    path("public/<str:username>/", views.public_wishlist, name="public"),
    path("visibility/<int:wishlist_id>/",views.toggle_visibility,name="toggle_visibility"),

]