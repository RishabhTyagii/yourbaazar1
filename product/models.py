from django.db import models
from django.urls import reverse
from decimal import Decimal
# from django.contrib.auth.models import User
class category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='category_images/')
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name
class subcategory(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='subcategory_images/')
    category = models.ForeignKey(category, on_delete=models.CASCADE)
    description = models.TextField()
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class product_type(models.Model):
    
    category = models.ForeignKey(category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(subcategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='product_type_images/')
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()


    def __str__(self):
        return self.name

    

class product(models.Model):
    sku = models.CharField(max_length=100)
    seller = models.ForeignKey('seller.Seller', on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    category = models.ForeignKey('category', on_delete=models.CASCADE)
    subcategory = models.ForeignKey('subcategory', on_delete=models.CASCADE)
    product_type = models.ForeignKey('product_type', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    thumbnail = models.ImageField(upload_to='products/thumbnails/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    # discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_available = models.BooleanField(default=True)
    cod_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(max_length=100, unique=True)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    shipping_charge = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('40.00'),
        help_text="Default shipping charge for this product"
    )
    length_cm = models.DecimalField(
    max_digits=6, decimal_places=2,
    default=Decimal("10.0"),
    help_text="Length of product in cm"
    )
    width_cm = models.DecimalField(
    max_digits=6, decimal_places=2,
    default=Decimal("10.0"),
    help_text="Width of product in cm"
    )
    height_cm = models.DecimalField(
    max_digits=6, decimal_places=2,
    default=Decimal("10.0"),
    help_text="Height of product in cm"
    )
    weight_kg = models.DecimalField(
    max_digits=6, decimal_places=3,
    default=Decimal("0.5"),
    help_text="Weight of product in kg"
    )

    short_description= models.TextField(max_length=100,null=True, blank=True)
   
    

    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse('product:product_detail', args=[self.id])
    def get_default_variant(self):
        return ProductVariant.objects.filter(color__product=self).order_by('price_before_discount').first()



class ProductColor(models.Model):
    product = models.ForeignKey(product, on_delete=models.CASCADE, related_name='colors')
    color_name = models.CharField(max_length=50)  # e.g. Red, Blue
    color_code = models.CharField(max_length=7, blank=True)  # Optional HEX: "#FF0000"

    image_main = models.ImageField(upload_to='color_images/', null=True, blank=True)
    image1 = models.ImageField(upload_to='color_images/', null=True, blank=True)
    image2 = models.ImageField(upload_to='color_images/', null=True, blank=True)
    image3 = models.ImageField(upload_to='color_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.color_name}"


class ProductVariant(models.Model):
    color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=50)  # e.g. S, M, L, XL
    stock = models.IntegerField(default=0)

    # ✅ Add price fields at variant level
    # price_after_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    price_before_discount = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    price_we_buy = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)

    @property
    
    def price_after_discount(self):
        return self.price_before_discount - (self.price_before_discount * self.discount / 100)

    def __str__(self):
        return f"{self.color.product.name} - {self.color.color_name} - {self.size} - ₹{self.price_before_discount}"

    @property
    def final_price(self):
        if self.discount:
            return self.price_before_discount * (1 - self.discount / 100)
        return self.price_before_discount