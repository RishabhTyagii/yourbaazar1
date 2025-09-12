# app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from product.models import product
from .models import SellerDraft, Seller, Product,SellerNotification
from .forms import SellerRegisterForm, OTPForm, ProductForm,SellerLoginForm, SellerProfileForm,ForgotPasswordRequestForm, ForgotPasswordOTPForm, PasswordResetForm
from .utils import generate_otp, send_otp_email, notify_admin_new_seller, notify_seller_approved, otp_expiry_time, resend_cooldown_time,send_reset_otp_email
from decimal import Decimal
from collections import defaultdict
from django.db.models import Sum, F, DecimalField, Value, Q,ExpressionWrapper
from django.db.models.functions import Coalesce
from order.models import Order, OrderItem,ORDER_STATUS_CHOICES
from seller_products.models import SellerProductMeta
from django.core.paginator import Paginator
from seller_reviews.models import SellerTestimonial
from wallet.models import SellerWallet, WalletTransaction, WithdrawalRequest

def seller_landing(request):
    seller_id = request.session.get("seller_id") 
    total_sellers = Seller.objects.count()
    total_products = product.objects.count()
    total_orders = Order.objects.count()  # or your field for completed orders
    wallet = SellerWallet.objects.filter(seller=seller_id).first()

    # Latest approved reviews for carousel (e.g., last 8)
    carousel_reviews = SellerTestimonial.objects.filter(is_approved=True).select_related("seller").order_by("-created_at")[:8]
    context = {
        'total_sellers': total_sellers,
        'total_products': total_products,
        'total_orders': total_orders,
        'carousel_reviews': carousel_reviews,
        'wallet': wallet,
    
        # 'latest_reviews': latest_reviews,
    }
    return render(request, 'seller/seller_info.html', context)


def seller_register(request):
    request.session.pop("seller_draft_id", None)
    if request.method == "POST":
        form = SellerRegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].strip()
            username = form.cleaned_data["username"].strip()

            # Check if email or username already exist in final Seller
            email_exists = Seller.objects.filter(email__iexact=email).exists()
            username_exists = Seller.objects.filter(username__iexact=username).exists()

            if email_exists:
                # Check if a valid draft exists for this email
                draft = SellerDraft.objects.filter(email__iexact=email).first()
                if draft and draft.otp_expires_at and draft.otp_expires_at > timezone.now():
                    request.session["seller_draft_id"] = draft.id
                    request.session.modified = True
                    return redirect("seller:verify_otp")
                else:
                    form.add_error("email", "Email already registered.")

            if username_exists:
                form.add_error("username", "Username already taken.")

            # Check pending drafts (email OR username)
            pending_draft = SellerDraft.objects.filter(
                Q(email__iexact=email) | Q(username__iexact=username)
            ).first()
            if pending_draft:
                if pending_draft.otp_expires_at and pending_draft.otp_expires_at < timezone.now():
                    # Expired → remove draft
                    pending_draft.delete()
                    pending_draft = None
                else:
                    request.session["seller_draft_id"] = pending_draft.id
                    request.session.modified = True
                    return redirect("seller:verify_otp")

            # Create new draft only if no errors and no valid pending draft
            if form.is_valid() and not pending_draft:
                draft = SellerDraft(
                    email=email,
                    phone=form.cleaned_data["phone"],
                    username=username,
                    business_name=form.cleaned_data["business_name"],
                    owner_name=form.cleaned_data["owner_name"],
                    address=form.cleaned_data["address"],
                    city=form.cleaned_data["city"],
                    state=form.cleaned_data["state"],
                    pincode=form.cleaned_data["pincode"],
                    bank_account_name=form.cleaned_data.get("bank_account_name", ""),
                    bank_account_no=form.cleaned_data.get("bank_account_no", ""),
                    ifsc=form.cleaned_data.get("ifsc", ""),
                    upi_id=form.cleaned_data.get("upi_id", ""),
                    gst=form.cleaned_data.get("gst") or "",
                    pan=form.cleaned_data.get("pan") or "",
                    pan_photo=request.FILES.get("pan_photo"),  # ✅ Yeh ab model ke ImageField mein save hoga
                    aadhar_number=form.cleaned_data.get("aadhar_number", ""),
                    aadhar_photo=request.FILES.get("aadhar_photo"),  # ✅ Yeh bhi save hoga
                )
                draft.set_password(form.cleaned_data["password"])
                otp = generate_otp()
                draft.otp_code = otp
                draft.otp_expires_at = otp_expiry_time()
                draft.resend_cooldown_until = resend_cooldown_time()
                draft.save()

                request.session["seller_draft_id"] = draft.id
                request.session.modified = True
                send_otp_email(draft.email, otp)

                return redirect("seller:verify_otp")
    else:
        form = SellerRegisterForm()

    return render(request, "seller/seller_register.html", {"form": form})

