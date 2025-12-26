#seller_products/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from decimal import Decimal
# Adjust imports to your actual apps
from seller.models import Seller  # your existing Seller
from product.models import category, subcategory, product_type, product, ProductColor, ProductVariant
from PIL import Image
import os
from io import BytesIO
from django.core.files.base import ContentFile

class SellerProductDraft(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    seller = models.ForeignKey("seller.Seller", on_delete=models.CASCADE, related_name='product_drafts')

    # Category mapping
    category = models.ForeignKey(category, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey(subcategory, on_delete=models.SET_NULL, null=True, blank=True)
    product_type = models.ForeignKey(product_type, on_delete=models.SET_NULL, null=True, blank=True)

    # If not found, allow "other" suggestion
    category_other = models.CharField(max_length=120, blank=True)
    subcategory_other = models.CharField(max_length=120, blank=True)
    product_type_other = models.CharField(max_length=120, blank=True)

    # Core product fields (public-critical)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100)
    short_description = models.TextField(max_length=250, blank=True)
    description = models.TextField(blank=True)

    # Thumbnail/main image for the product itself
    thumbnail = models.ImageField(upload_to='drafts/thumbnails/%Y/%m/', null=True, blank=True)

    # Management fields (seller/admin)
    brand = models.CharField(max_length=120, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    minimum_shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    # Payment & shipping preferences
    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('online', 'Online Payment'),
        ('both', 'Both Available'),
    ]
    SHIPPING_CHOICES = [
        ('yourbaazar', 'Shipping by YourBaazar'),
    ]
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='both')
    shipping_by = models.CharField(max_length=15, choices=SHIPPING_CHOICES, default='yourbaazar')

    # Dimensions (for internal/shipping)
    length_cm = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    width_cm = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    height_cm = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)

    # Extended-color linkage possibility
    size_price_explanation = models.TextField(blank=True)

    # Status
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Final linkage after approval (for traceability)
    approved_product = models.ForeignKey(product, on_delete=models.SET_NULL, null=True, blank=True, related_name='source_drafts')

    class Meta:
        indexes = [
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku}) by {self.seller.username}"
    

class DraftColor(models.Model):
    draft = models.ForeignKey(SellerProductDraft, on_delete=models.CASCADE, related_name='colors')
    color_name = models.CharField(max_length=50)
    color_code = models.CharField(max_length=7, blank=True)
    image_main = models.ImageField(upload_to='drafts/color/%Y/%m/', null=True, blank=True)
    image1 = models.ImageField(upload_to='drafts/color/%Y/%m/', null=True, blank=True)
    image2 = models.ImageField(upload_to='drafts/color/%Y/%m/', null=True, blank=True)
    image3 = models.ImageField(upload_to='drafts/color/%Y/%m/', null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Auto convert all uploaded images to WebP
        for field_name in ['image_main', 'image1', 'image2', 'image3']:
            image_field = getattr(self, field_name)
            if image_field and image_field.name and not image_field.name.lower().endswith('.webp'):
                self._convert_to_webp(field_name)

    def _convert_to_webp(self, field_name):
        image_field = getattr(self, field_name)
        if not image_field:
            return
        try:
            img = Image.open(image_field)
            img = img.convert("RGB")

            webp_io = BytesIO()
            img.save(webp_io, format='WEBP', quality=80)
            webp_name = os.path.splitext(image_field.name)[0] + ".webp"

            image_field.save(webp_name, ContentFile(webp_io.getvalue()), save=False)
            super(DraftColor, self).save(update_fields=[field_name])
        except Exception as e:
            print(f"WebP conversion failed for {field_name}: {e}")

    def __str__(self):
        return f"{self.draft.name} - {self.color_name}"

class DraftVariant(models.Model):
    color = models.ForeignKey(DraftColor, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=50)
    stock = models.PositiveIntegerField(default=0)
    price_before_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(100)])
    price_we_buy = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.color.color_name} - {self.size}"

    @property
    def final_price(self):
        if self.price_before_discount is None:
            return None  # or Decimal("0.00") if you want a safe default

        discount = self.discount or Decimal("0")  # treat None as 0
        return self.price_before_discount * (Decimal("1") - discount / Decimal("100"))

class SellerProductMeta(models.Model):
    """
    Management-only meta, linked to final product for operational fields not shown on public pages.
    """
    seller = models.ForeignKey("seller.Seller", on_delete=models.CASCADE, related_name='product_meta')
    product = models.OneToOneField("product.product", on_delete=models.CASCADE, related_name='meta')
    payment_mode = models.CharField(max_length=10, choices=SellerProductDraft.PAYMENT_CHOICES, default='both')
    shipping_by = models.CharField(max_length=15, choices=SellerProductDraft.SHIPPING_CHOICES, default='yourbaazar')
    minimum_shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    length_cm = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    width_cm = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    height_cm = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    brand = models.CharField(max_length=120, blank=True)
    size_price_explanation = models.TextField(blank=True)

    def __str__(self):
        return f"Meta for {self.product.name} by {self.seller.username}"
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.product:
            self.product.shipping_charge = self.minimum_shipping
            self.product.save(update_fields=["shipping_charge"])
    
