from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import CheckoutForm, ReturnRequestForm, OrderStatusUpdateForm
from .models import Order, ORDER_STATUS_CHOICES
from product.models import product
from cart.models import Cart
from order.models import OrderItem,Order
from cart.cart import CartService
from coupon.models import Coupon, CouponUsage
from coupon.assign_coupons import evaluate_reward_rules
import qrcode
import base64
from io import BytesIO
import logging
import razorpay
from decimal import Decimal
from .models import ReturnRequest
from django.db import transaction
from django.template.loader import get_template
from django.core.mail import EmailMessage
from io import BytesIO
from xhtml2pdf import pisa
from django.utils.timezone import localtime
from seller.utils import notify_sellers_new_order
# views.py (imports ke saath top par)
from .shiprocket import ShiprocketClient



logger = logging.getLogger(__name__)


@login_required
def payment_success_view(request):
    payment_id = request.GET.get('payment_id')
    data = request.session.get('checkout_data')

    if not data:
        return HttpResponse("Session expired. Please try again.")

    form_data = data['form_data']
    cart_items = data['cart']
    total_price = data['total_price']

    # Create the main order
    order = Order(
        user=request.user,
        payment_method='card',
        payment_id=payment_id,
        payment_status='completed',
        subtotal=total_price['subtotal'],
        shipping_cost=total_price['shipping'],
        discount_amount=total_price.get('discount', 0),
        total_amount=total_price['total'],
        **form_data
    )
    order.save()

    # Create order items
    for item in cart_items:
        product_obj = item['product']
        variant = item.get('variant')
        quantity = item['quantity']
        
        OrderItem.objects.create(
            order=order,
            product=product_obj,
            variant=variant,
            quantity=quantity,
            price=variant.price_after_discount if variant else product_obj.get_price_after_discount(),
            discount_price=0
        )
        
        # Update stock
        if variant:
            variant.stock -= quantity
            variant.save()
        else:
            product_obj.stock -= quantity
            product_obj.save()

    # Clear cart
    if request.user.is_authenticated:
        Cart.objects.filter(user=request.user).delete()
    request.session.pop('checkout_data', None)

    # 🚀 Shiprocket order placement block
    try:
        from .shiprocket import ShiprocketClient
        sr = ShiprocketClient()
        result = sr.create_order(order)
        if result.get("success"):
            order.shipping_provider = "Shiprocket"
            order.awb_code = result.get("awb")
            order.courier_name = result.get("courier")
            order.tracking_url = result.get("tracking")
            order.save(update_fields=["shipping_provider","awb_code","courier_name","tracking_url","updated_at"])
        else:
            note = f"Shiprocket create failed: {result.get('error')} (code={result.get('code')})"
            order.notes = (order.notes or "") + ("\n" if order.notes else "") + note
            order.save(update_fields=["notes","updated_at"])
    except Exception as e:
        order.notes = (order.notes or "") + ("\n" if order.notes else "") + f"Shiprocket exception: {e}"
        order.save(update_fields=["notes","updated_at"])
    # 🚀 end Shiprocket block

    return redirect('order_success')

@staff_member_required
def print_pending_invoices(request):
    pending_orders = Order.objects.filter(status='Pending').distinct()
    receipts = []

    for order in pending_orders:
        qr_img = qrcode.make(str(order.tracking_id))
        qr_io = BytesIO()
        qr_img.save(qr_io, format='PNG')
        qr_base64 = base64.b64encode(qr_io.getvalue()).decode()

        receipts.append({
            'order': order,
            'order_items': order.items.all(),
            'subtotal': order.subtotal,
            'shipping': order.shipping_cost,
            'grand_total': order.total_amount,
            'qr_base64': qr_base64
        })

    return render(request, 'admin/all_pending_invoices.html', {'receipts': receipts})


@login_required
def invoice_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'admin/invoice.html', {
        'order': order,
        'order_items': order.items.all(),
        'unit_price': order.items.first().price if order.items.exists() else 0,
        'subtotal': order.subtotal,
        'shipping': order.shipping_cost,
        'grand_total': order.total_amount
    })
