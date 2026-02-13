# seller_api/models.py
from django.db import models
from seller.models import Seller
import secrets

class SellerAPIKey(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name="api_keys")
    api_key = models.CharField(max_length=64, unique=True)
    api_secret = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = "yb_" + secrets.token_hex(16)
        if not self.api_secret:
            self.api_secret = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.seller.username} API Key"
