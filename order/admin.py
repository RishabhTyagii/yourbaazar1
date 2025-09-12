from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .models import *
from django.utils.html import format_html

User = get_user_model()

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'variant', 'quantity', 'price', 'get_total_price')
    fields = ('product', 'variant', 'quantity', 'price', 'is_free', 'get_total_price')
    
    def get_total_price(self, obj):
        return obj.get_total_price()
    get_total_price.short_description = 'Total Price'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number',
        'customer_name',
        'user',
        'total_amount',
        'status',
        'payment_method',
        'shipping_cost',
        'created_at',
        'print_links'
    )
    list_filter = (
        'status', 
        'payment_method', 
        'created_at',
        'shipping_city'
    )
    search_fields = (
        'order_number',
        'tracking_id',
        'customer_name',
        'customer_email',
        'customer_phone',
        'user__username'
    )
    readonly_fields = (
        'order_number',
        'tracking_id',
        'created_at',
        'updated_at',
        'subtotal',
        'shipping_cost',
        'discount_amount',
        'total_amount'
    )
    fieldsets = (
        ('Order Information', {
            'fields': (
                'order_number',
                'tracking_id',
                'status',
                'created_at',
                'updated_at'
            )
        }),
        ('Customer Information', {
            'fields': (
                'user',
                'customer_name',
                'customer_email',
                'customer_phone'
            )
        }),
        ('Shipping Information', {
            'fields': (
                'shipping_address',
                'shipping_city',
                'shipping_state',
                'shipping_pin_code',
                'shipping_country'
            )
        }),
        ('Payment Information', {
            'fields': (
                'payment_method',
                'payment_status',
                'payment_id'
            )
        }),
        ('Financial Information', {
            'fields': (
                'subtotal',
                'shipping_cost',
                'discount_amount',
                'total_amount'
            )
        }),
        ('Shipping Details', {
            'fields': (
                'shipping_provider',
                'awb_code',
                'courier_name',
                'tracking_url'
            )
        }),
        ('Metadata', {
            'fields': (
                'notes',
                'ip_address'
            ),
            'classes': ('collapse',)
        })
    )
    inlines = [OrderItemInline]

    def print_links(self, obj):
        return format_html(
            '<a href="/admin/invoice/{}/" target="_blank" class="button">🧾 Invoice</a>&nbsp;'
            '<a href="/order/receipt/{}/" target="_blank" class="button">🚚 Delivery</a>',
            obj.id, obj.id
        )
    print_links.short_description = 'Documents'
    print_links.allow_tags = True

class OrderInline(admin.TabularInline):
    model = Order
    extra = 0
    readonly_fields = ('order_number', 'total_amount', 'status', 'created_at', 'shipping_cost')
    fields = ('order_number', 'total_amount', 'shipping_cost', 'status', 'created_at')
    
    def print_links(self, obj):
        return format_html(
            '<a href="/admin/order/order/{}/change/">View</a>',
            obj.id
        )
    print_links.short_description = 'Actions'

class CustomUserAdmin(UserAdmin):
    inlines = [OrderInline]

# Only modify User admin if it's the default User model
if User == get_user_model():
    if admin.site.is_registered(User):
        admin.site.unregister(User)
    admin.site.register(User, CustomUserAdmin)

@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'order', 'order_item', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['order__order_number', 'user__username']


