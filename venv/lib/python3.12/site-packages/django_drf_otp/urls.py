from django.urls import path

from .viewsets import OTPTokenViewSet

urlpatterns = [
    path("login/", OTPTokenViewSet.as_view({"post": "login"}), name="login"),
    path("verify-token/", OTPTokenViewSet.as_view({"post": "verify_token"}), name="verify-token"),
    path("resend-token/", OTPTokenViewSet.as_view({"post": "resend_token"}), name="resend-token"),
]
