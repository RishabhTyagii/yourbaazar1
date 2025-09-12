from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from coupon.models import Coupon
from product.models import * 
from decimal import Decimal

def calculate_shipping_weight(cart_items):
    """Calculate total shipping weight using maximum of actual vs volumetric weight"""
    total_weight = 0.0
    
    for item in cart_items:
        if not getattr(item, 'is_free', False):
            # Get dimensions from product
            length = item.product.length_cm or Decimal('10.0')
            breadth = item.product.width_cm or Decimal('10.0')
            height = item.product.height_cm or Decimal('10.0')
            weight = item.product.weight_kg or Decimal('0.5')
            
            # Calculate actual and volumetric weight for this item
            actual_weight = float(weight) * item.quantity
            volumetric_weight = (float(length) * float(breadth) * float(height) / 5000) * item.quantity
            
            # Use the maximum weight for shipping calculation
            item_weight = max(actual_weight, volumetric_weight)
            total_weight += item_weight
    
    # Ensure minimum weight
    return max(total_weight, 0.5)

class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
    )
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def subtotal(self):
        return sum(item.get_total_price() for item in self.items.all())

    @property
    def shipping_charge(self):
        """
        Dynamic shipping charge calculation:
        - Free shipping if subtotal > 2600 or free_shipping coupon
        - Else fetch real-time lowest courier rate from Shiprocket
        - Fallback: sum of product-level shipping_charge
        """
        from order.shiprocket import ShiprocketClient
        
        # ✅ Free shipping check
        if self.subtotal > Decimal('2600') or (self.coupon and self.coupon.type == 'free_shipping'):
            return Decimal('0')

        # ✅ Calculate package weight
        total_weight = calculate_shipping_weight(self.items.all())

        # ✅ Delivery pincode (from user's default address)
        try:
            address = self.user.addresses.filter(is_default=True).first()
            delivery_pincode = address.pin_code if address else None
        except Exception:
            delivery_pincode = None

        if not delivery_pincode:
            # fallback: product shipping charge sum
            return sum(
                Decimal(str(item.product.shipping_charge)) * item.quantity
                for item in self.items.all() if item.product.shipping_charge and not getattr(item, 'is_free', False)
            )

        # ✅ Fetch real-time shipping rate from Shiprocket
        try:
            sr = ShiprocketClient()
            rates = sr.calculate_shipping(
                delivery_pincode=delivery_pincode,
                weight=total_weight
            )
            
            if rates.get("success") and rates.get("couriers"):
                best_option = min(rates["couriers"], key=lambda r: r.get("rate", 99999))
                return Decimal(str(best_option.get("rate", "0.00")))
        except Exception as e:
            import logging
            logging.error(f"Shiprocket shipping calc failed: {e}")

        # ✅ Fallback: static sum of product shipping charges
        return sum(
            Decimal(str(item.product.shipping_charge)) * item.quantity
            for item in self.items.all() if item.product.shipping_charge and not getattr(item, 'is_free', False)
        )

    @property
    def total(self):
        subtotal = self.subtotal
        discount = Decimal('0')
        
        if self.coupon:
            if self.coupon.type == 'percentage':
                discount = subtotal * (self.coupon.discount_value / Decimal('100'))
            else:
                discount = self.coupon.discount_value

        return subtotal - discount + self.shipping_charge



class CartItem(models.Model):
    cart = models.ForeignKey('Cart', related_name='items', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(product, on_delete=models.CASCADE, null=True, blank=True)
    color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, null=True, blank=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_free = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ['cart', 'product', 'color', 'variant']

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.color.color_name}, {self.variant.size})"

    def save(self, *args, **kwargs):
        if not self.price and self.variant:
            self.price = self.variant.price_after_discount
        super().save(*args, **kwargs)

    def get_total_price(self):
        if self.is_free:
            return Decimal('0')
        return Decimal(str(self.price)) * self.quantity if self.price else Decimal('0')