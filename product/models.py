#product/models.py
from django.db import models
from django.urls import reverse
from decimal import Decimal
from PIL import Image
import os
from io import BytesIO
from django.core.files.base import ContentFile


# ---------- Reusable WebP Conversion Mixin ----------
class AutoWebpMixin:
    """
    Mixin to automatically convert image fields to WebP on save.
    """
    webp_quality = 80  # Adjustable

    def convert_to_webp(self, field_name):
        image_field = getattr(self, field_name)
        if not image_field or not image_field.name:
            return

        # Skip if already .webp
        if image_field.name.lower().endswith(".webp"):
            return

        try:
            img = Image.open(image_field)
            img = img.convert("RGB")
            webp_io = BytesIO()
            img.save(webp_io, format="WEBP", quality=self.webp_quality)

            webp_name = os.path.splitext(image_field.name)[0] + ".webp"
            image_field.save(webp_name, ContentFile(webp_io.getvalue()), save=False)
        except Exception as e:
            print(f"⚠️ WebP conversion failed for {field_name}: {e}")

    def convert_all_images(self, field_list):
        for field_name in field_list:
            self.convert_to_webp(field_name)


# ---------- Category ----------
class category(AutoWebpMixin, models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='category_images/')
    slug = models.SlugField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.convert_all_images(['image'])
        super().save(update_fields=['image'])

    def __str__(self):
        return self.name


# ---------- Subcategory ----------
class subcategory(AutoWebpMixin, models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='subcategory_images/')
    category = models.ForeignKey(category, on_delete=models.CASCADE)
    description = models.TextField()
    slug = models.SlugField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.convert_all_images(['image'])
        super().save(update_fields=['image'])

    def __str__(self):
        return self.name


# ---------- Product Type ----------
class product_type(AutoWebpMixin, models.Model):
    category = models.ForeignKey(category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(subcategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='product_type_images/')
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.convert_all_images(['image'])
        super().save(update_fields=['image'])

    def __str__(self):
        return self.name


# ---------- Product ----------
class product(AutoWebpMixin, models.Model):
    sku = models.CharField(max_length=100)
    seller = models.ForeignKey('seller.Seller', on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    category = models.ForeignKey('category', on_delete=models.CASCADE)
    subcategory = models.ForeignKey('subcategory', on_delete=models.CASCADE)
    product_type = models.ForeignKey('product_type', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    thumbnail = models.ImageField(upload_to='products/thumbnails/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    is_available = models.BooleanField(default=True)
    cod_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(max_length=100, unique=True)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shipping_charge = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('40.00'),
        help_text="Default shipping charge for this product"
    )
    length_cm = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("10.0"), help_text="Length of product in cm")
    width_cm = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("10.0"), help_text="Width of product in cm")
    height_cm = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("10.0"), help_text="Height of product in cm")
    weight_kg = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal("0.5"), help_text="Weight of product in kg")
    short_description = models.TextField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.convert_all_images(['thumbnail', 'image'])
        super().save(update_fields=['thumbnail', 'image'])

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product:product_detail', args=[self.id])

    def get_default_variant(self):
        return ProductVariant.objects.filter(color__product=self).order_by('price_before_discount').first()


# ---------- ProductColor ----------
class ProductColor(AutoWebpMixin, models.Model):
    product = models.ForeignKey(product, on_delete=models.CASCADE, related_name='colors')
    color_name = models.CharField(max_length=50)
    color_code = models.CharField(max_length=7, blank=True)

    image_main = models.ImageField(upload_to='color_images/', null=True, blank=True)
    image1 = models.ImageField(upload_to='color_images/', null=True, blank=True)
    image2 = models.ImageField(upload_to='color_images/', null=True, blank=True)
    image3 = models.ImageField(upload_to='color_images/', null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.convert_all_images(['image_main', 'image1', 'image2', 'image3'])
        super().save(update_fields=['image_main', 'image1', 'image2', 'image3'])

    def __str__(self):
        return f"{self.product.name} - {self.color_name}"


# ---------- ProductVariant ----------
class ProductVariant(models.Model):
    color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=50)
    stock = models.IntegerField(default=0)
    price_before_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    price_we_buy = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    @property
    def price_after_discount(self):
        if not self.price_before_discount:
            return Decimal("0.00")
        return self.price_before_discount - (self.price_before_discount * self.discount / 100)

    def __str__(self):
        return f"{self.color.product.name} - {self.color.color_name} - {self.size} - ₹{self.price_before_discount}"

    @property
    def final_price(self):
        if not self.price_before_discount:
            return Decimal("0.00")
        discount = self.discount or Decimal("0")
        return self.price_before_discount * (Decimal("1") - discount / Decimal("100"))
