from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserNotificationPreference
from .settings import otp_settings


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def user_is_created_or_save(sender, instance, created, **kwargs):
    notification_type = otp_settings.DEFAULT_NOTIFICATION_TYPE

    if created:
        UserNotificationPreference.objects.create(user=instance, notification_type=notification_type)
