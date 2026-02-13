import jwt
from django.conf import settings
from seller.models import Seller
from django.http import JsonResponse
from functools import wraps


def seller_jwt_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        # 1️⃣ Authorization header check
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return JsonResponse({"error": "token_missing"}, status=401)

        token = auth.split(" ")[1]

        try:
            # 2️⃣ Decode JWT
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )

            # 3️⃣ Seller attach
            request.seller = Seller.objects.get(id=payload["seller_id"])

            # 4️⃣ Scope attach (NEW)
            request.token_scope = payload.get("scope", "")

            # 5️⃣ Scope validation (NEW & IMPORTANT)
            if "draft_write" not in request.token_scope:
                return JsonResponse(
                    {"error": "permission_denied"},
                    status=403
                )

        except Seller.DoesNotExist:
            return JsonResponse({"error": "seller_not_found"}, status=401)

        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "token_expired"}, status=401)

        except jwt.InvalidTokenError:
            return JsonResponse({"error": "invalid_token"}, status=401)

        return view_func(request, *args, **kwargs)

    return wrapper
