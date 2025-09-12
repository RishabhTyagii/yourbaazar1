from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from coupon.models import AutoRewardRule, CouponUsage
from order.models import Order
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal

@login_required
def my_coupons_view(request):
    usages = CouponUsage.objects.filter(user=request.user).select_related('coupon')
    return render(request, 'my_coupons.html', {
        'usages': usages
    })


# coupon/reward_engine.py



def evaluate_reward_rules(user, latest_order):
    """
    Check all active AutoRewardRules and assign coupons based on user/order.
    """
    now = timezone.now()
    rules = AutoRewardRule.objects.filter(is_active=True).select_related('coupon')

    user_orders = Order.objects.filter(user=user)
    total_spent = user_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    order_count = user_orders.count()

    assigned = []

    for rule in rules:
        # ✅ Date validity check
        if rule.start_date and rule.start_date > now:
            continue
        if rule.end_date and rule.end_date < now:
            continue

        # ✅ Condition checks
        if rule.min_order_amount and latest_order.total_amount < rule.min_order_amount:
            continue
        if rule.min_order_count and order_count < rule.min_order_count:
            continue
        if rule.min_total_spent and total_spent < rule.min_total_spent:
            continue

        # ✅ NEW: Min items in this order
        if rule.min_items_per_order:
            item_count = latest_order.items.count()
            if item_count < rule.min_items_per_order:
                continue

        # ✅ Check if already assigned
        if not CouponUsage.objects.filter(user=user, coupon=rule.coupon).exists():
            CouponUsage.objects.create(user=user, coupon=rule.coupon)
            assigned.append(rule.coupon.code)

    return assigned