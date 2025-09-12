from django.db import models
from ckeditor.fields import RichTextField
from django.conf import settings
# Create your models here.
class NavImage(models.Model):
    logo_image=models.ImageField(upload_to='nav_images/', blank=True, null=True)
    carousal_image1=models.ImageField(upload_to='nav_images/', blank=True, null=True)
    carasoul_heading=models.CharField(max_length=255, blank=True, null=True)
    carasoul_paragraph=models.TextField(blank=True, null=True)

class footer(models.Model):
    location=models.CharField(max_length=255, blank=True, null=True)
    email_primary=models.EmailField(max_length=255, blank=True, null=True)
    email_secondary=models.EmailField(max_length=255, blank=True, null=True)
    phone_primary=models.CharField(max_length=20, blank=True, null=True)
    phone_secondary=models.CharField(max_length=20, blank=True, null=True)
    about_yourself=models.TextField(blank=True, null=True)
    def __str__(self):
        return self.location
        

class social_media(models.Model):
    facebook=models.URLField(max_length=255, blank=True, null=True)
    instagram=models.URLField(max_length=255, blank=True, null=True)
    twitter=models.URLField(max_length=255, blank=True, null=True)
    linkedin=models.URLField(max_length=255, blank=True, null=True) 
    youtube=models.URLField(max_length=255, blank=True, null=True)
    
class contact_us(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name=models.CharField(max_length=255, blank=True, null=True)
    email=models.EmailField(max_length=255, blank=True, null=True)
    phone=models.CharField(max_length=20, blank=True, null=True)
    subject=models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    message=models.TextField(blank=True, null=True)
    is_resolved = models.BooleanField(default=False)  # ✅ Add this
    def __str__(self):
        return f"{self.name} - {self.subject}"
    
class HeroImage(models.Model):
    image = models.ImageField(upload_to='hero/')
    active = models.BooleanField(default=True)  # Optional flag
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Hero Image {self.id}"

class collection_card(models.Model):
    womens_image=models.ImageField(upload_to='collection_images/', blank=True, null=True)
    mens_image=models.ImageField(upload_to='collection_images/', blank=True, null=True)
    accessories_image=models.ImageField(upload_to='collection_images/', blank=True, null=True)
    womens_heading=models.CharField(max_length=255, blank=True, null=True)
    mens_heading=models.CharField(max_length=255, blank=True, null=True)
    accessories_heading=models.CharField(max_length=255, blank=True, null=True)
    womens_paragraph=models.TextField(blank=True, null=True)
    mens_paragraph=models.TextField(blank=True, null=True)
    accessories_paragraph=models.TextField(blank=True, null=True)
    def __str__(self):
        return f"Collection Card {self.id}"
    
class shop_sale(models.Model):
    sale_image=models.ImageField(upload_to='sale_images/', blank=True, null=True)
    sale_heading=models.CharField(max_length=255, blank=True, null=True)
    sale_discount=models.CharField(max_length=50, blank=True, null=True)
    sale_paragraph=models.TextField(blank=True, null=True)
    def __str__(self):
        return f"Sale {self.id}"