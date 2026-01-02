from django.urls import path
from . import views

urlpatterns = [
    path('', views.available_discounts, name='discount_list'),
]
