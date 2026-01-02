from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'orders'

urlpatterns = [
    path("", lambda request: redirect("orders:my_orders"), name="orders_home"),
    path('checkout/', views.checkout, name='checkout'),
    path("place/", views.place_order, name="place_order"),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('success/<int:order_id>/', views.order_success, name='success'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),

]
