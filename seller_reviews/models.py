from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class SellerTestimonial(models.Model):
    seller = models.ForeignKey("seller.Seller", on_delete=models.CASCADE, related_name="testimonials")

    # Simple fields the seller fills (prefilled from Seller but editable)
    display_name = models.CharField(max_length=120, blank=True)      # e.g., "Rakesh Kumar"
    business_name = models.CharField(max_length=160, blank=True)     # e.g., "RK Traders"
    photo = models.ImageField(upload_to="seller_reviews/%Y/%m/", blank=True, null=True)

    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    experience = models.TextField()  # short paragraph

    is_approved = models.BooleanField(default=True)  # set False if you want moderation
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("seller",)]  # one public testimonial per seller (simple)
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["is_approved"]),
        ]

    def __str__(self):
        return f"{self.display_name or self.seller.username} ({self.rating}★)"
