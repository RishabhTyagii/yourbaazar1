from django.contrib import admin

# Register your models here.
from .models import SellerDraft, Seller, Product
@admin.register(SellerDraft)
class SellerDraftAdmin(admin.ModelAdmin):   
    list_display = ('email', 'username', 'business_name', 'created_at')
    search_fields = ('email', 'username', 'business_name')
    list_filter = ('created_at',)
@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'business_name', 'is_approved', 'created_at')
    search_fields = ('email', 'username', 'business_name')
    list_filter = ('is_approved', 'created_at')
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):   
    list_display = ('name', 'sku', 'price', 'stock', 'seller', 'created_at')
    search_fields = ('name', 'sku', 'seller__username')
    list_filter = ('created_at', 'seller')
    raw_id_fields = ('seller',)
