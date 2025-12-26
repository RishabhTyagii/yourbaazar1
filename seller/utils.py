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

from django.core.mail import EmailMultiAlternatives

def send_otp_email(to_email, otp):
    subject = "YourBaazar Seller OTP Verification"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [to_email]

    # Plain text fallback
    text_content = f"Your OTP is {otp}. It will expire in {settings.OTP_EXPIRE_MIN} minutes."

    # HTML email template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>YourBaazar OTP</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f4f4f4; font-family: Arial, sans-serif;">
      <table align="center" cellpadding="0" cellspacing="0" width="100%" style="max-width:600px; background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.1); margin:20px auto;">
        
        <!-- Header -->
        <tr>
          <td style="background:#2911e0; text-align:center; padding:25px;">
            <img src="https://yourbaazar.com/static/icon/logo.png" alt="YourBaazar Logo" style="max-width:160px;">
          </td>
        </tr>

        <!-- Content -->
        <tr>
          <td style="padding:35px; color:#333;">
            <h2 style="color:#2911e0; margin-bottom:20px; text-align:center;">OTP Verification</h2>
            <p style="font-size:16px; line-height:1.6; margin-bottom:20px; text-align:center;">
              Dear Seller,<br>
              Use the following One-Time Password (OTP) to verify your account:
            </p>
            
            <!-- OTP Button -->
            <div style="text-align:center; margin:30px 0;">
              <a href="#" style="background:#2911e0; color:#fff; font-size:22px; font-weight:bold; padding:15px 35px; border-radius:8px; text-decoration:none; letter-spacing:3px; display:inline-block;">
                {otp}
              </a>
            </div>
            
            <p style="font-size:15px; color:#555; text-align:center;">
              This OTP will expire in <strong>{settings.OTP_EXPIRE_MIN} minutes</strong>. 
              Please do not share this code with anyone.
            </p>

            <!-- Security Note -->
            <div style="margin-top:25px; font-size:13px; color:#777; text-align:center; background:#f9f9f9; padding:12px; border-radius:6px;">
              ⚠️ For your security, YourBaazar will never ask for your OTP via phone or email. 
            </div>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#fafafa; padding:20px; text-align:center; font-size:13px; color:#999;">
            <p style="margin:0 0 10px 0; font-size:14px; color:#333; font-weight:bold;">
              YourBaazar Seller App – Grow Your Business with Us 🚀
            </p>
            Need help? Contact us at 
            <a href="mailto:support@yourbaazar.com" style="color:#2911e0; text-decoration:none;">support@yourbaazar.com</a><br><br>
            © {settings.SITE_NAME if hasattr(settings, "SITE_NAME") else "YourBaazar"} | All rights reserved.
          </td>
        </tr>

      </table>
    </body>
    </html>
    """

    # Create email
    email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)


from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def notify_admin_new_seller(email, username, business_name):
    subject = "New Seller Registration Pending Approval"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [settings.ADMIN_NOTIFY_EMAIL]

    # Plain text fallback
    text_content = f"""
    A new seller registered:

    Email: {email}
    Username: {username}
    Business: {business_name}

    Please approve in admin panel.
    """

    # HTML email template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>New Seller Registration</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f4f4f4; font-family: Arial, sans-serif;">
      <table align="center" cellpadding="0" cellspacing="0" width="100%" style="max-width:600px; background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.1); margin:20px auto;">
        
        <!-- Header -->
        <tr>
          <td style="background:#2911e0; text-align:center; padding:25px;">
            <img src="https://yourbaazar.com/static/icon/logo.png" alt="YourBaazar Logo" style="max-width:160px;">
          </td>
        </tr>

        <!-- Content -->
        <tr>
          <td style="padding:35px; color:#333;">
            <h2 style="color:#2911e0; margin-bottom:20px; text-align:center;">New Seller Registration</h2>
            <p style="font-size:16px; line-height:1.6; margin-bottom:25px; text-align:center;">
              A new seller has registered and is pending approval. Here are the details:
            </p>

            <!-- Seller Info Table -->
            <table align="center" cellpadding="10" cellspacing="0" style="width:100%; border-collapse:collapse; background:#f9f9f9; border-radius:8px;">
              <tr>
                <td style="font-weight:bold; color:#2911e0; width:30%;">Email:</td>
                <td style="color:#333;">{email}</td>
              </tr>
              <tr>
                <td style="font-weight:bold; color:#2911e0;">Username:</td>
                <td style="color:#333;">{username}</td>
              </tr>
              <tr>
                <td style="font-weight:bold; color:#2911e0;">Business:</td>
                <td style="color:#333;">{business_name}</td>
              </tr>
            </table>

            <div style="text-align:center; margin-top:30px;">
              <a href="{getattr(settings, 'ADMIN_PANEL_URL', '#')}" 
                 style="background:#2911e0; color:#fff; font-size:16px; font-weight:bold; padding:12px 25px; border-radius:6px; text-decoration:none; display:inline-block;">
                Approve Seller
              </a>
            </div>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#fafafa; padding:20px; text-align:center; font-size:13px; color:#999;">
            <p style="margin:0 0 10px 0; font-size:14px; color:#333; font-weight:bold;">
              YourBaazar Seller App – Grow Your Business with Us 🚀
            </p>
            Need help? Contact us at 
            <a href="mailto:support@yourbaazar.com" style="color:#2911e0; text-decoration:none;">support@yourbaazar.com</a><br><br>
            © {settings.SITE_NAME if hasattr(settings, "SITE_NAME") else "YourBaazar"} | All rights reserved.
          </td>
        </tr>

      </table>
    </body>
    </html>
    """

    # Create email
    email_obj = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email_obj.attach_alternative(html_content, "text/html")
    email_obj.send(fail_silently=False)

