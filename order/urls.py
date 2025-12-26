from django.urls import path
from . import views

# from .views import SalesAnalysisView

from .views import OrderTrackingView, track_orders_view

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
path('order-success/<int:order_id>/', views.order_success, name='order_success'),
path('track/', track_orders_view, name='track_orders'),
    
# path("ajax/calc-shipping/", views.ajax_calculate_shipping, name="ajax_calculate_shipping"),

path('track-order/', OrderTrackingView.as_view(), name='track_order'),
path('orders/', views.order_list, name='order_list'),
path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
path('invoice/<int:order_id>/', views.invoice_view, name='invoice'),
path('admin/invoice/<int:order_id>/', views.admin_invoice_view, name='admin_invoice'),
path('order/receipt/<int:order_id>/', views.delivery_receipt_view, name='delivery_receipt'),
path('print-pending-receipts/', views.print_pending_receipts, name='print_pending_receipts'),
path('checkout/', views.checkout_view, name='checkout'),

path('payment-success/', views.payment_success_view, name='payment_success'),

path('print-pending-invoices/', views.print_pending_invoices, name='print_pending_invoices'),

path('return/', views.create_return_request, name='create_return_request'),
    path('return/history/', views.return_history, name='return_history'),
    path('ajax/order-items/', views.order_items_for_return, name='order_items_for_return'),

path('admin/returns/', views.return_request_admin_view, name='admin_return_requests'),
path('order/admin/returns/toggle/', views.toggle_return_status, name='toggle_return_status'),


path('order/order-success/', views.order_success_page, name='order_success')






]
