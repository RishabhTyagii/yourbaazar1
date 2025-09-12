# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),  # OTP verification page
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('profile/', views.view_profile, name='view_profile'), 
    path('edit-profile/', views.edit_profile, name='edit_profile'),
   path('change-password/', views.request_password_change, name='change_password_with_otp'),
path('change-password/verify/', views.verify_password_otp, name='verify_password_otp'),
path('admin-dashboard/', views.custom_admin_dashboard, name='admin_dashboard'),
]
