from django.shortcuts import render
from django.http import HttpResponse

def recommendations_home(request):
    return HttpResponse("Recommendations working")
