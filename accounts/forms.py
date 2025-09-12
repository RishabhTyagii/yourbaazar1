# accounts/forms.py
from django import forms
from .models import Customer

class CustomerRegisterForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['username', 'email','phone_number', 'password']

class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6)

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['username', 'email', 'first_name', 'last_name','phone_number']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')  # pass current user in view
        super(EditProfileForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        if Customer.objects.filter(username=username).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("This username is already taken.")
        return username
class EmailForm(forms.Form):
    email = forms.EmailField()

class OTPPasswordForm(forms.Form):
    otp = forms.CharField(max_length=6)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)