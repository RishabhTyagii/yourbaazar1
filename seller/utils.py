# app/utils.py
import random
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

from django.urls import reverse
from django.conf import settings
from collections import defaultdict
from .models import SellerNotification
from seller_products.models import SellerProductMeta
def generate_otp():
    return f"{random.randint(100000, 999999)}"

def send_otp_email(to_email, otp):
    subject = "Your OTP Verification Code"
    message = f"Your OTP is {otp}. It will expire in {settings.OTP_EXPIRE_MIN} minutes."
    recipient_list = [to_email]   # ✅ direct string use
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=False)

def notify_admin_new_seller(email, username, business_name):
    subject = "New Seller Registration Pending Approval"
    message = f"A new seller registered:\nEmail: {email}\nUsername: {username}\nBusiness: {business_name}\nPlease approve in admin."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_NOTIFY_EMAIL], fail_silently=False)

def notify_seller_approved(to_email):
    subject = "Seller Approved"
    message = "Congratulations! Your seller account has been approved. You can now add products."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)

def otp_expiry_time():
    return timezone.now() + timedelta(minutes=settings.OTP_EXPIRE_MIN)

def resend_cooldown_time():
    return timezone.now() + timedelta(seconds=settings.OTP_RESEND_COOLDOWN_SEC)


def send_reset_otp_email(to_email, otp):
    subject = "Reset your password - OTP"
    message = f"Your password reset OTP is {otp}. It will expire in {settings.OTP_EXPIRE_MIN} minutes."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)   


def notify_sellers_new_order(order):
    """Notify all sellers involved in an order about new items"""
    notified_sellers = set()

    for item in order.items.all():
        seller_meta = SellerProductMeta.objects.filter(product=item.product).first()
        if not seller_meta:
            continue

        seller = seller_meta.seller
        if seller.id in notified_sellers:
            continue  # already notified

        # 1️⃣ Create in-app notification
        SellerNotification.objects.create(
            seller=seller,
            message=f"You have received a new order: {order.order_number}\n"
                    f"Product: {item.product.name} (SKU: {item.product.sku})\n"
                    f"Quantity: {item.quantity}",
            order=order  # optional, if you want to link notification to order
        )

        # 2️⃣ Send email
        message = f"Hi {seller.username},\n\n" \
                  f"You have received a new order: {order.order_number}\n" \
                  f"Product: {item.product.name} (SKU: {item.product.sku})\n" \
                  f"Quantity: {item.quantity}\n\n" \
                  f"View order: http://yourbaazar/seller/seller/orders/{order.id}/"

        send_mail(
            subject=f"New Order #{order.order_number}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[seller.email],  # <- direct email from Seller model
        )

        notified_sellers.add(seller.id)