def verify_otp(request):
    draft_id = request.session.get("seller_draft_id")
    if not draft_id:
        messages.error(request, "No pending registration found.")
        return redirect("seller_register")

    draft = get_object_or_404(SellerDraft, id=draft_id)
    cooldown_remaining = max(0, int((draft.resend_cooldown_until - timezone.now()).total_seconds())) if draft.resend_cooldown_until else 0

    if request.method == "POST":
        form = OTPForm(request.POST)
        if form.is_valid():
            input_otp = form.cleaned_data["otp"]
            if not draft.otp_code or not draft.otp_expires_at or timezone.now() > draft.otp_expires_at:
                messages.error(request, "OTP expired. Please resend.")
            elif input_otp != draft.otp_code:
                messages.error(request, "Wrong OTP. Please try again.")
            else:
                # Create final Seller, mark email verified
                seller = Seller(
                    email=draft.email,
                    phone=draft.phone,
                    username=draft.username,
                    business_name=draft.business_name,
                    owner_name=draft.owner_name,
                    address=draft.address,

                    city=draft.city,
                    state=draft.state,
                    pincode=draft.pincode,
                    bank_account_name=draft.bank_account_name,
                    bank_account_no=draft.bank_account_no,
                    ifsc=draft.ifsc,
                    upi_id=draft.upi_id,
                    # Optional fields

                    gst=draft.gst,
                    pan=draft.pan,
                    password_hash=draft.password_hash,
                    is_email_verified=True,
                    is_approved=False,
                        # 👇 new fields
                    pan_photo=draft.pan_photo,
                    aadhar_number=draft.aadhar_number,
                    aadhar_photo=draft.aadhar_photo,

                )
                seller.save()
                draft.delete()

                # login-like session
                request.session["seller_id"] = seller.id
                request.session.pop("seller_draft_id", None)
                
                # notify admin
                notify_admin_new_seller(seller.email, seller.username, seller.business_name)

                return redirect("seller:seller_landing")
    else:
        form = OTPForm()

    return render(request, "seller/verify_otp.html", {
        "form": form,
        "cooldown_remaining": cooldown_remaining
    })