@staff_member_required
@login_required
def order_list(request):
    # Admin sees all orders, regular user sees only their own
    if request.user.is_staff or request.user.is_superuser:
        orders = Order.objects.all().order_by('-created_at')
    else:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            # Admin can edit any order, users only their own
            if request.user.is_staff or request.user.is_superuser:
                order = Order.objects.get(id=order_id)
            else:
                order = Order.objects.get(id=order_id, user=request.user)

            form = OrderStatusUpdateForm(request.POST, instance=order)
            if form.is_valid():
                form.save()
                messages.success(request, 'Order status updated successfully!')
                return redirect('order_list')
        except Order.DoesNotExist:
            messages.error(request, 'Order not found or you don\'t have permission.')
            return redirect('order_list')

    return render(request, 'admin/order_list.html', {
        'orders': orders,
        'status_form': OrderStatusUpdateForm(),
        'ORDER_STATUS_CHOICES': ORDER_STATUS_CHOICES
    })
@staff_member_required
@login_required
def order_detail(request, order_id):
    if request.user.is_staff or request.user.is_superuser:
        # Admin can access any order
        order = get_object_or_404(Order, id=order_id)
    else:
        # Regular users can only access their own ordersxxxxxxxxxxxxxxx
        order = get_object_or_404(Order, id=order_id, user=request.user)

    return render(request, 'admin/order_detail.html', {
        'order': order,
        'order_items': order.items.all()
    })



def apply_coupon_discount(summary, coupon):
    discount = Decimal('0.00')
    coupon_type = coupon.type 
    if coupon_type == 'percent':
        discount = summary['subtotal'] * Decimal(coupon.discount_value) / 100
        
    elif coupon_type == 'fixed':
        discount = Decimal(coupon.discount_value)
    elif coupon_type == 'free_shipping':
        if 'original_shipping' not in summary:
            summary['original_shipping'] = summary.get('shipping', Decimal('0.00'))
        summary['shipping'] = Decimal('0.00')
        discount = Decimal('0.00')
    elif coupon_type == 'cashback':
        # Optional: Show as cashback message
        cashback_amount = Decimal(coupon.cashback_amount or '0.00')
        summary['cashback'] = cashback_amount
        discount = Decimal('0.00')
      
    elif coupon_type == 'free_product' and coupon.free_product:
        discount = coupon.free_product.price

    summary['discount'] = discount
    summary['total'] = summary['subtotal']  + summary['shipping'] - discount
    return summary


# order/utils.py (या जहां आपने रखा हो)

from decimal import Decimal
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def calculate_summary(cart_items, shipping_zip=None, cod=False, applied_coupon=None):
    """
    Calculate subtotal, discount, and shipping (Shiprocket API se).
    """
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    discount = Decimal('0.00')
    shipping = Decimal('0.00')

    # ✅ Coupon discount calculation
    if applied_coupon:
        if applied_coupon.type == 'percentage':
            discount = (subtotal * Decimal(applied_coupon.value)) / Decimal('100')
        elif applied_coupon.type == 'fixed':
            discount = Decimal(applied_coupon.value)
        elif applied_coupon.type == 'free_shipping':
            discount = Decimal('0.00')  # shipping alag handle hoga
        elif applied_coupon.type == 'free_product':
            discount = Decimal('0.00')  # already cart_items me adjust hai

    # ✅ Shiprocket dynamic shipping calculation
    if shipping_zip:
        try:
            from .shiprocket import ShiprocketClient

            # total weight calculate
            weight = sum([
                getattr(item['product'], "weight_kg",
                        getattr(settings, "SHIPROCKET_DEFAULT_WEIGHT_KG", 0.5)) * item['quantity']
                for item in cart_items if not item.get('is_free')
            ])
            sr = ShiprocketClient()

            rates = sr.calculate_shipping(
                pickup_pincode=settings.SHIPROCKET_PICKUP_PIN,
                delivery_pincode=shipping_zip,
                weight=weight,
                cod=cod
            )

            if isinstance(rates, list) and rates:
                best_option = min(rates, key=lambda r: r.get("rate", 99999))
                shipping = Decimal(str(best_option.get("rate", "0.00")))
            else:
                logger.warning(f"No valid shipping rates: {rates}")

        except Exception as e:
            logger.error(f"Shiprocket shipping calc failed: {e}")
            # fallback: per product shipping charge
            shipping = sum(
                Decimal(str(item['product'].shipping_charge))
                for item in cart_items if not item.get('is_free') and getattr(item['product'], "shipping_charge", None)
            )

    # ✅ Free shipping rules (subtotal > 2600 OR coupon free_shipping)
    if subtotal > Decimal('2600') or (applied_coupon and applied_coupon.type == 'free_shipping'):
        shipping = Decimal('0.00')

    total = max(Decimal('0.00'), subtotal + shipping - discount)

    return {
        'subtotal': subtotal,
        'discount': discount,
        'shipping': shipping,
        'total': total
    }




