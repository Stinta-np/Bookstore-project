from django.urls import path
from . import views

urlpatterns = [
    path('', views.recommendations_home, name='recommendations_home'),
]
