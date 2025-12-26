# yourbaazar/middleware.py
from django.utils.deprecation import MiddlewareMixin

class SellerSubdomainMiddleware(MiddlewareMixin):
    def process_request(self, request):
        host = request.META.get('HTTP_HOST', '')
        is_seller_subdomain = 'yourbaazarseller.shop' in host

        if is_seller_subdomain:
            path = request.path

            # Agar double /seller/ hai toh usko normalize karo
            if path.startswith('/seller/seller/'):
                path = path.replace('/seller/seller/', '/seller/', 1)

            # Agar bilkul bhi /seller/ nahi hai toh chipkao
            elif not path.startswith('/seller/'):
                path = '/seller' + path

            # Final set karo
            request.path = path
            request.path_info = path
