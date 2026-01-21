from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.db import models, transaction
from django.core.files import File
import tempfile
import subprocess
import os
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



class FestivalSlide(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    desktop_image = models.ImageField(upload_to='festival_slides/desktop/', blank=True, null=True)
    mobile_image = models.ImageField(upload_to='festival_slides/mobile/', blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title or "Untitled Slide"

    # ✅ Delete images on object delete
    def delete(self, *args, **kwargs):
        if self.desktop_image:
            self.desktop_image.delete(save=False)
        if self.mobile_image:
            self.mobile_image.delete(save=False)
        super(FestivalSlide, self).delete(*args, **kwargs)


# 🔹 Pre-save: delete old images on update
@receiver(pre_save, sender=FestivalSlide)
def delete_old_images_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return  # new object

    try:
        old_instance = FestivalSlide.objects.get(pk=instance.pk)
    except FestivalSlide.DoesNotExist:
        return

    # Desktop image
    if old_instance.desktop_image and instance.desktop_image != old_instance.desktop_image:
        old_instance.desktop_image.delete(save=False)

    # Mobile image
    if old_instance.mobile_image and instance.mobile_image != old_instance.mobile_image:
        old_instance.mobile_image.delete(save=False)


# 🔹 Post-delete: ensure images deleted from S3
@receiver(post_delete, sender=FestivalSlide)
def delete_images_on_delete(sender, instance, **kwargs):
    if instance.desktop_image:
        instance.desktop_image.delete(save=False)
    if instance.mobile_image:
        instance.mobile_image.delete(save=False)
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
import os
from io import BytesIO
from django.core.files.base import ContentFile

@receiver(post_save, sender=FestivalSlide)
def convert_images_to_webp(sender, instance, **kwargs):
    """Auto-convert uploaded FestivalSlide images to WebP on save (production safe)"""

    def convert_and_replace(field_name):
        image_field = getattr(instance, field_name)
        if not image_field:
            return

        # Skip if already .webp
        name = image_field.name.lower()
        if name.endswith(".webp"):
            return

        try:
            img = Image.open(image_field)
            img = img.convert("RGB")

            buffer = BytesIO()
            img.save(buffer, format="WEBP", quality=85)
            buffer.seek(0)

            # Build new filename
            base, _ = os.path.splitext(image_field.name)
            new_name = base + ".webp"

            # Replace file on the field
            image_field.save(new_name, ContentFile(buffer.read()), save=False)

            # Save only the updated field
            instance.save(update_fields=[field_name])

        except Exception as e:
            # Log silently (no crash in prod)
            import logging
            logging.getLogger("django").warning(f"WebP conversion failed for {field_name}: {e}")

    convert_and_replace("desktop_image")
    convert_and_replace("mobile_image")

class HomeVideo(models.Model):
    title = models.CharField(max_length=100, blank=True)
    video = models.FileField(upload_to="home_videos/")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or "Homepage Video"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # ✅ convert ONLY first time upload
        if is_new and self.video:
            transaction.on_commit(self._convert_video_s3_safe)

    def _convert_video_s3_safe(self):
        """
        S3-safe conversion:
        S3 → temp file → ffmpeg → mp4 → upload → delete original
        """

        # already converted
        if self.video.name.endswith("_h264.mp4"):
            return

        original_name = self.video.name

        # ---------- 1️⃣ DOWNLOAD FROM S3 TO TEMP ----------
        with tempfile.NamedTemporaryFile(delete=False, suffix=".input") as temp_input:
            for chunk in self.video.chunks():
                temp_input.write(chunk)
            input_path = temp_input.name

        output_path = input_path.replace(".input", "_h264.mp4")

        try:
            # ---------- 2️⃣ FFMPEG CONVERT (REAL COMPRESSION) ----------
            subprocess.run([
                "ffmpeg", "-y",
                "-i", input_path,

                # 🔻 force 720p
                "-vf", "scale=1280:-2",

                # 🎥 H.264
                "-vcodec", "libx264",
                "-preset", "slow",
                "-crf", "26",

                # 📉 bitrate cap (important)
                "-maxrate", "2000k",
                "-bufsize", "4000k",

                # 🌈 compatibility
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",

                # 🔇 remove audio
                "-an",

                output_path
            ], check=True)

            # ---------- 3️⃣ FORCE .mp4 NAME ----------
            base_name = os.path.splitext(os.path.basename(original_name))[0]
            new_name = f"{base_name}_h264.mp4"

            with open(output_path, "rb") as f:
                self.video.save(new_name, File(f), save=False)

            super().save(update_fields=["video"])

            # ---------- 4️⃣ DELETE ORIGINAL FILE FROM S3 ----------
            self.video.storage.delete(original_name)

        finally:
            # ---------- 5️⃣ CLEAN TEMP FILES ----------
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)


# 🔥 DELETE FROM S3 (ADMIN / QUERYSET / CASCADE SAFE)
@receiver(post_delete, sender=HomeVideo)
def delete_video_from_s3(sender, instance, **kwargs):
    if instance.video:
        instance.video.delete(save=False)
