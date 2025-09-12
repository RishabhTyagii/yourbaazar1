# app/models.py
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.conf import settings
from order.models import Order  # Adjust import based on your actual app structure
class SellerDraft(models.Model):
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    username = models.CharField(max_length=150)
    business_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255)
    address = models.TextField()

    city = models.CharField(max_length=100,blank=True, null=True)
    state = models.CharField(max_length=100,blank=True, null=True)
    pincode = models.CharField(max_length=10,blank=True, null=True)
    bank_account_name = models.CharField(max_length=150, blank=True)
    bank_account_no = models.CharField(max_length=40, blank=True)
    ifsc = models.CharField(max_length=20, blank=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    # Optional fields
    # gst and pan are optional for initial registration
    gst = models.CharField(max_length=20, blank=True, null=True)
    pan = models.CharField(max_length=20, blank=True, null=True)
    # 👇 new fields
    pan_photo = models.ImageField(upload_to="seller_docs/pan/%Y/%m/", blank=True, null=True)
    aadhar_number = models.CharField(max_length=16, blank=True, null=True)
    aadhar_photo = models.ImageField(upload_to="seller_docs/aadhar/%Y/%m/", blank=True, null=True)
    password_hash = models.CharField(max_length=255)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expires_at = models.DateTimeField(blank=True, null=True)
    resend_cooldown_until = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

class Seller(models.Model):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    username = models.CharField(max_length=150, unique=True)
    business_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255)
    address = models.TextField()

    
    state = models.CharField(max_length=100,blank=True, null=True)
    city = models.CharField(max_length=100,blank=True, null=True)
    pincode = models.CharField(max_length=10,blank=True, null=True)
    bank_account_name = models.CharField(max_length=150, blank=True)
    bank_account_no = models.CharField(max_length=40, blank=True)
    ifsc = models.CharField(max_length=20, blank=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)

    # Optional fields
    # gst and pan are optional for initial registration

    gst = models.CharField(max_length=20, blank=True, null=True)
    pan = models.CharField(max_length=20, blank=True, null=True)
    # 👇 new fields
    pan_photo = models.ImageField(upload_to="seller_docs/pan/%Y/%m/", blank=True, null=True)
    aadhar_number = models.CharField(max_length=16, blank=True, null=True)
    aadhar_photo = models.ImageField(upload_to="seller_docs/aadhar/%Y/%m/", blank=True, null=True)
    password_hash = models.CharField(max_length=255)
    is_email_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Forgot password OTP flow fields
    reset_otp_code = models.CharField(max_length=6, blank=True, null=True)
    reset_otp_expires_at = models.DateTimeField(blank=True, null=True)
    reset_resend_cooldown_until = models.DateTimeField(blank=True, null=True)
    def __str__(self):
        if self.business_name:
            return self.business_name
        elif self.owner_name:
            return self.owner_name
        return self.user.username  # fallback
    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

class Product(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, validators=[MinLengthValidator(1)])
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)



class SellerNotification(models.Model):
    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True, 
        blank=True
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='seller_notifications')
    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.seller.email} - Order #{self.order.order_number}"