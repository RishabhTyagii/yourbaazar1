from django.contrib import admin

# Register your models here.
from .models import NavImage, footer, social_media, contact_us,HeroImage, collection_card, shop_sale

admin.site.register(NavImage)
admin.site.register(footer)
admin.site.register(social_media)
admin.site.register(contact_us)
@admin.register(HeroImage)
class HeroImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'image', 'active', 'created_at']
    list_filter = ['active']
    search_fields = ['id']
@admin.register(collection_card)
class CollectionCardAdmin(admin.ModelAdmin):
    list_display = ['id', 'womens_heading', 'mens_heading', 'accessories_heading']
    search_fields = ['womens_heading', 'mens_heading', 'accessories_heading']
admin.site.register(shop_sale)