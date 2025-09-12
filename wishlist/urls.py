from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'wishlist'

urlpatterns = [
    path('', views.view_wishlist, name='view_wishlist'),
    path('add/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove/<int:wishlist_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('move-to-cart/<int:wishlist_id>/', views.move_to_cart, name='move_to_cart'),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)