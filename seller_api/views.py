# seller_api/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django_ratelimit.decorators import ratelimit
from django.db import transaction
from decimal import Decimal

from product.models import category, subcategory, product_type
from seller_products.models import SellerProductDraft, DraftColor, DraftVariant

from .auth import validate_api_key, generate_token
from .permissions import seller_jwt_required
from django.views.decorators.http import require_GET
# ==========
# Meta Data:
# ==========

def category_list(request):
    data = list(
        category.objects.values("id", "name")
    )
    return JsonResponse({"categories": data})

def subcategory_list(request):
    category_id = request.GET.get("category_id")
    if not category_id:
        return JsonResponse({"error": "category_id required"}, status=400)

    data = list(
        subcategory.objects.filter(category_id=category_id)
        .values("id", "name")
    )
    return JsonResponse({"subcategories": data})

def product_type_list(request):
    category_id = request.GET.get("category_id")
    subcategory_id = request.GET.get("subcategory_id")

    if not category_id or not subcategory_id:
        return JsonResponse(
            {"error": "category_id & subcategory_id required"},
            status=400
        )

    data = list(
        product_type.objects.filter(
            category_id=category_id,
            subcategory_id=subcategory_id
        ).values("id", "name")
    )

    return JsonResponse({"product_types": data})


# ================================
# AUTH TOKEN API
# ================================
@csrf_exempt
@ratelimit(
    key="ip",
    rate="10/m",
    block=True
)
def seller_token_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    api_key = data.get("api_key")
    api_secret = data.get("api_secret")

    if not api_key or not api_secret:
        return JsonResponse({"error": "API key & secret required"}, status=400)

    key_obj = validate_api_key(api_key, api_secret)
    if not key_obj:
        return JsonResponse({"error": "Invalid API credentials"}, status=401)

    token = generate_token(key_obj.seller)
    return JsonResponse({
        "access_token": token,
        "expires_in": 7200
    })


# ================================
# FULL DRAFT CREATE (ATOMIC)
# ================================
@csrf_exempt
@seller_jwt_required
@ratelimit(
    key=lambda group, request: str(request.seller.id),
    rate='30/m',
    block=True
)
def create_full_draft(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        with transaction.atomic():

            # -------------------------
            # PRODUCT BASIC DATA
            # -------------------------
            p = data.get("product")
            if not p:
                raise Exception("Product data missing")

            sku = p.get("sku")
            if not sku:
                raise Exception("SKU is required")

            # SKU uniqueness check
            if SellerProductDraft.objects.filter(sku=sku).exists():
                raise Exception("SKU already exists")

            # -------------------------
            # CATEGORY VALIDATION
            # -------------------------
            cat = category.objects.get(id=p["category_id"])
            sub = subcategory.objects.get(id=p["subcategory_id"], category=cat)
            ptype = product_type.objects.get(
                id=p["product_type_id"],
                category=cat,
                subcategory=sub
            )

            # -------------------------
            # CREATE DRAFT
            # -------------------------
            draft = SellerProductDraft.objects.create(
                seller=request.seller,
                name=p["name"],
                sku=sku,
                short_description=p.get("short_description", ""),
                description=p.get("description", ""),
                category=cat,
                subcategory=sub,
                product_type=ptype,
                brand=p.get("brand", ""),
                base_price=p.get("base_price"),
                payment_mode=p.get("payment_mode", "both"),
                status=SellerProductDraft.Status.PENDING
            )

            # -------------------------
            # COLORS & VARIANTS
            # -------------------------
            colors = data.get("colors")
            if not colors:
                raise Exception("At least one color is required")

            for c in colors:
                color = DraftColor.objects.create(
                    draft=draft,
                    color_name=c["color_name"],
                    color_code=c.get("color_code", "")
                )

                variants = c.get("variants")
                if not variants:
                    raise Exception("Each color must have at least one variant")

                for v in variants:
                    price_before = v.get("price_before_discount")
                    discount = Decimal(str(v.get("discount", 0)))

                    if price_before is not None:
                        price_before = Decimal(str(price_before))
                        price_we_buy = price_before * (Decimal("1") - discount / Decimal("100"))
                    else:
                        price_we_buy = None

                    DraftVariant.objects.create(
                        color=color,
                        size=v["size"],
                        stock=v["stock"],
                        price_before_discount=price_before,
                        discount=discount,
                        price_we_buy=price_we_buy
                    )


        color_ids = list(draft.colors.values_list("id", flat=True))

        return JsonResponse({
            "draft_id": draft.id,
            "color_ids": color_ids,
            "status": "complete_draft_created"
        })


    except category.DoesNotExist:
        return JsonResponse({"error": "Invalid category"}, status=400)
    except subcategory.DoesNotExist:
        return JsonResponse({"error": "Invalid subcategory for selected category"}, status=400)
    except product_type.DoesNotExist:
        return JsonResponse({"error": "Invalid product type for selected category/subcategory"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
@csrf_exempt
@seller_jwt_required
@ratelimit(
    key=lambda group, request: str(request.seller.id),
    rate='30/m',
    block=True
)
def upload_color_images(request, color_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        color = DraftColor.objects.select_related("draft").get(
            id=color_id,
            draft__seller=request.seller
        )

        for field in ["image_main", "image1", "image2", "image3"]:
            if field in request.FILES:
                setattr(color, field, request.FILES[field])

        color.save()

        return JsonResponse({
            "status": "images_uploaded",
            "color_id": color.id
        })

    except DraftColor.DoesNotExist:
        return JsonResponse({"error": "Invalid color or permission denied"}, status=404)

def ratelimit_handler(request, exception):
    return JsonResponse({
        "error": "rate_limit_exceeded",
        "detail": "Too many requests, slow down"
    }, status=429)

def save(self, *args, **kwargs):
    if self.price_before_discount is not None:
        discount = self.discount or Decimal("0")
        self.price_we_buy = self.price_before_discount * (
            Decimal("1") - discount / Decimal("100")
        )
    super().save(*args, **kwargs)

@require_GET
@seller_jwt_required
@ratelimit(
    key=lambda group, request: str(request.seller.id),  
    rate='30/m',
    block=True
)
def sku_list_view(request):

    skus = list(
        SellerProductDraft.objects.filter(
            seller=request.seller
        ).values_list("sku", flat=True)
    )

    return JsonResponse({
        "skus": skus,
        "count": len(skus)
    })