from django.urls import path
from . import views

app_name = "seller_products"

urlpatterns = [
    # Seller-facing
    path('drafts/', views.seller_draft_list, name='draft_list'),
    path('drafts/create/', views.seller_draft_create, name='draft_create'),
    path('drafts/<int:draft_id>/', views.seller_draft_detail, name='draft_detail'),
    path('drafts/<int:draft_id>/delete/', views.seller_draft_delete, name='draft_delete'),
    path("ajax/load-subcategories/", views.load_subcategories, name="ajax_load_subcategories"),
    path("ajax/load-product-types/", views.load_product_types, name="ajax_load_product_types"),
    # Seller product management
    path("products/", views.seller_product_list, name="product_list"),
     path('detail/<int:product_id>/', views.seller_product_detail, name='product_detail'),
    path("reviews/<int:product_id>/", views.seller_product_reviews, name="product_reviews"),
    path("products/<int:product_id>/edit/", views.seller_product_edit, name="product_edit"),
    # path(' seller_product_reviews/', views.seller_product_reviews, name='product_reviews'),
    # Admin-facing actions
    path('admin/drafts/', views.admin_draft_list, name='admin_draft_list'),
    path('admin/drafts/<int:draft_id>/', views.admin_draft_detail, name='admin_draft_detail'),
    path('admin/drafts/<int:draft_id>/approve/', views.admin_draft_approve, name='admin_draft_approve'),
    path('admin/drafts/<int:draft_id>/reject/', views.admin_draft_reject, name='admin_draft_reject'),
     # Admin-facing: Seller-wise Orders
    path('admin/seller-orders/', views.admin_seller_orders, name='admin_seller_orders'),
    path('admin/seller-orders/update-status/', views.admin_order_status_update, name='admin_order_status_update'),
    path('admin/seller-orders/<int:order_id>/seller/<int:seller_id>/', views.admin_seller_order_detail, name='admin_seller_order_detail'),
]