logger = logging.getLogger(__name__)


# order/views.py

# order/views.py

from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from .forms import CheckoutForm
from .models import Order, OrderItem, CouponUsage
from product.models import product, ProductVariant
from cart.cart import CartService
from order.shiprocket import ShiprocketClient
import logging

import logging
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from django.conf import settings

from cart.cart import CartService
from order.forms import CheckoutForm
from order.models import Order, OrderItem
from product.models import product
from coupon.models import Coupon, CouponUsage
from order.shiprocket import ShiprocketClient

logger = logging.getLogger(__name__)

@transaction.atomic
@login_required
def checkout_view(request):
    cart_service = CartService(request)
    razorpay_order_id = None
    cod_available = True
    applied_coupon = None

    product_id = request.GET.get('product_id')
    is_single_product = bool(product_id)

    try:
        if is_single_product:
            product_obj = get_object_or_404(product, id=product_id)
            cod_available = product_obj.cod_available

            cart_items = [{
                'product': product_obj,
                'quantity': 1,
                'price': product_obj.get_price_after_discount(),
                'variant': None,
                'is_free': False
            }]

            subtotal = product_obj.get_price_after_discount()
            shipping = Decimal('0.00')
            discount = Decimal('0.00')

            if subtotal > Decimal('2600'):
                shipping = Decimal('0.00')

            summary = {
                'subtotal': subtotal,
                'shipping': shipping,
                'discount': discount,
                'tax': cart_service.calculate_tax(subtotal - discount),
                'total': subtotal + shipping - discount,
                'item_count': 1
            }

        else:
            # Full cart checkout
            if 'applied_coupon' in request.session:
                try:
                    applied_coupon = Coupon.objects.get(
                        code=request.session['applied_coupon'],
                        is_active=True,
                        valid_from__lte=timezone.now(),
                        valid_to__gte=timezone.now()
                    )
                except Coupon.DoesNotExist:
                    request.session.pop('applied_coupon', None)

            cart_items = cart_service.get_cart_items()
            summary = cart_service.get_summary()

            if applied_coupon:
                summary['discount'] = cart_service.get_coupon_discount()
                summary['total'] = summary['subtotal'] - summary['discount'] + summary['shipping']

            # COD check per product
            for item in cart_items:
                product_obj = item['product'] if isinstance(item, dict) else item.product
                if hasattr(product_obj, "cod_available") and not product_obj.cod_available:
                    cod_available = False

        # Razorpay order creation (full cart only)
        if summary['total'] > 0 and not is_single_product:
            razorpay_order_id = create_razorpay_order(summary['total'])

    except Exception as e:
        logger.error(f"Checkout processing error: {str(e)}", exc_info=True)
        messages.error(request, "Error processing your order. Please try again.")
        return redirect('view_cart')

    # Handle POST - place order
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = Order(
                    user=request.user,
                    payment_method=request.POST.get("payment_method").lower(),
                    payment_id=request.POST.get("razorpay_payment_id"),
                    **form.cleaned_data
                )
                order.save()

                subtotal = Decimal('0')
                # ✅ Always use checkout/cart shipping
                shipping = summary['shipping']

                # Save items and update stock
                for item in cart_items:
                    if isinstance(item, dict):
                        product_obj = item['product']
                        variant_obj = item['variant']
                        quantity_val = item['quantity']
                        price_val = item['price']
                        is_free_val = item.get('is_free', False)
                    else:
                        product_obj = item.product
                        variant_obj = item.variant
                        quantity_val = item.quantity
                        price_val = item.variant.price_after_discount if item.variant else item.product.price_after_discount
                        is_free_val = getattr(item, 'is_free', False)

                    OrderItem.objects.create(
                        order=order,
                        product=product_obj,
                        variant=variant_obj,
                        quantity=quantity_val,
                        price=price_val,
                        is_free=is_free_val,
                        shipping_cost=Decimal('0.00')
                    )

                    subtotal += price_val * quantity_val

                    if not is_free_val:
                        if variant_obj:
                            variant_obj.stock -= quantity_val
                            variant_obj.save()
                        else:
                            product_obj.stock -= quantity_val
                            product_obj.save()

                # ✅ Free shipping condition
                if (subtotal > Decimal('2600') or
                    (applied_coupon and applied_coupon.type == 'free_shipping')):
                    shipping = Decimal('0')

                # ✅ Final order amount update
                order.subtotal = subtotal
                order.discount_amount = summary['discount']
                order.shipping_cost = shipping
                order.total_amount = max(
                    Decimal('0'),
                    subtotal + shipping - order.discount_amount
                )
                order.save()

                # Log coupon usage
                if applied_coupon:
                    CouponUsage.objects.create(
                        coupon=applied_coupon,
                        user=request.user,
                        order=order,
                        discount_given=summary['discount'],
                        used_at=timezone.now()
                    )
                    request.session.pop('applied_coupon', None)

                # Clear cart
                if not is_single_product:
                    cart_service.clear()

                # Shiprocket order placement
                try:
                    sr = ShiprocketClient()
                    result = sr.create_order(order)
                    if result.get("success"):
                        order.shipping_provider = "Shiprocket"
                        if result.get("awb"):
                            order.awb_code = result["awb"]
                        if result.get("shipment_id"):
                            order.shipment_id = result["shipment_id"]
                        if result.get("courier"):
                            order.courier_name = result["courier"]
                        if result.get("tracking"):
                            order.tracking_url = result["tracking"]
                        order.save(update_fields=["shipping_provider", "awb_code", "shipment_id", "courier_name", "tracking_url", "updated_at"])
                    else:
                        note = f"Shiprocket create failed: {result.get('error')} (code={result.get('code')})"
                        order.notes = (order.notes or "") + ("\n" if order.notes else "") + note
                        order.save(update_fields=["notes", "updated_at"])
                except Exception as e:
                    order.notes = (order.notes or "") + ("\n" if order.notes else "") + f"Shiprocket exception: {e}"
                    order.save(update_fields=["notes", "updated_at"])

                return redirect('order_success', order_id=order.id)

            except Exception as e:
                logger.error(f"Order processing error: {str(e)}", exc_info=True)
                messages.error(request, f"Error processing your order: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CheckoutForm(initial=get_initial_data(request.user))

    return render(request, 'checkout.html', {
        'form': form,
        'cart_items': cart_items,
        'summary': summary,
        'is_single': is_single_product,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'razorpay_order_id': razorpay_order_id,
        'cod_available': cod_available,
        'applied_coupon': applied_coupon
    })


def create_razorpay_order(amount):
    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        order = client.order.create({
            "amount": int(amount * 100),
            "currency": "INR",
            "payment_capture": 1,
        })
        return order['id']
    except Exception as e:
        logger.error(f"Razorpay error: {str(e)}")
        return None

def get_initial_data(user):
    return {
        'customer_name': user.get_full_name(),
        'customer_email': user.email,
        'customer_phone': user.phone if hasattr(user, 'phone') else '',
        'shipping_address': user.address if hasattr(user, 'address') else '',
        'shipping_city': user.city if hasattr(user, 'city') else '',
        'shipping_state': user.state if hasattr(user, 'state') else '',
        'shipping_zip_code': user.zip_code if hasattr(user, 'zip_code') else '',
        'shipping_country': 'India'
    }
def create_razorpay_order(amount):
    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        order = client.order.create({
            "amount": int(amount * 100),
            "currency": "INR",
            "payment_capture": 1,
        })
        return order['id']
    except Exception as e:
        logger.error(f"Razorpay error: {str(e)}")
        return None



def render_to_pdf(template_src, context_dict={}):
    """Convert HTML template into PDF"""
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result, encoding='UTF-8')
    if pisa_status.err:
        return None
    return result.getvalue()

