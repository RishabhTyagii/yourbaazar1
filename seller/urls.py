# app/urls.py
from django.urls import path
from . import views
app_name = 'seller'
urlpatterns = [
        path('', views.mainpage, name='mainpage'),

    path("seller/", views.seller_landing, name="seller_landing"),
    path("seller/register/", views.seller_register, name="seller_register"),
    path("seller/verify-otp/", views.verify_otp, name="verify_otp"),
    path("seller/resend-otp/", views.resend_otp, name="resend_otp"),
    path("seller/login/", views.seller_login, name="seller_login"),
    path("seller/logout/", views.seller_logout, name="seller_logout"),
    path("seller/product_list/", views.product_list, name="product_list"),
    path("seller/add_product/", views.add_product, name="add_product"),
    path("admin-panel/sellers/", views.admin_seller_list, name="admin_seller_list"),
    path("admin-panel/sellers/<int:seller_id>/approve/", views.admin_approve_seller, name="admin_approve_seller"),
    path("seller/view-profile/", views.view_profile, name="view_profile"),
    path("seller/edit-profile/", views.edit_profile, name="edit_profile"),
    # Seller-facing Orders
    path("seller/orders/", views.seller_order_list, name="seller_order_list"),
    path("seller/orders/<int:order_id>/", views.seller_order_detail, name="seller_order_detail"),
    path("seller/notifications/", views.seller_notifications, name="seller_notifications"),
    path("notifications/mark-all/", views.mark_all_read, name="seller_mark_all_read"),
    path("notifications/<int:pk>/toggle/", views.toggle_read, name="seller_toggle_notification"),
    path("notifications/<int:pk>/delete/", views.delete_notification, name="seller_delete_notification"),
    # Forgot password flow
    path("seller/forgot-password/", views.forgot_password_request, name="forgot_password_request"),
    path("seller/forgot-password/verify-otp/", views.forgot_password_verify_otp, name="forgot_password_verify_otp"),
    path("seller/forgot-password/reset/", views.forgot_password_reset, name="forgot_password_reset"),
    path("seller/forgot-password/resend-otp/", views.forgot_password_resend_otp, name="forgot_password_resend_otp"),
    # change credentials 
    path("credentials/request/", views.request_update_credentials, name="request_update_credentials"),
    path("credentials/verify-otp/", views.verify_update_otp, name="verify_update_otp"),
    path("credentials/update/", views.update_credentials, name="update_credentials"),
    # invoice
    path('orders/<int:order_id>/invoice/', views.seller_order_invoice, name='seller_order_invoice'),
    # admin facing
     path("sellers/", views.seller_list_admin, name="seller_list_admin"),
     path("sellers/<int:seller_id>/", views.admin_seller_detail, name="admin_seller_detail"),
   
    
    
]
