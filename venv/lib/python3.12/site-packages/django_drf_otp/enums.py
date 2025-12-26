from django.db.models import TextChoices


class TokenType(TextChoices):
    TOTP = "totp"
    HOTP = "hotp"


class NotificationType(TextChoices):
    EMAIL = "email"
    SMS = "sms"
    AUTHENTICATOR = "authenticator"
