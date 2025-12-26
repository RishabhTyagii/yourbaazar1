
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from product.models import category, subcategory, product_type, product
from django.shortcuts import get_object_or_404, render
app_name = "basicinfo"
urlpatterns = [
    # path('contact_us/', views.nextpage, name='nextpage'),
    path('contact_us/', views.contactus, name='contactus'),
path('ajax/footer/', views.footer_data, name='footer_data'),
    path('ajax/navbar/', views.ajax_navbar, name='ajax_navbar'),
     path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),
path('contact-queries/', views.contact_query_list, name='contact_query_list'),
    path('toggle-query-status/', views.toggle_query_status, name='toggle_query_status'),
     path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
      path('about_us/', views.about_us, name='about_us'),
# path('contact_success/', views.contactus, name='contact_success'),  # Added success page URL
  path('dashboard/', views.sales_dashboard, name='sales_dashboard'),
    path('get-sales-data/', views.get_sales_data, name='get_sales_data'),
    path('profit-analysis/', views.profit_analysis_view, name='profit_analysis'),

   path('festival-slides/', views.festival_slides_view, name='festival_slides'),

            path('deliveryinfo/', views.deliveryinfo, name='deliveryinfo'),

    ]
