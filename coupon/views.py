
from django.contrib.auth.decorators import login_required

from .models import Coupon, CouponUsage
from collections import defaultdict
from decimal import Decimal
import json
from django.http import JsonResponse
import logging

from django.db.models.functions import Coalesce
from django.db.models import Prefetch
from django.db.models import Count, Sum,DecimalField
from django.utils.timezone import localtime     

from cart.cart import CartService
from django.utils import timezone

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.utils import timezone
from coupon.models import Coupon, CouponUsage
from cart.cart import CartService
from cart.models import CartItem




logger = logging.getLogger(__name__)


@login_required
def apply_coupon_view(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            code = body.get('code')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'})

        if not code:
            return JsonResponse({
                'success': False,
                'message': 'Coupon code is required'
            })

        cart_service = CartService(request)
        cart_total = cart_service.get_cart_total()
        if isinstance(cart_total, dict):  # ✅ अगर dict है तो उसमें से 'total' निकाल ले
            cart_total = cart_total.get('total', 0)

        try:
            # Case-insensitive coupon fetch
            coupon = Coupon.objects.get(code__iexact=code, is_active=True)

            # Remove previously applied coupon
            if 'applied_coupon' in request.session:
                old_code = request.session['applied_coupon']
                try:
                    old_coupon = Coupon.objects.get(code=old_code)
                    if old_coupon.type == 'free_product' and old_coupon.free_product:
                        CartItem.objects.filter(
                            cart=cart_service.cart, 
                            product=old_coupon.free_product
                        ).delete()
                except Coupon.DoesNotExist:
                    pass

            # Validate coupon
            validation_error = validate_coupon(coupon, request.user, cart_total)
            if validation_error:
                return JsonResponse({
                    'success': False,
                    'message': validation_error
                })

            # Apply coupon
            request.session['applied_coupon'] = coupon.code
            
            # Handle free product if applicable
            if coupon.type == 'free_product' and coupon.free_product:
                if not cart_service.cart.items.filter(product=coupon.free_product).exists():
                    CartItem.objects.create(
                        cart=cart_service.cart, 
                        product=coupon.free_product, 
                        quantity=1,
                        price=Decimal('0')
                    )

            # Calculate new totals
            new_total = calculate_discounted_total(cart_service, coupon)
            
            return JsonResponse({
                'success': True,
                'message': 'Coupon applied successfully',
                'discount': str(coupon.discount_value if coupon.type == 'fixed' else f"{coupon.discount_value}%"),
                'new_total': str(new_total),
                'is_free_product': coupon.type == 'free_product'
            })

        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid coupon code'
            })
        except Exception as e:
            logger.error(f"Coupon application error: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Error applying coupon'
            })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def validate_coupon(coupon, user, cart_total):
    """Validate coupon against various conditions"""
    if coupon.valid_to and coupon.valid_to < timezone.now():
        return 'Coupon has expired.'
    
    if cart_total < coupon.min_cart_value:
        return f'Minimum cart value ₹{coupon.min_cart_value} required.'
    
    if coupon.first_time_only and CouponUsage.objects.filter(user=user).exists():
        return 'Coupon is only for first-time users.'
    
    if coupon.one_time_use and CouponUsage.objects.filter(user=user, coupon=coupon).exists():
        return 'You have already used this coupon.'
    
    return None

def calculate_discounted_total(cart_service, coupon):
    """Calculate new total after applying coupon"""
    subtotal = cart_service.get_subtotal_price()
    
    if coupon.type == 'fixed':
        return max(subtotal - coupon.discount_value, Decimal('0'))
    elif coupon.type == 'percent':
        discount = subtotal * (coupon.discount_value / Decimal('100'))
        return max(subtotal - discount, Decimal('0'))
    elif coupon.type == 'free_product':
        return subtotal  # Free product already added with price=0
    return subtotal

@login_required
def remove_coupon_view(request):
    if request.method == 'POST' and 'applied_coupon' in request.session:
        coupon_code = request.session.pop('applied_coupon')
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.type == 'free_product' and coupon.free_product:
                CartItem.objects.filter(
                    cart=CartService(request).cart,
                    product=coupon.free_product
                ).delete()
        except Coupon.DoesNotExist:
            pass
        
        return JsonResponse({
            'success': True,
            'message': 'Coupon removed successfully',
            'new_total': str(CartService(request).get_total_price())
        })
    
    return JsonResponse({
        'success': False,
        'message': 'No coupon applied'
    })

