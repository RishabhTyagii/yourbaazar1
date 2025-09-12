# app/forms.py
from django import forms
from django.core.exceptions import ValidationError
from seller.models import Seller

class SellerRegisterForm(forms.Form):
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)
    username = forms.CharField(max_length=150)
    business_name = forms.CharField(max_length=255)
    owner_name = forms.CharField(max_length=255)
    address = forms.CharField(widget=forms.Textarea)
    
    # Additional fields for seller registration
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)
    pincode = forms.CharField(max_length=10)
    bank_account_name = forms.CharField(max_length=150, required=False)
    bank_account_no = forms.CharField(max_length=40, required=False)
    ifsc = forms.CharField(max_length=20, required=False)
    upi_id=forms.CharField(max_length=100,required=False)
    # Optional fields
    # gst and pan are optional for initial registration
    gst = forms.CharField(max_length=20, required=False)
    pan = forms.CharField(max_length=20, required=False)
    pan_photo = forms.ImageField(required=False)
    aadhar_number = forms.CharField(required=False)
    aadhar_photo = forms.ImageField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("confirm_password"):
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned



class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6)

class SellerLoginForm(forms.Form):
    # Seller email या username दोनों से login सपोर्ट
    identifier = forms.CharField(label="Email or Username", max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = Seller
        fields = ["username", "phone",'email',"business_name", "owner_name", "gst","bank_account_name","bank_account_no", "ifsc", 'upi_id',"pan", 'aadhar_number',"address", "city", "state", "pincode"]
        widgets = {
            "bank_account_no": forms.NumberInput(attrs={"readonly": "readonly"}),
            "email": forms.TextInput(attrs={"readonly": "readonly"}),
            "business_name": forms.TextInput(attrs={"readonly": "readonly"}),
            "bank_account_name": forms.TextInput(attrs={"readonly": "readonly"}),
            "ifsc": forms.TextInput(attrs={"readonly": "readonly"}),
            "upi_id": forms.TextInput(attrs={"readonly": "readonly"}),
        }

    def __init__(self, *args, **kwargs):
        self.seller = kwargs.pop("seller", None)
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if Seller.objects.exclude(id=self.seller.id).filter(username__iexact=username).exists():
            raise ValidationError("This username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if Seller.objects.exclude(id=self.seller.id).filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")
        return email

# app/forms.py

# from django import forms
# from django.core.exceptions import ValidationError

from django.db import models

class ForgotPasswordRequestForm(forms.Form):
    identifier = forms.CharField(label="Email or Username", max_length=150)

    def clean_identifier(self):
        identifier = self.cleaned_data["identifier"].strip()
        exists = Seller.objects.filter(
            models.Q(email__iexact=identifier) | models.Q(username__iexact=identifier)
        ).exists()
        if not exists:
            raise ValidationError("Account not found.")
        return identifier


class ForgotPasswordOTPForm(forms.Form):
    otp = forms.CharField(max_length=6)


class PasswordResetForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, min_length=6)
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=6)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password") != cleaned.get("confirm_password"):
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned
    
class UpdateCredentialRequestForm(forms.Form):
    # Seller clicks "Change Credentials" → triggers OTP send
    pass  # No fields, just button to trigger OTP

class CredentialOTPForm(forms.Form):
    otp = forms.CharField(max_length=6)

class UpdateCredentialsForm(forms.ModelForm):
    class Meta:
        model = Seller
        fields = ["email", "bank_account_no", "bank_account_name", "ifsc", "upi_id"]
        widgets = {
            "email": forms.TextInput(),
            "bank_account_no": forms.TextInput(),
            "bank_account_name": forms.TextInput(),
            "ifsc": forms.TextInput(),
            "upi_id": forms.TextInput(),
        }

    def __init__(self, *args, seller=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.seller = seller  # <-- yaha seller ko store kar lo
        self.fields["email"] # Optional, OTP verification ensures email

    def clean_email(self):
        email = self.cleaned_data["email"]
        if self.seller and Seller.objects.exclude(id=self.seller.id).filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")
        return email



class ProductForm(forms.Form):
    name = forms.CharField(max_length=255)
    sku = forms.CharField(max_length=100)
    price = forms.DecimalField(max_digits=10, decimal_places=2)
    stock = forms.IntegerField(min_value=0)
    description = forms.CharField(widget=forms.Textarea, required=False)

