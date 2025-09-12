#cart/urls.py
from django.urls import path
from . import views



urlpatterns = [
    path('add/<int:product_id>/<int:variant_id>/', views.add_to_cart, name='add_to_cart'),
    path('buy-now/<slug:slug>/<int:color_id>/<str:size>/', views.buy_now, name='buy_now'),
    path('', views.view_cart, name='view_cart'),
    path('update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
]
