from abc import ABC, abstractmethod
from typing import Dict

from django.core.mail import EmailMultiAlternatives
from django.template import loader

from .enums import NotificationType
from .settings import otp_settings


class BaseNotifier(ABC):
    notification_type: NotificationType

    @abstractmethod
    def notify(self, email: str, token: str, extra_context: Dict, **kwargs) -> None:  # nocover
        raise NotImplementedError()


class EmailNotifier(BaseNotifier):
    notification_type = NotificationType.EMAIL

    def notify(self, email: str, token: str, extra_context: Dict, **kwargs) -> None:
        email_config = otp_settings.EMAIL_CONFIG
        context = {"token": token, **extra_context}

        request = context.pop("request", None)
        if request:
            context["base_url"] = request.build_absolute_uri("/")

        email = EmailMultiAlternatives(
            subject=email_config["SUBJECT"],
            body=loader.render_to_string(email_config["TEMPLATE_PATH"], context),
            to=[email],
        )
        email.content_subtype = 'html'
        email.send()
