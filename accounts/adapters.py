from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from accounts.models import Customer  # change if your user model is different

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Check if the user already exists with the same email
        if sociallogin.user.email:
            try:
                existing_user = Customer.objects.get(email=sociallogin.user.email)
                # Attach existing user to the social login
                sociallogin.connect(request, existing_user)
                raise ImmediateHttpResponse(redirect('/'))  # redirect to homepage or profile
            except Customer.DoesNotExist:
                pass
