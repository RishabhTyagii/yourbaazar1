from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
# from .views import all_sneakers
from .views import CategoryAutocomplete, SubcategoryAutocomplete,ProductTypeAutocomplete

from product.models import category, subcategory, product_type, product
from django.shortcuts import get_object_or_404, render
app_name = "product"
urlpatterns = [
path('', views.indexpage, name='indexpage'),

path('', views.homepage_view, name='homepage_view'),
    path("check-pincode/", views.check_pincode, name="check_pincode"),
path("update-shipping/", views.update_shipping_by_pincode, name="update_shipping"),
path('ajax/search/', views.ajax_search, name='ajax_search'),

# path('all_sneakers/', all_sneakers, name='all_sneakers'),
# path('search/', views.search, name='search'),
path('categories/', views.category_list, name='category_list'),  # Moved categories here
path('categories/<int:category_id>/', views.subcategory_list, name='subcategory_list'),
path('categories/<int:category_id>/<int:subcategory_id>/', views.product_type_list, name='product_type_list'),
path('categories/<int:category_id>/<int:subcategory_id>/<int:product_type_id>/', views.product_list, name='product_list'),
# path('product/<int:product_id>/', views.product_detail, name='product_detail'),
 path('product/<int:product_id>/',views. product_detail, name='product_detail'),
 path('products/get_color_data/<int:color_id>/', views.get_color_data, name='get_color_data'),
 path('category-autocomplete/', CategoryAutocomplete.as_view(), name='category-autocomplete'),
path('subcategory-autocomplete/', SubcategoryAutocomplete.as_view(), name='subcategory-autocomplete'),
path('product-type-autocomplete/', ProductTypeAutocomplete.as_view(), name='product-type-autocomplete'),
path('sales-products/', views.all_sales_products, name='sales_products'),
# urls.py
path('collection/<str:collection_type>/', views.collection_view, name='collection_view'),


path('clear-order-success/', views.clear_order_success, name='clear_order_success'),

#inventory
   path('variant-stocks/', views.stock_list, name='variant_stock_list'),
    path('update-stock/<int:variant_id>/', views.update_stock, name='update_stock'),

   
    
]