@login_required
def order_success(request, order_id):
    payment_id = request.GET.get('payment_id')
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # ✅ Update order payment_status on success
    with transaction.atomic():
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if payment_id:
            order.payment_status = "paid"
            order.payment_method = "online"
            order.save()

    # 1️⃣ Track applied coupon (if used at checkout)
    coupon_code = request.session.get('applied_coupon')
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if not CouponUsage.objects.filter(user=request.user, coupon=coupon, order=order).exists():
                CouponUsage.objects.create(
                    user=request.user,
                    coupon=coupon,
                    order=order
                )
            del request.session['applied_coupon']
        except Coupon.DoesNotExist:
            pass

    # 2️⃣ Admin-controlled dynamic coupon rules
    assigned = evaluate_reward_rules(request.user, order)
    if assigned:
        request.session['new_coupons'] = assigned
    
    # 3️⃣ Order success session data
    request.session['order_success_data'] = {
        'order_id': order.id,
        'payment_id': payment_id
    }
    # 2️⃣ Notify sellers about this order
    notify_sellers_new_order(order)

    return redirect('order_success')

def order_success_page(request):
    return render(request, 'order_success.html')


class OrderTrackingView(View):
    template_name = 'orders/track_order.html'

    @method_decorator(login_required(login_url='/accounts/login/'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        tracking_id = request.GET.get('tracking_id', '').strip()
        orders = []
        items = []
        
        if request.user.is_authenticated:
            orders = Order.objects.filter(user=request.user).order_by('-created_at')
        elif tracking_id:
            try:
                order = get_object_or_404(Order, tracking_id=tracking_id)
                orders = [order]
            except:
                orders = []

        if orders:
            items = OrderItem.objects.filter(order__in=orders).select_related(
                'product', 'variant', 'variant__color'
            )

        context = {
            'orders': orders,
            'items': items,
            'tracking_id': tracking_id,
        }
        return render(request, self.template_name, context)
    
    
    
    
    
    
    
    
    
    
    
    
    
    



@staff_member_required
def print_pending_receipts(request):
    orders = Order.objects.filter(status='Pending')
    all_receipts = []

    for order in orders:
        qr_img = qrcode.make(str(order.tracking_id))
        qr_io = BytesIO()
        qr_img.save(qr_io, format='PNG')
        qr_base64 = base64.b64encode(qr_io.getvalue()).decode()

        all_receipts.append({
            'order': order,
            'qr_base64': qr_base64,
        })

    return render(request, 'admin/all_pending_delivery_receipts.html', {
        'receipts': all_receipts
    })

@login_required
def invoice_view(request, order_id):
    if request.user.is_staff or request.user.is_superuser:
        # Admin can view any invoice
        order = get_object_or_404(Order, id=order_id)
    else:
        # Regular users can view only their own invoice
        order = get_object_or_404(Order, id=order_id, user=request.user)

    return render(request, 'admin/invoice.html', {
        'order': order,
        'order_items': order.items.all(),
        'unit_price': order.items.first().price if order.items.exists() else 0,
        'subtotal': order.subtotal,
        'shipping': order.shipping_cost,
        'grand_total': order.total_amount
    })

@staff_member_required
def delivery_receipt_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    qr_img = qrcode.make(str(order.tracking_id))
    qr_io = BytesIO()
    qr_img.save(qr_io, format='PNG')
    qr_base64 = base64.b64encode(qr_io.getvalue()).decode()

    return render(request, 'admin/delivery_receipt.html', {
        'order': order,
        'qr_base64': qr_base64,
    })
@staff_member_required
def admin_invoice_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('admin/invoice.html', {
        'order': order,
        'order_items': order.items.all(),
        'user': order.user,
        'subtotal': order.subtotal,
        'shipping': order.shipping_cost,
        'grand_total': order.total_amount
        
    })
    return HttpResponse(html)












@login_required
def create_return_request(request):
    if request.method == 'POST':
        form = ReturnRequestForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            return_request = form.save(commit=False)
            return_request.user = request.user
            return_request.save()
            messages.success(request, "Your return request has been submitted!")
            return redirect('return_history')
        else:
            print("Form errors:", form.errors)  # 🔍 helpful in development
    else:
        form = ReturnRequestForm(user=request.user)

    return render(request, 'orders/return_request_form.html', {'form': form})

@login_required
def return_history(request):
    returns = ReturnRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/return_history.html', {'returns': returns})
    

@login_required
def order_items_for_return(request):
    order_id = request.GET.get('order_id')
    items = []

    try:
        order_id = int(order_id)
    except (ValueError, TypeError):
        return JsonResponse({'items': items})

    delivered_items = OrderItem.objects.filter(
        order_id=order_id,
        item_status__iexact='delivered'
    )

    # Exclude ALL items that already have ANY return request
    already_requested = ReturnRequest.objects.filter(order_id=order_id).values_list('order_item_id', flat=True)

    eligible_items = delivered_items.exclude(id__in=already_requested)

    for item in eligible_items.select_related('product', 'variant', 'variant__color'):
        label = item.product.name
        if item.variant:
            color = getattr(item.variant.color, 'color_name', '')
            size = getattr(item.variant, 'size', '')
            details = ', '.join(filter(None, [color, f"Size {size}" if size else ""]))
            if details:
                label = f"{label} ({details})"
        items.append({'id': item.id, 'label': label})

    return JsonResponse({'items': items})



@staff_member_required
def return_request_admin_view(request):
    search_query = request.GET.get('q', '').strip()
    returns = ReturnRequest.objects.all()

    if search_query:
        returns = returns.filter(
            Q(customer_name__icontains=search_query) |
            Q(customer_email__icontains=search_query) |
            Q(order__order_number__icontains=search_query)
        )

    paginator = Paginator(returns, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/return_requests.html', {
        'page_obj': page_obj,
        'search_query': search_query,
    })

@require_POST
@staff_member_required
def toggle_return_status(request):
    request_id = request.POST.get('id')
    try:
        return_request = ReturnRequest.objects.get(id=request_id)
        return_request.is_resolved = not return_request.is_resolved
        return_request.save()
        return JsonResponse({'success': True, 'new_status': return_request.is_resolved})
    except ReturnRequest.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Return request not found'})



import requests
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Order
from .shiprocket import ShiprocketClient

@login_required
def track_orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    tracking_data = {}
    sr = ShiprocketClient()

    for order in orders:
        try:
            if order.awb_code:
                url = f"{sr.BASE}/courier/track/awb/{order.awb_code}"
                res = requests.get(url, headers=sr._headers(), timeout=20)

                if res.status_code == 200:
                    data = res.json()

                    # ✅ Fix: Some Shiprocket responses nest tracking info differently
                    tracking_info = (
                        data.get("tracking_data")
                        or data.get("data", {}).get("tracking_data")
                        or {}
                    )

                    current_status = (
                        tracking_info.get("current_status")
                        or data.get("tracking_data", {}).get("shipment_status", "Not Updated Yet")
                    )

                    activities = (
                        tracking_info.get("shipment_track_activities")
                        or data.get("tracking_data", {}).get("shipment_track_activities")
                        or []
                    )

                    tracking_data[order.id] = {
                        "status": current_status,
                        "activities": activities,
                    }
                else:
                    tracking_data[order.id] = {"error": res.text}

            elif getattr(order, "shipment_id", None):
                res = requests.get(
                    f"{sr.BASE}/orders/show/{order.shipment_id}",
                    headers=sr._headers(),
                    timeout=20
                )
                if res.status_code == 200:
                    data = res.json()
                    tracking_data[order.id] = {
                        "status": data.get("status", "Pending"),
                        "activities": []
                    }
                else:
                    tracking_data[order.id] = {"status": "Pending", "activities": []}
            else:
                tracking_data[order.id] = {"status": "Pending", "activities": []}

        except Exception as e:
            tracking_data[order.id] = {"error": str(e)}

    return render(request, "orders/track_orders.html", {
        "orders": orders,
        "tracking_data": tracking_data
    })

