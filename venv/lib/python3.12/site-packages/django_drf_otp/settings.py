from typing import Any, Dict, Optional

from django.conf import settings
from django.test.signals import setting_changed
from django.utils.translation import gettext_lazy as _

from .enums import NotificationType, TokenType

DEFAULTS = {
    "ENABLE_OTP_AUTHENTICATION": True,
    "TOKEN_LENGTH": 6,
    "TOKEN_SECRET": "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567",
    "TOTP_TOKEN_TTL": 300,
    "DEFAULT_TOKEN_TYPE": TokenType.TOTP,
    "DEFAULT_NOTIFICATION_TYPE": NotificationType.EMAIL,
    "EMAIL_CONFIG": {
        "SUBJECT": _("Verification Token"),
        "TEMPLATE_PATH": "django_drf_otp/email.html",
    },
    "OTP_DISABLED_USERS": [],
}


class Settings:
    def __init__(self, defaults: Dict, user_settings: Optional[Dict]) -> None:
        self._user_settings = user_settings
        self.defaults = defaults or DEFAULTS

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings") or self._user_settings is None:
            self._user_settings = getattr(settings, "OTP_SETTINGS", {})
        return self._user_settings

    def __getattr__(self, attr: str) -> Any:
        if attr not in self.defaults:
            raise AttributeError("Invalid API setting: '%s'" % attr)

        try:
            val = self.user_settings[attr]
        except KeyError:
            val = self.defaults[attr]
        return val

    def reload(self):
        if hasattr(self, '_user_settings'):
            delattr(self, '_user_settings')


otp_settings = Settings(DEFAULTS, None)


def reload_api_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting == 'OTP_SETTINGS':
        otp_settings.reload()


setting_changed.connect(reload_api_settings)
