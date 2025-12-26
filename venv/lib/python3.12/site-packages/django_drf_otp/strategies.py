import base64
import re
import typing
from abc import ABC, abstractmethod
from typing import Optional, Union

from django.contrib.auth.models import AbstractUser
from pyotp import TOTP

from .enums import TokenType
from .models import VerificationToken
from .settings import otp_settings


class BaseOTPStrategy(ABC):
    token_type: Union[TokenType, str]

    @abstractmethod
    def generate_token(self, extra_secret_chars: Optional[str] = None) -> str:  # nocover
        raise NotImplementedError()

    @abstractmethod
    def verify_token(self, token: str, extra_secret_chars: Optional[str] = None) -> bool:  # nocover
        raise NotImplementedError()

    @abstractmethod
    def generate_token_for_user(self, user: typing.Type[AbstractUser]) -> VerificationToken:  # nocover
        raise NotImplementedError()

    @staticmethod
    def create_verification_token(
        user: AbstractUser, token: str, token_type: Union[TokenType, str], secret_chars: str
    ) -> VerificationToken:
        return VerificationToken.objects.create(
            user=user, token=token, token_type=token_type, secret_chars=secret_chars
        )

    @staticmethod
    def deactivate_old_verification_tokens(verification_token: VerificationToken) -> None:
        VerificationToken.objects.filter(user=verification_token.user, is_active=True).exclude(
            id=verification_token.id
        ).update(is_active=False)


class TOTPStrategy(BaseOTPStrategy):
    token_type = TokenType.TOTP

    def generate_token(self, extra_secret_chars: Optional[str] = None) -> str:
        token_class = self._get_token_class(extra_secret_chars=extra_secret_chars)
        return token_class.now()

    def verify_token(self, token: str, extra_secret_chars: Optional[str] = None) -> bool:
        token_class = self._get_token_class(extra_secret_chars=extra_secret_chars)
        return token_class.verify(otp=token)

    def generate_token_for_user(self, user: AbstractUser) -> VerificationToken:
        secret_chars = VerificationToken.generate_secret_chars(user=user)

        email = user.email
        match = re.search(r"\+(.*?)@", email)
        if match:
            email = email.replace(match.group(0), "@")

        otp_token_data = next(
            filter(lambda x: x.get("email") == email, otp_settings.OTP_DISABLED_USERS),
            {"token": self.generate_token(extra_secret_chars=secret_chars)},
        )
        token = otp_token_data["token"]

        verification_token = self.create_verification_token(
            user=user,
            token=token,
            token_type=self.token_type,
            secret_chars=secret_chars,
        )
        self.deactivate_old_verification_tokens(verification_token=verification_token)
        return verification_token

    def _get_token_class(self, extra_secret_chars: Optional[str] = None) -> TOTP:
        base32_secret_chars = self._get_base32_secret(extra_secret_chars=extra_secret_chars)
        return TOTP(s=base32_secret_chars, digits=otp_settings.TOKEN_LENGTH, interval=otp_settings.TOTP_TOKEN_TTL)

    def _get_base32_secret(self, extra_secret_chars: Optional[str] = None) -> str:
        base32_secret_chars = otp_settings.TOKEN_SECRET
        if extra_secret_chars:
            base32_secret_chars += extra_secret_chars

        return base64.b32encode(base32_secret_chars.encode("utf-8")).decode("utf-8")