from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def notify_seller_approved(to_email):
    subject = "Congratulations! Your Seller Account is Approved 🎉"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [to_email]

    # Plain text fallback
    text_content = """
    Congratulations! Your seller account has been approved. 
    You can now log in and start adding products to YourBaazar Seller App.
    """

    # HTML email template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Seller Approved</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f4f4f4; font-family: Arial, sans-serif;">
      <table align="center" cellpadding="0" cellspacing="0" width="100%" style="max-width:600px; background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.1); margin:20px auto;">
        
        <!-- Header -->
        <tr>
          <td style="background:#2911e0; text-align:center; padding:25px;">
            <img src="https://yourbaazar.com/static/icon/logo.png" alt="YourBaazar Logo" style="max-width:160px;">
          </td>
        </tr>

        <!-- Content -->
        <tr>
          <td style="padding:35px; color:#333; text-align:center;">
            <h2 style="color:#2911e0; margin-bottom:15px;">Congratulations 🎉</h2>
            <p style="font-size:16px; line-height:1.6; margin-bottom:25px;">
              Your seller account has been <strong>approved</strong>! <br>
              You can now log in to your dashboard and start adding products to grow your business with us.
            </p>

            <!-- CTA Button -->
            <div style="margin:30px 0;">
              <a href="{getattr(settings, 'SELLER_DASHBOARD_URL', '#')}" 
                 style="background:#2911e0; color:#fff; font-size:16px; font-weight:bold; padding:14px 28px; border-radius:6px; text-decoration:none; display:inline-block;">
                Add Products Now
              </a>
            </div>

            <p style="font-size:14px; color:#666; margin-top:20px;">
              We’re excited to have you on board 🚀
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#fafafa; padding:20px; text-align:center; font-size:13px; color:#999;">
            <p style="margin:0 0 10px 0; font-size:14px; color:#333; font-weight:bold;">
              YourBaazar Seller App – Grow Your Business with Us 🚀
            </p>
            Need help? Contact us at 
            <a href="mailto:support@yourbaazar.com" style="color:#2911e0; text-decoration:none;">support@yourbaazar.com</a><br><br>
            © {settings.SITE_NAME if hasattr(settings, "SITE_NAME") else "YourBaazar"} | All rights reserved.
          </td>
        </tr>

      </table>
    </body>
    </html>
    """

    # Create email
    email_obj = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email_obj.attach_alternative(html_content, "text/html")
    email_obj.send(fail_silently=False)


def otp_expiry_time():
    return timezone.now() + timedelta(minutes=settings.OTP_EXPIRE_MIN)

def resend_cooldown_time():
    return timezone.now() + timedelta(seconds=settings.OTP_RESEND_COOLDOWN_SEC)


from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def send_reset_otp_email(to_email, otp):
    subject = "Reset Your Password - OTP"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [to_email]

    # Plain text fallback
    text_content = f"Your password reset OTP is {otp}. It will expire in {settings.OTP_EXPIRE_MIN} minutes."

    # HTML email template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Password Reset OTP</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f4f4f4; font-family: Arial, sans-serif;">
      <table align="center" cellpadding="0" cellspacing="0" width="100%" style="max-width:600px; background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.1); margin:20px auto;">
        
        <!-- Header -->
        <tr>
          <td style="background:#2911e0; text-align:center; padding:25px;">
            <img src="https://yourbaazar.com/static/icon/logo.png" alt="YourBaazar Logo" style="max-width:160px;">
          </td>
        </tr>

        <!-- Content -->
        <tr>
          <td style="padding:35px; color:#333; text-align:center;">
            <h2 style="color:#2911e0; margin-bottom:15px;">Password Reset Request</h2>
            <p style="font-size:16px; line-height:1.6; margin-bottom:25px;">
              We received a request to reset your password.<br>
              Use the following One-Time Password (OTP) to proceed:
            </p>

            <!-- OTP Button -->
            <div style="margin:30px 0;">
              <a href="#" style="background:#2911e0; color:#fff; font-size:22px; font-weight:bold; padding:14px 28px; border-radius:6px; text-decoration:none; letter-spacing:2px; display:inline-block;">
                {otp}
              </a>
            </div>

            <p style="font-size:15px; color:#555; margin-bottom:20px;">
              This OTP will expire in <strong>{settings.OTP_EXPIRE_MIN} minutes</strong>.<br>
              If you did not request a password reset, please ignore this email.
            </p>

            <!-- Security Note -->
            <div style="margin-top:25px; font-size:13px; color:#777; text-align:center; background:#f9f9f9; padding:12px; border-radius:6px;">
              ⚠️ For your security, never share this OTP with anyone.  
            </div>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#fafafa; padding:20px; text-align:center; font-size:13px; color:#999;">
            <p style="margin:0 0 10px 0; font-size:14px; color:#333; font-weight:bold;">
              YourBaazar Seller App – Grow Your Business with Us 🚀
            </p>
            Need help? Contact us at 
            <a href="mailto:support@yourbaazar.com" style="color:#2911e0; text-decoration:none;">support@yourbaazar.com</a><br><br>
            © {settings.SITE_NAME if hasattr(settings, "SITE_NAME") else "YourBaazar"} | All rights reserved.
          </td>
        </tr>

      </table>
    </body>
    </html>
    """

    # Create email
    email_obj = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email_obj.attach_alternative(html_content, "text/html")
    email_obj.send(fail_silently=False)


