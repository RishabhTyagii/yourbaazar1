from django.conf import settings
from cart.models import Cart, CartItem
from product.models import product, ProductVariant
from decimal import Decimal
from django.conf import settings
from coupon.models import Coupon
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class CartService:
    def __init__(self, request):
        self.request = request
        self.user = request.user
        self.session = request.session

        if self.user.is_authenticated:
            self.cart, _ = Cart.objects.get_or_create(user=self.user)
        else:
            self.cart_key = 'anonymous_cart'
            self.cart = self.session.get(self.cart_key, {})

    def save(self):
        if not self.user.is_authenticated:
            self.session[self.cart_key] = self.cart
            self.session.modified = True

    def add_item(self, product, variant, quantity=1):
        try:
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            if variant.stock < quantity:
                raise ValueError("Not enough stock available")

            if self.user.is_authenticated:
                cart_item, created = CartItem.objects.get_or_create(
                    cart=self.cart,
                    product=product,
                    variant=variant,
                    defaults={'quantity': quantity}
                )
                if not created:
                    total_qty = cart_item.quantity + quantity
                    if total_qty > variant.stock:
                        raise ValueError("Exceeds available stock")
                    cart_item.quantity = total_qty
                    cart_item.save()
            else:
                key = f"{product.id}_{variant.id}"
                if key in self.cart:
                    total_qty = self.cart[key]['quantity'] + quantity
                    if total_qty > variant.stock:
                        raise ValueError("Exceeds available stock")
                    self.cart[key]['quantity'] = total_qty
                else:
                    self.cart[key] = {
                        'product_id': product.id,
                        'variant_id': variant.id,
                        'quantity': quantity,
                        'price': str(variant.price_after_discount),
                        'shipping_charge': str(product.shipping_charge) if product.shipping_charge else '0',
                        'image': variant.color.image_main.url if variant.color.image_main else '',
                        'product_name': product.name,
                        'color_name': variant.color.color_name,
                        'size': variant.size
                    }
                self.save()
            return True
        except Exception as e:
            logger.error(f"Add to cart failed: {e}")
            raise

    def get_cart_items(self):
        if self.user.is_authenticated:
            return self.cart.items.select_related('product', 'variant', 'variant__color')
        else:
            items = []
            for key, item in self.cart.items():
                try:
                    prod = product.objects.get(id=item['product_id'])
                    variant = ProductVariant.objects.get(id=item['variant_id']) if item['variant_id'] else None
                    items.append({
                        'product': prod,
                        'variant': variant,
                        'quantity': item['quantity'],
                        'price': Decimal(item['price']),
                        'shipping_charge': Decimal(item.get('shipping_charge', '0')),
                        'is_free': item.get('is_free', False)
                    })
                except (product.DoesNotExist, ProductVariant.DoesNotExist):
                    continue
            return items

    def clear(self):
        if self.user.is_authenticated:
            self.cart.items.all().delete()
        else:
            self.cart = {}
            self.save()

    def get_total_quantity(self):
        if self.user.is_authenticated:
            return sum(item.quantity for item in self.cart.items.all())
        return sum(item['quantity'] for item in self.cart.values())

    def get_subtotal_price(self):
        total = Decimal('0.00')
        if self.user.is_authenticated:
            for item in self.cart.items.all():
                if item.variant and not getattr(item, 'is_free', False):
                    total += item.variant.price_after_discount * item.quantity
        else:
            for item in self.cart.values():
                try:
                    if not item.get('is_free'):
                        total += Decimal(item['price']) * item['quantity']
                except Exception:
                    continue
        return total

    def calculate_shipping_charge(self):
        """Calculate shipping using Shiprocket API if pincode is set, else fallback static"""
        subtotal = self.get_subtotal_price()

        # Coupon based free shipping
        code = self.session.get('applied_coupon')
        if code:
            try:
                coupon = Coupon.objects.get(code__iexact=code)
                if coupon.type == 'free_shipping':
                    return Decimal('0.00')
            except Coupon.DoesNotExist:
                pass

        # Threshold free shipping
        if subtotal > Decimal('2600'):
            return Decimal('0.00')

        # 🔥 Try Shiprocket API if pincode already checked
        pincode = self.session.get("delivery_pincode")
        if pincode:
            try:
                from order.shiprocket import ShiprocketClient
                sr = ShiprocketClient()

                # Calculate total weight (using maximum of actual vs volumetric)
                total_weight = 0.0
                if self.user.is_authenticated:
                    for item in self.cart.items.all():
                        if not getattr(item, 'is_free', False):
                            # Get dimensions from product
                            length = item.product.length_cm or Decimal('10.0')
                            breadth = item.product.width_cm or Decimal('10.0')
                            height = item.product.height_cm or Decimal('10.0')
                            weight = item.product.weight_kg or Decimal('0.5')
                            
                            # Calculate actual and volumetric weight for this item
                            actual_weight = float(weight) * item.quantity
                            volumetric_weight = (float(length) * float(breadth) * float(height) / 5000) * item.quantity
                            
                            # Use the maximum weight for shipping calculation
                            item_weight = max(actual_weight, volumetric_weight)
                            total_weight += item_weight
                else:
                    for item in self.cart.values():
                        if not item.get('is_free', False):
                            try:
                                prod = product.objects.get(id=item['product_id'])
                                length = prod.length_cm or Decimal('10.0')
                                breadth = prod.width_cm or Decimal('10.0')
                                height = prod.height_cm or Decimal('10.0')
                                weight = prod.weight_kg or Decimal('0.5')
                                
                                # Calculate actual and volumetric weight for this item
                                actual_weight = float(weight) * item['quantity']
                                volumetric_weight = (float(length) * float(breadth) * float(height) / 5000) * item['quantity']
                                
                                # Use the maximum weight for shipping calculation
                                item_weight = max(actual_weight, volumetric_weight)
                                total_weight += item_weight
                            except product.DoesNotExist:
                                continue
                
                # Ensure minimum weight
                total_weight = max(total_weight, 0.5)

                res = sr.calculate_shipping(pincode, total_weight)
                if res.get("success") and res.get("couriers"):
                    best = min(res["couriers"], key=lambda x: x.get("rate", 99999))
                    return best["rate"]
            except Exception as e:
                logger.error(f"Shiprocket shipping error: {e}")

        # Fallback to static shipping calculation
        return self._fallback_static_shipping()

    def _fallback_static_shipping(self):
        """Fallback calculation using static product charges."""
        shipping_total = Decimal('0.00')
        if self.user.is_authenticated:
            for item in self.cart.items.all():
                if item.product.shipping_charge and not getattr(item, 'is_free', False):
                    shipping_total += Decimal(str(item.product.shipping_charge)) 
        else:
            for item in self.cart.values():
                if not item.get('is_free', False):
                    shipping_total += Decimal(item.get('shipping_charge', '0')) 
        return shipping_total

    def calculate_tax(self, taxable_amount):
        return taxable_amount * Decimal('0.00009')

    def get_free_product_price(self):
        total = Decimal('0.00')
        if self.user.is_authenticated:
            for item in self.cart.items.all():
                if getattr(item, 'is_free', False):
                    total += item.variant.price_after_discount * item.quantity
        else:
            for item in self.cart.values():
                if item.get('is_free'):
                    total += Decimal(item['price']) * item['quantity']
        return total

    def get_coupon_discount(self):
        code = self.session.get('applied_coupon')
        if not code:
            return Decimal('0.00')
        
        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            return Decimal('0.00')

        subtotal = self.get_subtotal_price()

        # Match these to your actual Coupon model fields
        if coupon.type == 'percent':
            return (coupon.discount_value / Decimal('100')) * subtotal
        elif coupon.type == 'fixed':
            return min(coupon.discount_value, subtotal)
        elif coupon.type == 'free_shipping':
            return -self.calculate_shipping_charge()
        elif coupon.type == 'free_product':
            return self.get_free_product_price()
        elif coupon.type == 'cashback':
            return Decimal('0.00')
        return Decimal('0.00')

    def get_total_price(self):
        subtotal = self.get_subtotal_price()
        discount = self.get_coupon_discount()
        shipping = self.calculate_shipping_charge()
        tax = self.calculate_tax(subtotal - discount)
        total = subtotal - discount + shipping 
        return {
            'subtotal': subtotal,
            'discount': discount,
            'shipping': shipping,
            'tax': tax,
            'total': total
        }

    def get_summary(self):
        subtotal = self.get_subtotal_price()
        discount = self.get_coupon_discount()
        shipping = self.calculate_shipping_charge()
        tax = self.calculate_tax(subtotal - discount)
        total = subtotal - discount + shipping + tax
        return {
            'subtotal': subtotal,
            'shipping': shipping,
            'tax': tax,
            'discount': discount,
            'total': total
        }

    def get_cart_total(self):
        items = self.get_cart_items()
        subtotal = Decimal('0.00')
        for item in items:
            price = item.variant.price_after_discount if self.user.is_authenticated else Decimal(item['price'])
            quantity = item.quantity if self.user.is_authenticated else item['quantity']
            subtotal += price * quantity

        shipping = self.calculate_shipping_charge()
        tax = self.calculate_tax(subtotal)
        total = subtotal + shipping 

        return {
            'subtotal': subtotal,
            'shipping': shipping,
            'tax': tax,
            'total': total,
            'item_count': len(items)
        }

    def apply_coupon(self, code):
        try:
            coupon = Coupon.objects.get(
                code__iexact=code,
                is_active=True,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now()
            )
        except Coupon.DoesNotExist:
            return False, "Invalid or expired coupon."

        self.session['applied_coupon'] = coupon.code

        if coupon.type == 'free_product' and coupon.free_product:
            item_key = f"FREE-{coupon.free_product.id}"
            for key, item in self.cart.items():
                if item['product_id'] == str(coupon.free_product.id) and item.get('is_free'):
                    break
            else:
                self.cart[item_key] = {
                    'product_id': str(coupon.free_product.id),
                    'variant_id': None,
                    'quantity': 1,
                    'price': '0.00',
                    'is_free': True
                }
                self.save()

        return True, "Coupon applied successfully."

    def remove_coupon(self):
        code = self.session.get('applied_coupon')
        if not code:
            return
        try:
            coupon = Coupon.objects.get(code__iexact=code)
            if coupon.type == 'free_product' and coupon.free_product:
                product_id = str(coupon.free_product.id)
                keys_to_remove = [key for key, item in self.cart.items()
                                if item['product_id'] == product_id and item.get('is_free')]
                for key in keys_to_remove:
                    del self.cart[key]
        except Coupon.DoesNotExist:
            pass
        self.session.pop('applied_coupon', None)
        self.save()