from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from orders.models import Order
from books.models import Book
from django.db.models.functions import TruncMonth
from django.contrib.auth.models import User

from recommendations.utils import wishlist_recommendations
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from orders.models import Order
from django.contrib.auth.models import User
from django.db.models import Sum

@staff_member_required
def dashboard_home(request):
    total_orders = Order.objects.count()
    paid_orders = Order.objects.filter(paid=True).count()
    pending_orders = Order.objects.filter(paid=False).count()
    labels=['jan','feb','mar','apr']
    values=[1200,1500,900,1800]
    total_revenue = Order.objects.filter(paid=True).aggregate(
        Sum('total_amount')
    )['total_amount__sum'] or 0
    total_users = User.objects.count()
    context = {
        'total_orders': total_orders,
        'paid_orders': paid_orders,
        'pending_orders': pending_orders,
        'total_revenue': total_revenue,
        'total_users': total_users,
        'labels': json.dumps(labels),
        'values': json.dumps(values),
    }

    return render(request, 'dashboard/home.html',context)



def users_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'dashboard/users_list.html', {
        'users': users
    })

def books_list(request):
    books = Book.objects.all().order_by('-created_at')
    return render(request, 'dashboard/books_list.html', {
        'books': books
    })

def sales_report(request):
    total_sales = Order.objects.filter(paid=True).aggregate(
        Sum('total_amount')
    )['total_amount__sum'] or 0

    total_orders = Order.objects.filter(paid=True).count()

    return render(request, 'dashboard/sales_report.html', {
        'total_sales': total_sales,
        'total_orders': total_orders,
    })

def sales_chart_data():
    return(
        Order.objects
        .filter(paid=True)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )

def dashboard(request):
    recommendations = wishlist_recommendations(request.user)
    return render(request, "dashboard/dashboard.html", {
        "recommendations": recommendations
    })
