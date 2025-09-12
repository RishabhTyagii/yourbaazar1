from django.urls import path
from . import views

app_name = "wallet"

urlpatterns = [
    path('dashboard/', views.wallet_dashboard, name='wallet_dashboard'),
    path('withdraw/', views.withdrawal_request_view, name='withdraw_request'),
    # Admin
    path('admin/transactions/', views.admin_transactions, name='admin_transactions'),
      path("admin/withdrawal/approve/<int:wr_id>/", views.admin_approve_withdrawal, name="admin_approve_withdrawal"),
    path("admin/withdrawal/reject/<int:wr_id>/", views.admin_reject_withdrawal, name="admin_reject_withdrawal"),

]