@login_required
def coupon_analytics_dashboard(request):
    # Optimized query to fetch coupons with usage counts and related data
    coupons = Coupon.objects.annotate(
        usage_count=Count('usages', distinct=True),
        total_revenue=Coalesce(
            Sum('usages__order__total_amount', output_field=DecimalField()),
            Decimal('0')
        )
    ).prefetch_related(
        Prefetch('usages', queryset=CouponUsage.objects.select_related('order')),
        'products',
        'free_product'
    ).order_by('-usage_count')

    # Initialize stats dictionary with Decimal values
    total_stats = {
        'total_coupons': Coupon.objects.count(),
        'total_used': CouponUsage.objects.count(),
        'total_fixed_discount': Decimal('0'),
        'total_percent_discount': Decimal('0'),
        'total_free_product_value': Decimal('0'),  # Cost of free products given away
        'total_revenue_fixed': Decimal('0'),
        'total_revenue_percent': Decimal('0'),
        'total_revenue_free': Decimal('0'),       # Revenue from orders with free product coupons
        'total_revenue_shipping': Decimal('0'),
        'total_revenue_cashback': Decimal('0'),
        'net_profit': Decimal('0')                # New metric: Revenue - Discounts
    }

    # Calculate values for each coupon
    for coupon in coupons:
        # Calculate discount value based on coupon type
        if coupon.type == 'fixed':
            coupon.total_value = coupon.usage_count * coupon.discount_value
            total_stats['total_fixed_discount'] += coupon.total_value
            total_stats['total_revenue_fixed'] += coupon.total_revenue
            
        elif coupon.type == 'percent':
            # Get all orders where this coupon was used
            orders = [u.order for u in coupon.usages.all() if hasattr(u, 'order') and u.order]
            percent_discount = sum(
                (coupon.discount_value / Decimal('100')) * Decimal(str(order.total_amount))

                for order in orders if hasattr(order, 'total_amount')
            )
            coupon.total_value = percent_discount
            total_stats['total_percent_discount'] += percent_discount
            total_stats['total_revenue_percent'] += coupon.total_revenue
            
        elif coupon.type == 'free_product' and coupon.free_product:
            # Free product value = product price × usage count
            free_product_value = coupon.usage_count * coupon.free_product.base_price
            coupon.total_value = free_product_value
            total_stats['total_free_product_value'] += free_product_value
            total_stats['total_revenue_free'] += coupon.total_revenue  # Full order revenue
            
        elif coupon.type == 'free_shipping':
            total_stats['total_revenue_shipping'] += coupon.total_revenue
            
        elif coupon.type == 'cashback':
            total_stats['total_revenue_cashback'] += coupon.total_revenue

    # Calculate final totals
    total_stats['total_discount'] = (
        total_stats['total_fixed_discount'] +
        total_stats['total_percent_discount'] +
        total_stats['total_free_product_value']
    )
    
    total_stats['total_revenue'] = (
        total_stats['total_revenue_fixed'] +
        total_stats['total_revenue_percent'] +
        total_stats['total_revenue_free'] +
        total_stats['total_revenue_shipping'] +
        total_stats['total_revenue_cashback']
    )
    
    total_stats['net_profit'] = (
        total_stats['total_revenue'] - 
        total_stats['total_discount']
    )

    # Prepare chart data
    usages = CouponUsage.objects.all()
    
    # Used vs Unused data
    used_unused_data = {
        'used': total_stats['total_used'],
        'unused': total_stats['total_coupons'] - total_stats['total_used']
    }
    
    # Daily usage data
    daily_usage = defaultdict(int)
    for usage in usages:
        date_str = localtime(usage.used_at).strftime('%Y-%m-%d')
        daily_usage[date_str] += 1
    
    # Revenue by type (now includes free product revenue)
    revenue_by_type = {
        'Fixed': float(total_stats['total_revenue_fixed']),
        'Percentage': float(total_stats['total_revenue_percent']),
        'Free Product': float(total_stats['total_revenue_free']),
        'Free Shipping': float(total_stats['total_revenue_shipping']),
        'Cashback': float(total_stats['total_revenue_cashback'])
    }

    context = {
        'coupons': coupons,
        'stats': {k: float(v) if isinstance(v, Decimal) else v 
                 for k, v in total_stats.items()},  # Decimal to float for template
        'used_unused_data': json.dumps(used_unused_data),
        'daily_dates': json.dumps(sorted(daily_usage.keys())),
        'daily_counts': json.dumps([daily_usage[date] for date in sorted(daily_usage.keys())]),
        'revenue_types': json.dumps(list(revenue_by_type.keys())),
        'revenue_values': json.dumps(list(revenue_by_type.values())),
    }

    return render(request, 'admin/coupon_analytics.html', context)