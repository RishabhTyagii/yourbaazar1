from django.contrib import admin
from .models import SellerTestimonial

@admin.register(SellerTestimonial)
class SellerTestimonialAdmin(admin.ModelAdmin):
    list_display = ("seller", "display_name", "business_name", "rating", "is_approved", "created_at")
    list_filter = ("is_approved", "rating", "created_at")
    search_fields = ("seller__username", "display_name", "business_name", "experience")
    autocomplete_fields = ("seller",)