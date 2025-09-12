# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class Customer(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True) 
    otp = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    

    def __str__(self):
        return self.email
    def get_full_name(self):
        # first_name + last_name fallback
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username  # fallback

