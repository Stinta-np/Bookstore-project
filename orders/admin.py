from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('book', 'quantity', 'price', 'subtotal')
    
    def subtotal(self, obj):
        return obj.subtotal
    subtotal.short_description = 'Subtotal'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'user', 
        'full_name',
        'total_amount', 
        'status', 
        'paid',
        'created_at'
    ]
    list_filter = ['status', 'paid', 'created_at']
    search_fields = ['id', 'user__username', 'full_name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('user', 'status', 'paid')
        }),
        ('Delivery Address', {
            'fields': ('full_name', 'phone', 'email', 'address_line1', 'address_line2', 'city', 'state', 'pincode')
        }),
        ('Payment Details', {
            'fields': ('total_amount', 'discount_amount', 'coupon', 'payment_method')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'book', 'quantity', 'price', 'subtotal']
    list_filter = ['order__status']
    
    def subtotal(self, obj):
        return obj.subtotal
    subtotal.short_description = 'Subtotal'