def resend_otp(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request")

    draft_id = request.session.get("seller_draft_id")
    if not draft_id:
        return JsonResponse({"ok": False, "error": "No pending registration"}, status=400)

    draft = get_object_or_404(SellerDraft, id=draft_id)
    now = timezone.now()
    if draft.resend_cooldown_until and now < draft.resend_cooldown_until:
        remaining = int((draft.resend_cooldown_until - now).total_seconds())
        return JsonResponse({"ok": False, "cooldown_remaining": remaining}, status=429)

    otp = generate_otp()
    draft.otp_code = otp
    draft.otp_expires_at = otp_expiry_time()
    draft.resend_cooldown_until = resend_cooldown_time()
    draft.save()

    send_otp_email(draft.email, otp)
    remaining = int((draft.resend_cooldown_until - timezone.now()).total_seconds())
    return JsonResponse({"ok": True, "cooldown_remaining": remaining})

def require_seller_login(view_func):
    def wrapper(request, *args, **kwargs):
        seller_id = request.session.get("seller_id")
        if not seller_id:
            messages.error(request, "Please log in.")
            return redirect("seller:seller_login")
        request.seller = get_object_or_404(Seller, id=seller_id)
        return view_func(request, *args, **kwargs)
    return wrapper

@require_seller_login
def view_profile(request):
    seller = request.seller  # decorator se current seller object mil jaega
    return render(request, "seller/view_profile.html", {
        "seller": seller
    })

@require_seller_login
def edit_profile(request):
    seller = request.seller  # decorator se current seller object mil jaega

    if request.method == "POST":
        form = SellerProfileForm(request.POST, instance=seller, seller=seller)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("seller:view_profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SellerProfileForm(instance=seller, seller=seller)

    return render(request, "seller/edit_profile.html", {"form": form})
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.db.models import Q
# from .forms import SellerLoginForm
# from .models import Seller

def seller_login(request):
    # अगर पहले से logged-in है तो product_list पर भेज दें
    if request.session.get("seller_id"):
        return redirect("seller:seller_landing")

    if request.method == "POST":
        form = SellerLoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data["identifier"].strip()
            password = form.cleaned_data["password"]

            # Email या username दोनों पर खोज
            seller = Seller.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()
            if not seller:
                messages.error(request, "Account not found.")
            else:
                # Email verification compulsory
                if not seller.is_email_verified:
                    messages.error(request, "Please verify your email via OTP first.")
                    return redirect("seller:seller_register")

                # Password verify
                if not seller.check_password(password):
                    messages.error(request, "Invalid credentials.")
                else:
                    # Login success → session set
                    request.session['seller_id'] = seller.id
                    request.session['seller_username'] = seller.username  # optional, for display
                    messages.success(request, f"Welcome back, {seller.username}!")
                    return redirect("seller:seller_landing")
    else:
        form = SellerLoginForm()

    return render(request, "seller/login.html", {"form": form})

# ===================forgot password ===============>
# app/views.py






def _get_reset_seller(request):
    seller_id = request.session.get("reset_seller_id")
    if not seller_id:
        return None
    return Seller.objects.filter(id=seller_id).first()

# views.py

def forgot_password_request(request):
    # 1) Logged-in user hua to identifier prefill kar dena (email ya username)
    prefilled = None
    if request.session.get("seller_id"):
        # current seller identify
        seller = Seller.objects.filter(id=request.session["seller_id"]).first()
        if seller:
            prefilled = seller.email or seller.username

    if request.method == "POST":
        form = ForgotPasswordRequestForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data["identifier"].strip()
            seller = Seller.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()
            if not seller:
                messages.error(request, "Account not found.")
            else:
                otp = generate_otp()
                seller.reset_otp_code = otp
                seller.reset_otp_expires_at = otp_expiry_time()
                seller.reset_resend_cooldown_until = resend_cooldown_time()
                seller.save()

                request.session["reset_seller_id"] = seller.id
                request.session["reset_otp_verified"] = False
                request.session.modified = True

                send_reset_otp_email(seller.email, otp)

                return redirect("seller:forgot_password_verify_otp")
    else:
        # Prefill identifier if logged-in
        initial = {"identifier": prefilled} if prefilled else {}
        form = ForgotPasswordRequestForm(initial=initial)

    return render(request, "seller/forgot_password_request.html", {"form": form})


def forgot_password_verify_otp(request):
    seller = _get_reset_seller(request)
    if not seller:
        messages.error(request, "No reset request found. Please start again.")
        return redirect("seller:forgot_password_request")

    cooldown_remaining = 0
    if seller.reset_resend_cooldown_until:
        cooldown_remaining = max(
            0, int((seller.reset_resend_cooldown_until - timezone.now()).total_seconds())
        )

    if request.method == "POST":
        form = ForgotPasswordOTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data["otp"].strip()
            if not seller.reset_otp_code or not seller.reset_otp_expires_at or timezone.now() > seller.reset_otp_expires_at:
                messages.error(request, "OTP expired. Please resend.")
            elif otp != seller.reset_otp_code:
                messages.error(request, "Invalid OTP.")
            else:
                # Mark verified
                request.session["reset_otp_verified"] = True
                request.session.modified = True
                return redirect("seller:forgot_password_reset")
    else:
        form = ForgotPasswordOTPForm()

    return render(request, "seller/forgot_password_verify_otp.html", {
        "form": form,
        "cooldown_remaining": cooldown_remaining
    })


def forgot_password_resend_otp(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request")

    seller = _get_reset_seller(request)
    if not seller:
        return JsonResponse({"ok": False, "error": "No reset request"}, status=400)

    now = timezone.now()
    if seller.reset_resend_cooldown_until and now < seller.reset_resend_cooldown_until:
        remaining = int((seller.reset_resend_cooldown_until - now).total_seconds())
        return JsonResponse({"ok": False, "cooldown_remaining": remaining}, status=429)

    otp = generate_otp()
    seller.reset_otp_code = otp
    seller.reset_otp_expires_at = otp_expiry_time()
    seller.reset_resend_cooldown_until = resend_cooldown_time()
    seller.save()

    send_reset_otp_email(seller.email, otp)

    remaining = int((seller.reset_resend_cooldown_until - timezone.now()).total_seconds())
    return JsonResponse({"ok": True, "cooldown_remaining": remaining})


def forgot_password_reset(request):
    seller = _get_reset_seller(request)
    if not seller:
        messages.error(request, "No reset request found.")
        return redirect("seller:forgot_password_request")

    if not request.session.get("reset_otp_verified"):
        messages.error(request, "Please verify OTP first.")
        return redirect("seller:forgot_password_verify_otp")

    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            new_pwd = form.cleaned_data["new_password"]
            seller.set_password(new_pwd)
            # Reset OTP fields cleanup
            seller.reset_otp_code = None
            seller.reset_otp_expires_at = None
            seller.reset_resend_cooldown_until = None
            seller.save()

            # Clear session
            request.session.pop("reset_seller_id", None)
            request.session.pop("reset_otp_verified", None)
            request.session.modified = True

            messages.success(request, "Password changed successfully. Please log in.")
            return redirect("seller:seller_login")
    else:
        form = PasswordResetForm()

    return render(request, "seller/forgot_password_reset.html", {"form": form})

# ===================================================>

# =================credential change ==========================>
# app/views.py

from datetime import timedelta
from .forms import CredentialOTPForm, UpdateCredentialsForm

def send_otp_email1(seller, otp):
    # Use your email backend to send OTP
    from django.core.mail import send_mail
    send_mail(
        subject="OTP for Credential Update",
        message=f"Your OTP is {otp}. It expires in 10 minutes.",
        from_email="noreply@yourbaazar.com",
        recipient_list=[seller.email]
    )
    
@require_seller_login
def request_update_credentials(request):
    seller = request.seller
    now = timezone.now()

    # Resend cooldown
    if seller.reset_resend_cooldown_until and seller.reset_resend_cooldown_until > now:
        remaining = (seller.reset_resend_cooldown_until - now).seconds
        messages.error(request, f"Please wait {remaining} seconds before resending OTP.")
        return redirect("seller:request_update_credentials")

    # Generate OTP
    otp = generate_otp()
    seller.reset_otp_code = otp
    seller.reset_otp_expires_at = now + timedelta(minutes=10)
    seller.reset_resend_cooldown_until = now + timedelta(seconds=30)
    seller.save()

    send_otp_email1(seller, otp)
    messages.success(request, "OTP sent to your registered email.")
    return redirect("seller:verify_update_otp")
@require_seller_login
def verify_update_otp(request):
    seller = request.seller

    if request.method == "POST":
        form = CredentialOTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data["otp"]
            now = timezone.now()
            if seller.reset_otp_code == otp and seller.reset_otp_expires_at > now:
                seller.reset_otp_code = None
                seller.reset_otp_expires_at = None
                seller.save()
                request.session["otp_verified"] = True
                return redirect("seller:update_credentials")
            else:
                messages.error(request, "Invalid or expired OTP.")
    else:
        form = CredentialOTPForm()

    return render(request, "seller/verify_update_otp.html", {"form": form})
@require_seller_login
def update_credentials(request):
    seller = request.seller

    if not request.session.get("otp_verified"):
        messages.error(request, "OTP verification required.")
        return redirect("seller:request_update_credentials")

    if request.method == "POST":
        form = UpdateCredentialsForm(request.POST, instance=seller)
        if form.is_valid():
            form.save()
            messages.success(request, "Credentials updated successfully!")
            request.session.pop("otp_verified")
            return redirect("seller:view_profile")
    else:
        form = UpdateCredentialsForm(instance=seller)

    return render(request, "seller/update_credentials.html", {"form": form})

# =============================================================>
def seller_logout(request):
    # पूरी session clear कर दो (safe way)
    request.session.pop("seller_id", None)
    request.session.pop("seller_draft_id", None)  # remove any draft binding
    request.session.modified = True
    # request.session.flush()
    # messages.success(request, "Logged out successfully.")
    return redirect("seller:seller_landing")


@require_seller_login
def product_list(request):
    seller = request.seller
    products = Product.objects.filter(seller=seller).order_by("-created_at")

    # If not approved, show message and hide form
    show_form = seller.is_approved
    message = None
    if not seller.is_approved:
        message = "Within 24 hrs you will be verified."

    form = ProductForm() if show_form else None
    return render(request, "seller/product_list.html", {
        "seller": seller,
        "products": products,
        "show_form": show_form,
        "message": message,
        "form": form
    })

@require_seller_login
def add_product(request):
    seller = request.seller
    if not seller.is_approved:
        messages.error(request, "Your account is not approved yet.")
        return redirect("seller:product_list")

    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            Product.objects.create(
                seller=seller,
                name=form.cleaned_data["name"],
                sku=form.cleaned_data["sku"],
                price=form.cleaned_data["price"],
                stock=form.cleaned_data["stock"],
                description=form.cleaned_data.get("description", "")
            )
            messages.success(request, "Product added.")
            return redirect("seller:product_list")
    else:
        form = ProductForm()
    return render(request, "seller/add_product.html", {"form": form})

@require_seller_login
def seller_notifications(request):
    seller = request.seller
    notifications = seller.notifications.all().order_by("-created_at")  # latest first by model Meta
    return render(request, "seller/notifications.html", {
        "notifications": notifications
    })

@require_seller_login
def mark_all_read(request):
    seller = request.seller
    seller.notifications.filter(is_read=False).update(is_read=True)
    return redirect("seller:seller_notifications")


@require_seller_login
def toggle_read(request, pk):
    note = get_object_or_404(SellerNotification, pk=pk, seller=request.seller)
    note.is_read = not note.is_read
    note.save()
    return redirect("seller:seller_notifications")


@require_seller_login
def delete_notification(request, pk):
    note = get_object_or_404(SellerNotification, pk=pk, seller=request.seller)
    note.delete()
    return redirect("seller:seller_notifications")



# Simple admin panel views (you can also use Django admin)
from django.contrib.admin.views.decorators import staff_member_required
# ==========================orders==========================
# Seller-facing Orders
EXCLUDE_ORDER_STATUSES = ["Cancelled", "Returned", "Refunded"]
EXCLUDE_ITEM_STATUSES = ["cancelled", "returned"]

def _seller_product_ids(seller):
    return list(
        SellerProductMeta.objects.filter(seller=seller).values_list("product_id", flat=True)
    )

DECIMAL12_2 = DecimalField(max_digits=12, decimal_places=2)

def _line_total_expr():
    # price (DecimalField) * quantity (IntegerField) -> wrap with explicit output_field
    return ExpressionWrapper(F("price") * F("quantity"), output_field=DECIMAL12_2)

def _seller_items_qs(seller, extra_filters=None):
    product_ids = _seller_product_ids(seller)
    qs = OrderItem.objects.filter(product_id__in=product_ids).select_related(
        "order", "product", "variant", "variant__color"
    )
    # Net sales: exclude cancelled/refunded/returned orders and cancelled/returned items
    qs = qs.exclude(order__status__in=EXCLUDE_ORDER_STATUSES).exclude(item_status__in=EXCLUDE_ITEM_STATUSES)
    if extra_filters:
        qs = qs.filter(**extra_filters)
    return qs

    

def _seller_metrics(seller, start=None, end=None, payment_method=None, status=None):
    # Common filters for both “all” and “net” calculations
    common_filters = {}
    if start and end:
        common_filters["order__created_at__date__range"] = (start, end)
    if payment_method:
        common_filters["order__payment_method__iexact"] = payment_method
    if status:
        common_filters["order__status__iexact"] = status

    product_ids = _seller_product_ids(seller)

    # 1) ALL ORDERS (for Total Orders card): no exclusion; count distinct orders containing seller’s products
    all_items_qs = OrderItem.objects.filter(product_id__in=product_ids)
    if common_filters:
        all_items_qs = all_items_qs.filter(**common_filters)

    total_orders_all = all_items_qs.values_list("order_id", flat=True).distinct().count()

    # 2) Cancelled / Returned Orders counts (distinct orders touching seller and in these statuses)
    cancelled_orders = all_items_qs.filter(order__status__iexact="Cancelled").values_list("order_id", flat=True).distinct().count()
    returned_orders = all_items_qs.filter(order__status__iexact="Returned").values_list("order_id", flat=True).distinct().count()

    # 3) NET METRICS (exclude cancelled/returned/refunded orders and cancelled/returned items)
    net_items_qs = _seller_items_qs(seller, extra_filters=common_filters)

    total_items_net = net_items_qs.aggregate(n=Coalesce(Sum("quantity"), Value(0)))["n"]

    line_total = _line_total_expr()

    cod_sales_net = net_items_qs.filter(order__payment_method__iexact="cod").aggregate(
        s=Coalesce(Sum(line_total, output_field=DECIMAL12_2), Value(0, output_field=DECIMAL12_2))
    )["s"]

    online_sales_net = net_items_qs.exclude(order__payment_method__iexact="cod")\
    .filter(order__payment_status__in=["pending","paid", "completed", "success"])\
    .aggregate(
        s=Coalesce(Sum(_line_total_expr(), output_field=DECIMAL12_2), Value(0, output_field=DECIMAL12_2))
    )["s"]
    print(list(net_items_qs.values("order_id", "order__payment_status", "order__payment_method")))


    return {
        # Cards
        "total_orders_all": total_orders_all,     # All orders (distinct)
        "cancelled_orders": cancelled_orders,     # Distinct cancelled orders
        "returned_orders": returned_orders,       # Distinct returned orders

        # Net KPIs
        "total_items": total_items_net,
        "cod_sales": cod_sales_net,
        "online_sales": online_sales_net,
    }




@require_seller_login
def seller_order_list(request):
    seller = request.seller

    q = request.GET.get("q", "").strip()
    payment_method = request.GET.get("payment_method", "").strip()
    status = request.GET.get("status", "").strip()
    start_date = request.GET.get("start", "").strip()
    end_date = request.GET.get("end", "").strip()

    product_ids = _seller_product_ids(seller)

    # TABLE (no default exclusions; user filters only)
    seller_order_ids_qs = OrderItem.objects.filter(product_id__in=product_ids)

    if start_date and end_date:
        seller_order_ids_qs = seller_order_ids_qs.filter(order__created_at__date__range=(start_date, end_date))
    if payment_method:
        seller_order_ids_qs = seller_order_ids_qs.filter(order__payment_method__iexact=payment_method)
    if status:
        seller_order_ids_qs = seller_order_ids_qs.filter(order__status__iexact=status)
    if q:
        seller_order_ids_qs = seller_order_ids_qs.filter(
            Q(order__order_number__icontains=q) |
            Q(order__customer_name__icontains=q) |
            Q(order__shipping_city__icontains=q) |
            Q(product__name__icontains=q)
        )

    seller_order_ids = seller_order_ids_qs.values_list("order_id", flat=True).distinct()

    orders = (
        Order.objects.filter(id__in=seller_order_ids)
        .order_by("-created_at")
        .select_related("user")
    )

    # Subtotals map per order (seller’s items only)
    seller_subtotals_qs = (
        OrderItem.objects
        .filter(order_id__in=seller_order_ids, product_id__in=product_ids)
        .values("order_id")
        .annotate(total=Sum(_line_total_expr(), output_field=DECIMAL12_2))
    )
    seller_subtotals = {it["order_id"]: it["total"] for it in seller_subtotals_qs}

    # Seller Shipping per order:
    # Get seller’s product metas with their minimum_shipping
    seller_product_metas = SellerProductMeta.objects.filter(seller=seller, product_id__in=product_ids).values("product_id", "minimum_shipping")
    min_ship_by_product = {m["product_id"]: m["minimum_shipping"] for m in seller_product_metas}

    # Build order -> set of product_ids for this seller (to avoid double counting shipping if same product appears multiple times)
    order_products_qs = (
        OrderItem.objects
        .filter(order_id__in=seller_order_ids, product_id__in=product_ids)
        .values("order_id", "product_id")
        .distinct()
    )
    from collections import defaultdict
    seller_shipping_map = defaultdict(lambda: Decimal("0"))
    for row in order_products_qs:
        pid = row["product_id"]
        shipping_amt = Decimal(str(min_ship_by_product.get(pid, 0)))  # default 0 if meta missing
        seller_shipping_map[row["order_id"]] += shipping_amt

    # CARDS (metrics): expanded to include total shipping (net)
    metrics = _seller_metrics(
        seller,
        start=start_date or None,
        end=end_date or None,
        payment_method=payment_method or None,
        status=status or None,
    )

    # Add net total shipping to metrics cards (exclude cancelled/returned/refunded orders and cancelled/returned items)
    # Net shipping = sum of minimum_shipping for distinct products (seller’s) present in the net items result set orders.
    net_items_qs = _seller_items_qs(
        seller,
        extra_filters={
            **({"order__created_at__date__range": (start_date, end_date)} if start_date and end_date else {}),
            **({"order__payment_method__iexact": payment_method} if payment_method else {}),
            **({"order__status__iexact": status} if status else {}),
        },
    )
    net_order_ids = list(net_items_qs.values_list("order_id", flat=True).distinct())
    net_order_products = (
        OrderItem.objects
        .filter(order_id__in=net_order_ids, product_id__in=product_ids)
        .exclude(item_status__in=EXCLUDE_ITEM_STATUSES)
        .values("order_id", "product_id")
        .distinct()
    )
    total_shipping_net = Decimal("0")
    for row in net_order_products:
        pid = row["product_id"]
        total_shipping_net += Decimal(str(min_ship_by_product.get(pid, 0)))
    metrics["total_shipping"] = total_shipping_net

    paginator = Paginator(orders, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "seller/orders_list.html", {
        "page_obj": page_obj,
        "seller_subtotals": seller_subtotals,
        "seller_shipping_map": seller_shipping_map,
        "metrics": metrics,
        "q": q,
        "payment_method": payment_method,
        "status": status,
        "start": start_date,
        "end": end_date,
    })


@require_seller_login
def seller_order_detail(request, order_id):
    seller = request.seller
    product_ids = _seller_product_ids(seller)

    if not OrderItem.objects.filter(order_id=order_id, product_id__in=product_ids).exists():
        messages.error(request, "Order not available.")
        return redirect("seller_order_list")

    order = get_object_or_404(Order, id=order_id)

    # Seller's items only
    items = (
        OrderItem.objects
        .filter(order=order, product_id__in=product_ids)
        .select_related("product", "variant", "variant__color")
    )

    # Subtotal (your current logic: price * quantity)
    seller_subtotal = sum([(it.price or Decimal("0")) * it.quantity for it in items])

    # Shipping = per DISTINCT product once, using SellerProductMeta.minimum_shipping
    min_ship_by_product = {
        row["product_id"]: row["minimum_shipping"]
        for row in SellerProductMeta.objects
            .filter(seller=seller, product_id__in=product_ids)
            .values("product_id", "minimum_shipping")
    }

    distinct_pids = (
        OrderItem.objects
        .filter(order=order, product_id__in=product_ids)
        .values_list("product_id", flat=True)
        .distinct()
    )

    seller_shipping = Decimal("0")
    for pid in distinct_pids:
        seller_shipping += Decimal(str(min_ship_by_product.get(pid, 0)))

    seller_total = seller_subtotal + seller_shipping

    return render(request, "seller/order_detail.html", {
        "order": order,
        "items": items,
        "seller_subtotal": seller_subtotal,
        "seller_shipping": seller_shipping,
        "seller_total": seller_total,
    })



@require_seller_login
def seller_order_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    seller = request.seller

    # Correct relation: product → meta → seller
    items = order.items.filter(product__meta__seller=seller)

    if not items.exists():
        return HttpResponse("Unauthorized - This order has no items for you.", status=403)

    seller_subtotal = sum(item.get_total_price() for item in items)
    seller_shipping = sum(getattr(item, "shipping_cost", 0) or 0 for item in items)
    gst_percent = 18
    gst_amount = round((seller_subtotal * gst_percent) / 100, 2)
    total_amount = seller_subtotal + seller_shipping + gst_amount

    context = {
        "order": order,
        "items": items,
        "seller_subtotal": seller_subtotal,
        "seller_shipping": seller_shipping,
        "gst_percent": gst_percent,
        "gst_amount": gst_amount,
        "total_amount": total_amount,
        "seller": seller,
    }

    return render(request, "seller/invoice_view.html", context)
    


# =========================================================
@staff_member_required
def admin_seller_list(request):
    pending = Seller.objects.filter(is_approved=False).order_by("-created_at")
    approved = Seller.objects.filter(is_approved=True).order_by("-approved_at")
    return render(request, "seller/admin_seller_list.html", {
        "pending": pending,
        "approved": approved,
    })

@staff_member_required
def admin_approve_seller(request, seller_id):
    seller = get_object_or_404(Seller, id=seller_id)
    seller.is_approved = True
    seller.approved_at = timezone.now()
    seller.save()
    notify_seller_approved(seller.email)
    messages.success(request, f"Approved {seller.username}.")
    return redirect("seller:admin_seller_list")


@staff_member_required
def seller_list_admin(request):
    query = request.GET.get("q", "")
    sellers = Seller.objects.all().order_by("-created_at")  # sorting latest first

    # Search by name, email, phone
    if query:
        sellers = sellers.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |  # agar field ka naam phone hai
            Q(pan__icontains=query) |
            Q(aadhar_number__icontains=query) |
            Q(business_name__icontains=query)
        )

    # Pagination
    paginator = Paginator(sellers, 10)  # 10 sellers per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "query": query,
    }
    return render(request, "seller/seller_list.html", context)

@staff_member_required
def admin_seller_detail(request, seller_id):
    seller = get_object_or_404(Seller, id=seller_id)
   
    return render(request, "seller/admin_seller_detail.html", {
        "seller": seller,
        
    })

from django.shortcuts import render, redirect

def mainpage(request):
    # ✅ Agar seller session already set hai
    if request.session.get("seller_id"):
        return redirect("seller:seller_landing")
    
    # ✅ Agar seller login nahi hai
    return render(request, "seller/sellerindex.html")
