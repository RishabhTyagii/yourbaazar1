from django.db import models
from django.contrib.auth import get_user_model
from product.models import product, ProductVariant
from django.conf import settings
import uuid
from django.utils import timezone
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from coupon.models import *

User = get_user_model()

ORDER_STATUS_CHOICES = (
    ('Pending', 'Pending'),
    ('Processing', 'Processing'),
    ('Shipped', 'Shipped'),
    ('Out for Delivery', 'Out for Delivery'),
    ('Delivered', 'Delivered'),
    ('Cancelled', 'Cancelled'),
    ('Returned', 'Returned'),
    ('Refunded', 'Refunded'),
)

PAYMENT_METHOD_CHOICES = (
    ('cod', 'Cash on Delivery'),
    ('card', 'Credit/Debit Card'),
    ('upi', 'UPI Payment'),
    ('wallet', 'Wallet'),
    ('netbanking', 'Net Banking'),
)

def generate_tracking_id():
    return str(uuid.uuid4())[:12].upper()

def generate_order_number():
    """Generate a unique order number combining date and UUID"""
    date_part = timezone.now().strftime('%Y%m%d')
    unique_part = uuid.uuid4().hex[:6].upper()
    return f"ORD-{date_part}-{unique_part}"

class Order(models.Model):
    """
    Main order model representing a customer's purchase
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, editable=False, default=generate_order_number)
    tracking_id = models.CharField(max_length=20, default=generate_tracking_id, unique=True)
    
    # Customer information
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    
    # Shipping information
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_pin_code = models.CharField(max_length=10)
    shipping_country = models.CharField(max_length=100, default='India')
    
    # Order details
    status = models.CharField(
        max_length=20, 
        choices=ORDER_STATUS_CHOICES, 
        default='Pending'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cod'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ),
        default='pending'
    )
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_details = models.JSONField(blank=True, null=True)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    
    # Financials
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Free shipping threshold
    FREE_SHIPPING_THRESHOLD = Decimal('2600.00')
    
    # Shipping provider
    shipping_provider = models.CharField(max_length=50, blank=True, null=True)
    awb_code = models.CharField(max_length=100, blank=True, null=True)
    courier_name = models.CharField(max_length=100, blank=True, null=True)
    tracking_url = models.URLField(blank=True, null=True)
    shipment_id = models.CharField(max_length=100, blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    notes = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['tracking_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        """Override save to ensure unique order number generation"""
        if not self.order_number:
            self.order_number = generate_order_number()
            while Order.objects.filter(order_number=self.order_number).exists():
                self.order_number = generate_order_number()
        
        if not self.tracking_id:
            self.tracking_id = generate_tracking_id()
            while Order.objects.filter(tracking_id=self.tracking_id).exists():
                self.tracking_id = generate_tracking_id()
        
        super().save(*args, **kwargs)
    
    def calculate_shipping_cost(self):
        """
        Calculate shipping cost dynamically (Shiprocket or free shipping rules only)
        """
        if not hasattr(self, '_shipping_calculated'):
            self._shipping_calculated = True

            # Free shipping if subtotal exceeds threshold or free shipping coupon
            if (self.subtotal >= self.FREE_SHIPPING_THRESHOLD or 
                (self.coupon and self.coupon.free_shipping)):
                self.shipping_cost = Decimal('0')
                return

            # Default to 0, actual shipping हमेशा checkout_view में Shiprocket से आएगा
            self.shipping_cost = Decimal('0')

    def calculate_totals(self):
        """Recalculate subtotal & total (shipping set externally in checkout)"""
        if self.pk:
            items = self.items.all()
            self.subtotal = sum(item.get_total_price() for item in items)

        # shipping_cost को यहाँ calculate नहीं करना है, ये checkout view से आएगी
        self.total_amount = max(
            Decimal('0'),
            self.subtotal + self.shipping_cost - self.discount_amount
        )


class OrderItem(models.Model):
    """
    Individual items within an order
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        product,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    seller = models.ForeignKey(   # ✅ ADD THIS
        "seller.Seller",
        on_delete=models.CASCADE,
        related_name="order_items",
        null=True,
        blank=True

    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    discount_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    is_free = models.BooleanField(default=False)
    
    # Tracking
    item_status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('returned', 'Returned'),
            ('cancelled', 'Cancelled'),
        ),
        default='pending'
    )
    
    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'product', 'variant'],
                name='unique_order_item'
            )
        ]
    
    def _str_(self):
        return f"{self.product.name} x{self.quantity} (Order #{self.order.order_number})"
    
    def get_unit_price(self):
        """Get the unit price after discount"""
        if self.is_free:
            return Decimal('0')
        price = self.price if self.price is not None else Decimal('0')
        discount = self.discount_price if self.discount_price is not None else Decimal('0')
        return max(Decimal('0'), price - discount)

    def get_total_price(self):
        """Get total price for the line item"""
        return self.get_unit_price() * self.quantity
    
    def save(self, *args, **kwargs):
        """Ensure price is properly set before saving"""
        if self.is_free:
            self.price = Decimal('0')
            self.discount_price = Decimal('0')
        else:
            if self.variant:
                self.price = self.variant.price_after_discount
            else:
                self.price = self.product.price  # fallback if no variant, optional

        if self.discount_price is None:
            self.discount_price = Decimal('0')
    
        if self.price < Decimal('0'):
            raise ValueError("Price cannot be negative")
        if self.discount_price < Decimal('0'):
            raise ValueError("Discount price cannot be negative")
        if self.get_total_price() < Decimal('0'):
            raise ValueError("Item total price cannot be negative")
        
        super().save(*args, **kwargs)

        if self.order_id:
            self.order.calculate_totals()
            self.order.save()


def return_image_upload_path(instance, filename):
    return f'return_images/{instance.user.id}/{filename}'

class ReturnRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='return_requests')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='return_requests')

    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)

    reason = models.TextField(blank=True, null=True)

    image1 = models.ImageField(upload_to=return_image_upload_path, blank=True, null=True)
    image2 = models.ImageField(upload_to=return_image_upload_path, blank=True, null=True)
    image3 = models.ImageField(upload_to=return_image_upload_path, blank=True, null=True)
    image4 = models.ImageField(upload_to=return_image_upload_path, blank=True, null=True)

    is_resolved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Return Request"
        verbose_name_plural = "Return Requests"
        ordering = ['-created_at']

    def __str__(self):
        return f"Return - {self.order.order_number} - {self.order_item.product.name}"

    def has_at_least_one_image(self):
        return any([self.image1, self.image2, self.image3, self.image4])


