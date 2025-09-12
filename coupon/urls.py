
from django.urls import path
from coupon import assign_coupons
from coupon import views
urlpatterns = [
     path('admin/coupons/analytics/', views.coupon_analytics_dashboard, name='coupon_analytics'),
    path('apply-coupon/', views.apply_coupon_view, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon_view, name='remove_coupon'),
    path('my-coupons/', assign_coupons.my_coupons_view, name='my_coupons')

]
# This URL pattern maps the 'apply/' path to the apply_coupon_view function in views.py