from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction

def notify_sellers_new_order(order):
    """Lightweight notification system for sellers on new orders"""
    notified_sellers = set()
    email_batch = []

    for item in order.items.all():
        seller_meta = SellerProductMeta.objects.filter(product=item.product).first()
        if not seller_meta:
            continue

        seller = seller_meta.seller
        if seller.id in notified_sellers:
            continue  # already notified

        # 1️⃣ In-app notification
        SellerNotification.objects.create(
            seller=seller,
            message=f"New order: {order.order_number} - "
                    f"{item.product.name} (x{item.quantity})",
            order=order
        )

        # 2️⃣ Collect emails (don’t send instantly)
        email_batch.append((
            f"New Order #{order.order_number}",  # subject
            f"You received a new order #{order.order_number}\n\n"
            f"Product: {item.product.name}\n"
            f"Quantity: {item.quantity}\n\n"
            f"Check: http://yourbaazar/seller/seller/orders/{order.id}/",
            settings.DEFAULT_FROM_EMAIL,
            [seller.email]
        ))

        notified_sellers.add(seller.id)

    # 3️⃣ Send all emails in bulk (faster, one connection)
    if email_batch:
        from django.core.mail import get_connection
        connection = get_connection()  # single SMTP connection
        send_mail = connection.send_messages  # alias

        # Convert tuples to EmailMessage objects
        from django.core.mail import EmailMessage
        email_messages = [
            EmailMessage(subject, body, from_email, recipient_list)
            for subject, body, from_email, recipient_list in email_batch
        ]

        send_mail(email_messages)

