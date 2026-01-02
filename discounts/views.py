from django.shortcuts import render
from django.http import HttpResponse

def available_discounts(request):
    return HttpResponse("Discounts page")
