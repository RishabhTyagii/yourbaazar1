# accounts/views.py
from django.shortcuts import render, redirect
from .forms import CustomerRegisterForm, OTPForm,EditProfileForm,EmailForm, OTPPasswordForm
from .models import Customer
from basicinfo.models import contact_us
from django.core.mail import send_mail
import random
from django.contrib.auth import logout
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.timezone import localtime
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.utils.timezone import now

from datetime import datetime, timedelta
from django.utils.crypto import get_random_string

from order.models import Order,ReturnRequest  # adjust path if needed
from wishlist.models import Wishlist  # adjust path if needed
from django.contrib.auth import get_user_model
import time
from django.contrib.auth.decorators import user_passes_test

from django.db.models import Q


import requests

from django.core.mail import EmailMultiAlternatives

def send_otp(email, otp):
    subject = "YourBaazar - Email Verification Code"

    text_content = f"""
Dear Customer,

Thank you for registering with YourBaazar!

Your OTP for account verification is: {otp}

This code is valid for 10 minutes. Please do not share it with anyone.

Best regards,
Team YourBaazar
"""

    # ✅ hosted logo link (replace this with your real logo URL if deployed)
    logo_url = "https://yourbaazar.in/static/icon/logo.png"

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>YourBaazar OTP Verification</title>
  <style>
    body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f4f8fb;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 600px;
      margin: 40px auto;
      background: #fff;
      border-radius: 14px;
      box-shadow: 0 6px 20px rgba(0,0,0,0.08);
      overflow: hidden;
    }}
    .header {{
      background: linear-gradient(135deg, #00bfa6, #0097b2);
      text-align: center;
      padding: 30px 20px 15px;
    }}
    .header img {{
      width: 70px;
      height: 70px;
      border-radius: 14px;
    }}
    .header h1 {{
      margin-top: 10px;
      color: #fff;
      font-size: 24px;
      font-weight: 600;
    }}
    .content {{
      padding: 30px;
      text-align: center;
      color: #333;
    }}
    .otp-box {{
      display: inline-block;
      background-color: #e6f7ff;
      color: #0077b6;
      padding: 14px 28px;
      border-radius: 8px;
      font-size: 22px;
      font-weight: bold;
      letter-spacing: 4px;
      margin: 25px 0;
    }}
    .footer {{
      background: #f9f9f9;
      color: #777;
      font-size: 13px;
      padding: 15px;
      text-align: center;
      border-top: 1px solid #eee;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <img src="{logo_url}" alt="YourBaazar Logo" />
      <h1>YourBaazar Verification</h1>
    </div>
    <div class="content">
      <p>Dear Customer,</p>
      <p>Thank you for registering with <b>YourBaazar</b>!</p>
      <p>Your One-Time Password (OTP) for account verification is:</p>
      <div class="otp-box">{otp}</div>
      <p>This code is valid for <b>10 minutes</b>. Please do not share it with anyone.</p>
      <p>Best regards,<br><b>Team YourBaazar</b></p>
    </div>
    <div class="footer">
      &copy; {2025} YourBaazar. All rights reserved.
    </div>
  </div>
</body>
</html>
"""

    try:
        msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        print(f"✅ OTP sent to {email}")
        return True
    except Exception as e:
        print(f"❌ Error sending OTP: {e}")
        return False

# ----------------------
# Register View
# ----------------------
def register(request):
    if request.method == 'POST':
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            registration_data = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'phone_number': form.cleaned_data['phone_number'],
                'password': make_password(form.cleaned_data['password']),
                'otp': str(random.randint(100000, 999999)),
                'otp_expiry': (now() + timedelta(minutes=10)).timestamp(),
                'otp_attempts': 0
            }
            request.session['registration_data'] = registration_data

            if send_otp(registration_data['email'], registration_data['otp']):
                request.session['last_otp_time'] = time.time()
                return redirect('verify_otp')
            else:
                messages.error(request, "Failed to send OTP. Please try again.")
        else:
            messages.error(request, "Invalid form. Please correct the errors.")
    else:
        form = CustomerRegisterForm()

    return render(request, 'account/register.html', {'form': form})


# ----------------------
# Verify OTP View
# ----------------------
def verify_otp(request):
    registration_data = request.session.get('registration_data')

    if not registration_data:
        messages.error(request, "Session expired. Please register again.")
        return redirect('register')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp_expiry = registration_data.get('otp_expiry')
            otp_attempts = registration_data.get('otp_attempts', 0)

            # Expiry check
            if otp_expiry and now().timestamp() > otp_expiry:
                form.add_error(None, "OTP has expired. Please register again.")
                return render(request, 'account/verify_otp.html', {'form': form})

            # Attempt limit check
            if otp_attempts >= 5:
                form.add_error(None, "Too many wrong attempts. Please register again.")
                return render(request, 'account/verify_otp.html', {'form': form})

            # Match check
            if form.cleaned_data['otp'] == registration_data['otp']:
                Customer.objects.create(
                    username=registration_data['username'],
                    email=registration_data['email'],
                    phone_number=registration_data['phone_number'],
                    password=registration_data['password'],
                    is_verified=True
                )

                # Clear session
                request.session.pop('registration_data', None)
                request.session.pop('last_otp_time', None)

                messages.success(request, "Your account has been verified successfully!")
                return redirect('login')
            else:
                # Wrong OTP
                registration_data['otp_attempts'] = otp_attempts + 1
                request.session['registration_data'] = registration_data
                form.add_error(None, "Invalid OTP. Please try again.")

    else:
        form = OTPForm()

    return render(request, 'account/verify_otp.html', {'form': form})


# ----------------------
# Resend OTP View
# ----------------------
def resend_otp(request):
    registration_data = request.session.get('registration_data')
    if not registration_data:
        messages.error(request, "Session expired. Please register again.")
        return redirect('register')

    last_sent = request.session.get('last_otp_time', 0)
    current_time = time.time()

    if current_time - last_sent < 60:
        remaining_time = int(60 - (current_time - last_sent))
        messages.warning(request, f"Please wait {remaining_time} seconds before resending OTP.")
        return redirect('verify_otp')

    # Generate new OTP
    otp = str(random.randint(100000, 999999))
    registration_data['otp'] = otp
    registration_data['otp_expiry'] = (now() + timedelta(minutes=10)).timestamp()
    registration_data['otp_attempts'] = 0  # reset attempts
    request.session['registration_data'] = registration_data

    if send_otp(registration_data['email'], otp):
        request.session['last_otp_time'] = current_time
        messages.success(request, "OTP resent successfully.")
    else:
        messages.error(request, "Failed to resend OTP. Please try again.")

    return redirect('verify_otp')




from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if next_url and next_url.lower() != 'none':
                return redirect(next_url)
            else:
                return redirect('product:indexpage')  # Fallback homepage
        else:
            messages.error(request, "Invalid credentials. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'account/login.html', {'form': form, 'next': next_url})

def logout_view(request):
    logout(request)  # Logs the user out
    return redirect('product:indexpage')  # Redirect to the home page after logging out

# @login_required
# def view_profile(request):
#     return render(request, 'view_profile.html', {'user': request.user})
@login_required
def view_profile(request):
    user = request.user

    # Total orders for the logged-in user
    total_orders = Order.objects.filter(user=user).count()

    # Total wishlist items for the user (assuming one-to-many)
    total_wishlist_items = Wishlist.objects.filter(user=user).count()

    user_queries = contact_us.objects.filter(user=request.user).order_by('-id')  # latest first

    # Member since year (from date_joined field in AbstractUser)
    join_date = localtime(user.date_joined).strftime('%d %B %Y') 

    context = {
        'user': user,
        'total_orders': total_orders,
        'wishlist_count': total_wishlist_items,
        'member_since': join_date,
        'user_queries':user_queries
    }
    return render(request, 'account/view_profile.html', context)
@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=user, user=user)  # pass user
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('view_profile')
    else:
        form = EditProfileForm(instance=user, user=user)  # pass user here too

    return render(request, 'account/edit_profile.html', {'form': form})

# <a href="{% url 'edit_profile' %}">Edit Profile</a>



User = get_user_model()

def request_password_change(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            otp = get_random_string(6, allowed_chars='0123456789')
            user.otp = otp
            user.save()

            # Send OTP to email
            send_mail(
                'Your OTP for Password Reset',
                f'Hello {user.username},\n\nYour OTP to reset your password is: {otp},\n\n\n\n\n Team yourbaazar',
                # f"Dear {user.username},\n\n"
                # f"We received a request to reset your password for your YourBaazar account.\n\n"
                # f"Your One-Time Password (OTP) is: {otp}\n\n"
                # f"Please enter this OTP in the password reset page to proceed.\n"
                # f"This OTP is valid for a limited time only. Do not share it with anyone.\n\n"
                # f"If you did not request a password reset, please ignore this email.\n\n"
                # f"Best regards,\n"
                # f"Team YourBaazar"
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            request.session['reset_email'] = email
            messages.success(request, f'OTP sent to {email}')
            return redirect('verify_password_otp')

        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')

    return render(request, 'account/change_password_request.html')


def verify_password_otp(request):
    if request.method == 'POST':
        email = request.session.get('reset_email')
        otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        # confirm_password = request.POST.get('confirm_password')

        try:
            user = User.objects.get(email=email, otp=otp)
            user.set_password(new_password)
            user.otp = ''
            user.save()
            messages.success(request, 'Password successfully changed. Please log in.')
            return redirect('login')

        except User.DoesNotExist:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'account/change_password_verify.html')







@user_passes_test(lambda u: u.is_superuser)
def custom_admin_dashboard(request):
    query = request.GET.get('q', '').strip()
    customers = Customer.objects.all()

    customers = customers.filter(
    Q(username__icontains=query) |
    Q(email__icontains=query) |
    Q(phone_number__icontains=query) |
    Q(orders__id__icontains=query)
).distinct()

    customer_data = []
    for customer in customers:
        orders = Order.objects.filter(user=customer)
        total_orders = orders.count()
        total_spent = sum(order.total_amount for order in orders)

        customer_data.append({
            'customer': customer,
            'total_orders': total_orders,
            'total_spent': total_spent,
            'last_login': customer.last_login,
            'joined': customer.date_joined,
        })

    return render(request, 'admin/admin_dashboard.html', {
        'customer_data': customer_data,
        'query': query,
    })




