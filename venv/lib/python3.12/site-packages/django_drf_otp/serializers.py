from typing import Dict

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import VerificationToken


class OTPTokenSerializer(serializers.Serializer):
    username_field = get_user_model().USERNAME_FIELD
    password = serializers.CharField(write_only=True)

    default_error_messages = {
        "no_active_account": _("No active account found with the given credentials."),
        "invalid_credentials": _(f"{username_field} or password is incorrect."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()

    def validate(self, attrs: Dict) -> Dict:
        UserModel = get_user_model()
        filters = {
            self.username_field: attrs[self.username_field],
            "is_active": True,
        }

        try:
            user = UserModel.objects.get(**filters)
        except UserModel.DoesNotExist:
            raise ValidationError(
                detail=self.error_messages["no_active_account"],
                code="no_active_account",
            )

        if not user.check_password(attrs["password"]):
            raise ValidationError(
                detail=self.error_messages["invalid_credentials"].format(self.username_field),
                code="invalid_credentials",
            )

        attrs["user"] = user
        return attrs


class OTPTokenVerifySerializer(OTPTokenSerializer):
    token = serializers.CharField(max_length=6, min_length=6)
    verification_token = serializers.PrimaryKeyRelatedField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    def validate(self, attrs: Dict) -> Dict:
        validated_data = super().validate(attrs=attrs)
        user = validated_data["user"]
        try:
            verification_token = VerificationToken.objects.get(token=attrs["token"], is_active=True, user=user)
        except VerificationToken.DoesNotExist:
            raise ValidationError(detail=_("Invalid token."), code="invalid_token")
        except VerificationToken.MultipleObjectsReturned:
            VerificationToken.objects.filter(token=attrs["token"], is_active=True, user=user).update(is_active=False)
            raise ValidationError(detail=_("Invalid token."), code="invalid_token")

        from .services import OTPService

        verified = OTPService().verify_verification_token(verification_token=verification_token)
        if not verified:
            raise ValidationError(detail=_("Token has expired."), code="token_expired")

        verification_token.is_active = False
        verification_token.save(update_fields=["is_active"])

        attrs["verification_token"] = verification_token
        attrs["user"] = user
        return attrs


class OTPTokenResendSerializer(serializers.Serializer):
    username_field = get_user_model().USERNAME_FIELD

    default_error_messages = {
        "no_active_account": _("No active account found with the given credentials."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()

    def validate(self, attrs: Dict) -> Dict:
        UserModel = get_user_model()
        filters = {
            self.username_field: attrs[self.username_field],
            "is_active": True,
        }
        try:
            user = UserModel.objects.get(**filters)
        except UserModel.DoesNotExist:
            raise ValidationError(
                detail=self.error_messages["no_active_account"],
                code="no_active_account",
            )

        attrs["user"] = user
        return attrs
