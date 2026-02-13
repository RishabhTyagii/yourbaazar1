import jwt
from datetime import datetime, timedelta
from django.conf import settings
from seller_api.models import SellerAPIKey

JWT_SECRET = settings.SECRET_KEY
JWT_ALGO = "HS256"

def generate_token(seller):
    payload = {
        "seller_id": seller.id,
        "exp": datetime.utcnow() + timedelta(hours=2),
        "iat": datetime.utcnow(),
        "scope": "draft_write"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def validate_api_key(api_key, api_secret):
    try:
        return SellerAPIKey.objects.get(
            api_key=api_key,
            api_secret=api_secret,
            is_active=True
        )
    except SellerAPIKey.DoesNotExist:
        return None
