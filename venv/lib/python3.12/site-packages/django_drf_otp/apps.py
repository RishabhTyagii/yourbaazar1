from django.apps import AppConfig


class RestFrameworkOTPConfig(AppConfig):
    name = "django_drf_otp"
    verbose_name = "Django REST framework OTP"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from .signals import user_is_created_or_save
