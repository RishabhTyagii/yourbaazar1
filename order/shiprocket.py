import requests
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class ShiprocketClient:
    BASE = "https://apiv2.shiprocket.in/v1/external"
    _token = None
    _token_time = None

    def _auth(self):
        # Re-use token for ~8 hours
        if self._token and self._token_time and (timezone.now() - self._token_time).total_seconds() < 8 * 3600:
            return self._token
        res = requests.post(f"{self.BASE}/auth/login", json={
            "email": settings.SHIPROCKET_EMAIL,
            "password": settings.SHIPROCKET_PASSWORD
        }, timeout=20)
        res.raise_for_status()
        self._token = res.json().get("token")
        self._token_time = timezone.now()
        return self._token

    def _headers(self):
        return {"Authorization": f"Bearer {self._auth()}", "Content-Type": "application/json"}

    def _payment_method(self, order):
        pm = (order.payment_method or "").lower()
        return "COD" if pm == "cod" else "Prepaid"

    def _dims_for_item(self, item):
        """ ✅ Product model se dimensions/weight nikalna """
        product = item.product
        length = product.length_cm or Decimal("10.0")
        breadth = product.width_cm or Decimal("10.0")
        height = product.height_cm or Decimal("10.0")
        weight = product.weight_kg or Decimal("0.5")

        return {
            "length": float(length),
            "breadth": float(breadth),
            "height": float(height),
            "weight": float(weight),
        }

    def build_payload(self, order):
        items = []
        total_weight = 0.0
        final_length, final_breadth, final_height = 0.0, 0.0, 0.0

        for it in order.items.select_related("product", "variant").all():
            dims = self._dims_for_item(it)
            qty = int(it.quantity or 1)

            # ✅ Actual weight
            actual_weight = dims["weight"] * qty

            # ✅ Volumetric weight
            volumetric_weight = ((dims["length"] * dims["breadth"] * dims["height"]) / 5000) * qty

            # ✅ Final weight (use the maximum)
            final_weight = max(actual_weight, volumetric_weight)

            total_weight += final_weight
            final_length = max(final_length, dims["length"])
            final_breadth = max(final_breadth, dims["breadth"])
            final_height += dims["height"] * qty

            items.append({
                "name": getattr(it.product, "name", "Item"),
                "sku": getattr(it.product, "sku", f"SKU-{it.product_id}"),
                "units": qty,
                "selling_price": float(it.get_unit_price()),
                "discount": float(it.discount_price or Decimal("0")),
                "tax": 0.0,
                "hsn": "",
                "length": dims["length"],
                "breadth": dims["breadth"],
                "height": dims["height"],
                "weight": (final_weight / qty) if qty else final_weight,
            })

        billing_shipping = {
            "name": order.customer_name,
            "address": order.shipping_address,
            "city": order.shipping_city,
            "state": order.shipping_state,
            "country": order.shipping_country or "India",
            "pincode": order.shipping_pin_code,
            "email": order.customer_email,
            "phone": order.customer_phone,
        }

        payload = {
            "order_id": order.order_number,
            "order_date": timezone.localtime(order.created_at).strftime("%Y-%m-%d %H:%M"),
            "pickup_location": settings.SHIPROCKET_PICKUP,
            "channel_id": settings.SHIPROCKET_CHANNEL_ID,
            "comment": f"Order #{order.order_number}",

            # Billing/Shipping
            "billing_customer_name": billing_shipping["name"],
            "billing_last_name": "",
            "billing_address": billing_shipping["address"],
            "billing_city": billing_shipping["city"],
            "billing_pincode": billing_shipping["pincode"],
            "billing_state": billing_shipping["state"],
            "billing_country": billing_shipping["country"],
            "billing_email": billing_shipping["email"],
            "billing_phone": billing_shipping["phone"],
            "shipping_is_billing": True,

            "order_items": items,
            "payment_method": self._payment_method(order),

            # ✅ Checkout ke same values use karni hain
            "sub_total": float(order.subtotal or 0),
            "discount": float(order.discount_amount or 0),
            "shipping_charges": float(order.shipping_cost or 0),   # 👈 FIXED
            "total_discount": float(order.discount_amount or 0),

            # ✅ Dimensions required (Shiprocket validation ke liye)
            "length": final_length or 10.0,
            "breadth": final_breadth or 10.0,
            "height": final_height or 10.0,
            "weight": max(total_weight, 0.5),
        }
        return payload

    def create_order(self, order):
        try:
            payload = self.build_payload(order)
            res = requests.post(
                f"{self.BASE}/orders/create/adhoc",
                json=payload,
                headers=self._headers(),
                timeout=30
            )
            if res.status_code >= 400:
                try:
                    j = res.json()
                    msg = j.get("message") or j
                except Exception:
                    msg = res.text
                return {"success": False, "error": str(msg), "code": res.status_code}

            data = res.json()
            shipment_id = data.get("shipment_id") or data.get("data", {}).get("shipment_id")
            awb = data.get("awb_code") or data.get("data", {}).get("awb_code")
            courier = data.get("courier_company") or data.get("data", {}).get("courier_company") or data.get("courier_name")
            tracking = data.get("tracking_url") or data.get("data", {}).get("tracking_url")

            return {
                "success": True,
                "data": data,
                "shipment_id": shipment_id,
                "awb": awb,
                "courier": courier,
                "tracking": tracking,
            }

        except requests.RequestException as e:
            return {"success": False, "error": f"network_error: {e}", "code": 0}

    def calculate_shipping(self, delivery_pincode, weight=0.5):
        try:
            payload = {
                "pickup_postcode": getattr(settings, "SHIPROCKET_PICKUP_PINCODE", "110092"),
                "delivery_postcode": str(delivery_pincode),
                "cod": 1,
                "weight": float(weight),
            }
            url = f"{self.BASE}/courier/serviceability/"
            res = requests.get(url, params=payload, headers=self._headers(), timeout=20)

            if res.status_code == 200:
                data = res.json()
                if data.get("status") == 200 and "data" in data:
                    couriers = []
                    for c in data["data"].get("available_courier_companies", []):
                        couriers.append({
                            "courier_name": c.get("courier_name"),
                            "rate": Decimal(str(c.get("rate", "0"))),
                            "etd": c.get("etd"),
                            "courier_id": c.get("courier_company_id")
                        })
                    return {"success": True, "couriers": couriers}
                return {"success": False, "error": data.get("message", "No serviceability")}
            return {"success": False, "error": res.text}
        except Exception as e:
            return {"success": False, "error": str(e)}
