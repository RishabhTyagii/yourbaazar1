"""
URL configuration for yourbaazar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cart/', include('cart.urls')),
    path('', include(("product.urls", "product"),namespace='product')),
    path('order/', include('order.urls')),
    path('coupon/', include('coupon.urls')),
    
    path('accounts/', include('accounts.urls')),
    path('', include('basicinfo.urls')),
    path('nested_admin/', include('nested_admin.urls')),
    path('wishlist/', include('wishlist.urls', namespace='wishlist')),
     path('product_review/', include('product_review.urls', namespace='review')),
    #  path('sales/', include('salesdata.urls')),
    #  path('autocomplete/', include('dal.urls')), 
    path('seller/', include('seller.urls')),
    path('seller_products/', include('seller_products.urls', namespace='seller_products')),
    path('wallet/', include('wallet.urls', namespace='wallet')),
    path("seller-reviews/", include("seller_reviews.urls", namespace="seller_reviews")),
    path("seller_reports/",include('seller_reports.urls', namespace="seller_reports"))
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
