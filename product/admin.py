#product/admin.py

from django.contrib import admin
import nested_admin
from .models import category, subcategory, product, product_type, ProductColor, ProductVariant
from .forms import ProductForm, ProductTypeForm

# Category Admin
@admin.register(category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'image')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

# Subcategory Admin
@admin.register(subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'image', 'category')
    search_fields = ('name',)
    list_filter = ('category',)
    prepopulated_fields = {'slug': ('name',)}

# ProductType Admin — no autocomplete needed here
@admin.register(product_type)
class ProductTypeAdmin(admin.ModelAdmin):
    form = ProductTypeForm  # ✅ A plain form without autocomplete widgets
    list_display = ('name', 'image', 'category', 'subcategory')
    search_fields = ('name', 'category__name', 'subcategory__name')
    list_filter = ('category', 'subcategory')
    prepopulated_fields = {'slug': ('name',)}

# Inlines for nested product color & variants
class ProductVariantInline(nested_admin.NestedTabularInline):
    model = ProductVariant
    extra = 1

class ProductColorInline(nested_admin.NestedStackedInline):
    model = ProductColor
    inlines = [ProductVariantInline]
    extra = 1

# Main Product Admin
@admin.register(product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    form = ProductForm  # ✅ Uses autocomplete for category, subcategory, product_type
    inlines = [ProductColorInline]
    list_display = ('name', 'category', 'subcategory', 'product_type')
    list_filter = ('category', 'subcategory', 'product_type')
    autocomplete_fields = ['category', 'subcategory', 'product_type']



