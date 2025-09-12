import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from django.http import JsonResponse
from django.contrib import messages
from product.models import product, ProductColor, ProductVariant
from .models import Cart, CartItem
from .cart import CartService
from coupon.models import Coupon


logger = logging.getLogger(__name__)

# ========== CART OPERATIONS ==========

@login_required
def add_to_cart(request, product_id, variant_id):
    try:
        logger.info(f"Add to cart request - Product: {product_id}, Variant: {variant_id}")
        
        # Get the product and verify the variant belongs to it
        product_obj = get_object_or_404(product, id=product_id)
        variant = get_object_or_404(ProductVariant, id=variant_id, color__product=product_obj)
        
        if variant.stock <= 0:
            logger.warning(f"Out of stock - Variant: {variant_id}")
            return JsonResponse({
                'success': False, 
                'message': 'This item is currently out of stock'
            }, status=400)

        cart_service = CartService(request)
        cart_service.add_item(product=product_obj, variant=variant)
        
        logger.info(f"Added to cart - {product_obj.name} ({variant.size})")
        
        return JsonResponse({
            'success': True,
            'message': f"{product_obj.name} ({variant.size}) added to cart",
            'cart_count': cart_service.get_total_quantity(),
            'item_price': str(variant.price_after_discount)
        })

    except Exception as e:
        logger.error(f"Error adding to cart: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
def buy_now(request, slug, color_id, size):
    """
    Buy now flow - clears cart and adds single item
    """
    try:
        product_obj = get_object_or_404(product, slug=slug)
        color = get_object_or_404(ProductColor, id=color_id, product=product_obj)
        variant = get_object_or_404(ProductVariant, color=color, size=size)

        if variant.stock <= 0:
            messages.warning(request, "Selected variant is out of stock.")
            return redirect('product_detail', slug=slug)

        cart_service = CartService(request)
        cart_service.clear()
        cart_service.add_item(product=product_obj, variant=variant)
        
        logger.info(f"Buy now initiated - {product_obj.name}")
        
        return redirect('checkout')

    except Exception as e:
        logger.error(f"Buy now error: {str(e)}", exc_info=True)
        messages.error(request, "Error processing your request")
        return redirect('product_detail', slug=slug)

# ========== CART MANAGEMENT ==========
@login_required
def view_cart(request):
    cart_service = CartService(request)
    cart_items = cart_service.get_cart_items()

    applied_coupon_code = request.session.get('applied_coupon')
    applied_coupon = None
    # discount = Decimal('0')

    if applied_coupon_code:
        try:
            applied_coupon = Coupon.objects.get(code=applied_coupon_code)
            # discount = cart_service.get_coupon_discount()
        except Coupon.DoesNotExist:
            del request.session['applied_coupon']

    cart_summary = cart_service.get_summary()

    context = {
        'cart_items': cart_items,
        'cart_total': cart_summary,
        'applied_coupon': applied_coupon,
    }

    return render(request, 'view_cart.html', context)

@require_POST
@login_required
def update_cart_item(request, item_id):
    try:
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            item.delete()
            message = "Item removed from cart"
        else:
            if quantity > item.variant.stock:
                return JsonResponse({
                    'success': False,
                    'message': f"Only {item.variant.stock} available in stock"
                })
            item.quantity = quantity
            item.save()
            message = "Quantity updated"
        cart_service = CartService(request)
        cart_summary = cart_service.get_summary()

        return JsonResponse({
            'success': True,
            'message': message,
            'cart_count': cart_service.get_total_quantity(),
            'subtotal': str(item.variant.price_after_discount * item.quantity) if quantity > 0 else '0',
            'cart_summary': {
                'subtotal': str(cart_summary['subtotal']),
                'shipping': str(cart_summary['shipping']),
                'tax': str(cart_summary['tax']),
                'discount': str(cart_summary.get('discount', '0')),
                'total': str(cart_summary['total']),
            }
        })

    except Exception as e:
        logger.error(f"Error updating cart item: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@require_POST
@login_required
def remove_cart_item(request, item_id):
    try:
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

        # Safely get product name for message
        if item.variant and item.variant.color and item.variant.color.product:
            product_name = item.variant.color.product.name
        elif item.product:
            product_name = item.product.name
        else:
            product_name = "Product"

        # Delete the cart item
        item.delete()

        cart_service = CartService(request)
        cart_items = cart_service.get_cart_items() 
        cart_summary = cart_service.get_summary()
        if not cart_items or len(cart_items) == 0:
            cart_service.remove_coupon()

        # Check and remove coupon if invalid or cart empty
        applied_coupon_code = request.session.get('applied_coupon')
        if applied_coupon_code:
            try:
                coupon = Coupon.objects.get(code=applied_coupon_code, is_active=True)
                # Remove coupon if cart empty or subtotal zero
                if cart_summary['subtotal'] == 0 or len(cart_service.get_cart_items()) == 0:
                    cart_service.remove_coupon()
                    messages.info(request, "Coupon removed as the cart is empty.")
                # Remove coupon if min cart value no longer met
                elif cart_summary['subtotal'] < coupon.min_cart_value:
                    cart_service.remove_coupon()
                    messages.info(request, "Coupon removed as minimum cart value is not met.")
            except Coupon.DoesNotExist:
                if 'applied_coupon' in request.session:
                    del request.session['applied_coupon']

        return JsonResponse({
            'success': True,
            'message': f"{product_name} removed from cart",
            'cart_count': cart_service.get_total_quantity(),
            'cart_summary': {
                'subtotal': str(cart_summary['subtotal']),
                'shipping': str(cart_summary['shipping']),
                'tax': str(cart_summary['tax']),
                'discount': str(cart_summary.get('discount', '0')),
                'total': str(cart_summary['total']),
            }
        })

    except Exception as e:
        logger.error(f"Error removing cart item: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': "An error occurred while removing the item from the cart."
        }, status=400)

# ========== COUPON OPERATIONS ==========
@login_required
@require_POST
def apply_coupon(request):
    code = request.POST.get('code', '').strip()
    cart_service = CartService(request)

    success, message = cart_service.apply_coupon(code)
    cart_summary = cart_service.get_summary()

    return JsonResponse({
        'success': success,
        'message': message,
        'cart_summary': {
            'subtotal': str(cart_summary['subtotal']),
            'shipping': str(cart_summary['shipping']),
            'tax': str(cart_summary['tax']),
            'discount': str(cart_summary.get('discount', '0')),
            'total': str(cart_summary['total'])
        }
    })

@require_POST
def remove_coupon(request):
    cart_service = CartService(request)
    cart_service.remove_coupon()
    cart_summary = cart_service.get_summary()

    return JsonResponse({
        'success': True,
        'message': "Coupon removed successfully.",
        'cart_summary': {
            'subtotal': str(cart_summary['subtotal']),
            'shipping': str(cart_summary['shipping']),
            'tax': str(cart_summary['tax']),
            'discount': str(cart_summary.get('discount', '0')),
            'total': str(cart_summary['total'])
        }
    })