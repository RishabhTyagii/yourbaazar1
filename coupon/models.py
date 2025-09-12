#coupon/models.py
from django.contrib.auth.decorators import login_required
from django.db import models
from django.conf import settings
from product.models import product  # Adjust if product model name is capitalized
import datetime
from datetime import timedelta
from django.utils import timezone

from django.db import models
from django.utils import timezone  # ✅ Required for status logic
from product.models import product

class Coupon(models.Model):
    COUPON_TYPE_CHOICES = [
        ('percent', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('free_shipping', 'Free Shipping'),
        ('free_product', 'Free Product'),
        ('cashback', 'Cashback'),
    ]

    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='coupon_images/', null=True, blank=True)

    type = models.CharField(max_length=20, choices=COUPON_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    min_cart_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    first_time_only = models.BooleanField(default=False)
    one_time_use = models.BooleanField(default=False)
    uses_per_user = models.PositiveIntegerField(default=1)

    free_product = models.ForeignKey(product, null=True, blank=True, on_delete=models.SET_NULL, related_name='free_product_coupons')
    cashback_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    products = models.ManyToManyField(product, blank=True, related_name='product_coupons', help_text="Leave blank to apply to all products.")

    def __str__(self):
        return self.code

    @property
    def times_used(self):
        return self.usages.count() 

    def is_valid(self, user=None):
        now = timezone.now()
        if not self.is_active or not (self.valid_from <= now <= self.valid_to):
            return False

        if self.max_uses is not None:
            total_used = CouponUsage.objects.filter(coupon=self).count()
            if total_used >= self.max_uses:
                return False

        if user:
            user_used = CouponUsage.objects.filter(coupon=self, user=user).count()
            if user_used >= self.uses_per_user:
                return False

        return True

    # ✅ NEW: Dynamic Status Property
    @property
    def status(self):
        now = timezone.now()
        if self.valid_to and self.valid_to < now:
            return 'Expired'
        if not self.is_active:
            return 'Inactive'
        return 'Active'
    def coupon_type(self):
        return self.type



class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)
    discount_given = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order = models.ForeignKey('order.Order', on_delete=models.CASCADE,null=True, blank=True)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    def _str_(self):
        return f"{self.user.username} used {self.coupon.code}"


class AutoRewardRule(models.Model):
    name = models.CharField(max_length=255)

    # Trigger conditions
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_total_spent = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    min_order_count = models.PositiveIntegerField(null=True, blank=True)
    min_items_per_order = models.PositiveIntegerField(null=True, blank=True)
    # Validity
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} → {self.coupon.code}"
