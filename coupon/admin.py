from django.contrib import admin
from .models import Coupon, CouponUsage,AutoRewardRule

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'type', 'discount_value', 'times_used', 'valid_from', 'valid_to', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('code',)

@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'coupon', 'order', 'used_at')
    list_filter = ('coupon__type', 'used_at')
    search_fields = ('user__username', 'coupon__code', 'order__id')
admin.site.register(AutoRewardRule)
