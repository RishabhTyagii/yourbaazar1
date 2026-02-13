# seller_products/admin.py
from django.contrib import admin
import nested_admin

from .models import SellerProductDraft, DraftColor, DraftVariant, SellerProductMeta
from .forms import SellerProductDraftAdminForm  # ✅ DAL autocomplete form

# ----- Inlines -----
class DraftVariantInline(nested_admin.NestedTabularInline):
    model = DraftVariant
    extra = 0

class DraftColorInline(nested_admin.NestedStackedInline):
    model = DraftColor
    inlines = [DraftVariantInline]
    extra = 0

# ----- Draft Admin -----
@admin.register(SellerProductDraft)
class SellerProductDraftAdmin(nested_admin.NestedModelAdmin):
    form = SellerProductDraftAdminForm  # 🔥 cascading dropdown enable
    list_display = ('id', 'name', 'sku', 'seller', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'sku', 'seller__username', 'seller__email')
    inlines = [DraftColorInline]
    readonly_fields = ('approved_product',)

# ----- Meta Admin -----
@admin.register(SellerProductMeta)
class SellerProductMetaAdmin(admin.ModelAdmin):
    list_display = ('product', 'seller', 'shipping_by', 'payment_mode', 'minimum_shipping')
    search_fields = ('product__name', 'seller__username', 'seller__email')
    list_filter = ('shipping_by', 'payment_mode')
