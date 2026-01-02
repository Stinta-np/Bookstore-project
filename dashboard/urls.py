from django.urls import path
from . import views
from .views import dashboard

app_name='dashboard'

urlpatterns=[
    path('',views.dashboard_home,name='home'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('users/',views.users_list,name='dashboard_users'),
    path('books/',views.books_list,name='dashboard_books'),
    path('reports/sales/',views.sales_report,name='sales_report'),
]