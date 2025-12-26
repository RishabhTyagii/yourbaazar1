import random
import string

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .enums import NotificationType, TokenType


class AbstractBaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Created date"))
    update_date = models.DateTimeField(auto_now=True, verbose_name=_("Update date"))

    class Meta:
        abstract = True


class VerificationToken(AbstractBaseModel):
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User"))
    token = models.CharField(max_length=6, verbose_name=_("Token"))
    token_type = models.CharField(
        max_length=100, choices=TokenType.choices, default=TokenType.TOTP, verbose_name=_("Token type")
    )
    secret_chars = models.CharField(max_length=256, null=True, verbose_name=_("Extra secret characters"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is active"))

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "token"], name="active_token_idx"),
        ]

    @staticmethod
    def generate_secret_chars(user: AbstractUser) -> str:
        alphanumeric_chars = string.ascii_letters + string.digits

        random_chars = "".join([random.choice(alphanumeric_chars) for i in range(10)])
        username_field_value = getattr(user, user.USERNAME_FIELD)
        timestamp = str(timezone.now().timestamp()).replace(".", "")

        secret_chars = username_field_value + random_chars + timestamp
        return secret_chars


class UserNotificationPreference(AbstractBaseModel):
    user = models.OneToOneField(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        related_name="notification_preference",
    )
    notification_type = models.CharField(
        max_length=32,
        choices=NotificationType.choices,
        default=NotificationType.EMAIL,
        verbose_name=_("Notification Type"),
    )
