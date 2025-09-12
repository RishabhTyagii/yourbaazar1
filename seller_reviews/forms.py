from django import forms
from django.forms import ClearableFileInput, TextInput, Textarea
from .models import SellerTestimonial

class SellerTestimonialForm(forms.ModelForm):
    class Meta:
        model = SellerTestimonial
        fields = ["photo", "rating", "display_name", "business_name", "experience"]
        widgets = {
            "photo": ClearableFileInput(attrs={"class": "form-control"}),

            # ⭐ Hidden rating field (value set by clicking stars in template)
            "rating": forms.HiddenInput(),

            "display_name": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Your name",
            }),
            "business_name": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Your business name",
            }),
            "experience": Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Share your experience (onboarding, listings, payouts, support, etc.)",
            }),
        }

    def clean_rating(self):
        r = self.cleaned_data.get("rating")
        try:
            r = int(r)
        except (TypeError, ValueError):
            r = None
        if not r or r < 1 or r > 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return r

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo and getattr(photo, "size", 0) > 1_000_000:  # ~1 MB
            raise forms.ValidationError("Please upload an image under 1 MB.")
        return photo
