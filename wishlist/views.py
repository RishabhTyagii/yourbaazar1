# wishlist/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Wishlist
from product.models import product, ProductColor, ProductVariant
from cart.models import Cart, CartItem
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse

from django.contrib import messages

@login_required
@require_POST
def add_to_wishlist(request):
    product_id = request.POST.get('product_id')
    color_id = request.POST.get('color_id')
    variant_id = request.POST.get('variant_id')

    try:
        product_obj = get_object_or_404(product, id=product_id)
        color_obj = get_object_or_404(ProductColor, id=color_id) if color_id else None
        variant_obj = get_object_or_404(ProductVariant, id=variant_id) if variant_id else None

        # Check if item already exists in wishlist
        existing_item = Wishlist.objects.filter(
            user=request.user,
            product=product_obj,
            color=color_obj,
            variant=variant_obj
        ).first()

        if existing_item:
            existing_item.delete()
            return JsonResponse({
                'success': True,
                'added': False,
                'wishlist_count': Wishlist.objects.filter(user=request.user).count(),
                'message': 'Removed from wishlist'
            })
        else:
            Wishlist.objects.create(
                user=request.user,
                product=product_obj,
                color=color_obj,
                variant=variant_obj
            )
            return JsonResponse({
                'success': True,
                'added': True,
                'wishlist_count': Wishlist.objects.filter(user=request.user).count(),
                'message': 'Added to wishlist'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
def view_wishlist(request):
    items = Wishlist.objects.filter(user=request.user).select_related(
        'product', 
        'color', 
        'variant'
    )
    return render(request, 'wishlist.html', {'wishlist_items': items})



@login_required
def remove_from_wishlist(request, wishlist_id):
    item = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
    item.delete()
    messages.success(request, "Removed from wishlist.")
    return redirect('wishlist:view_wishlist')

@login_required
def move_to_cart(request, wishlist_id):
    wishlist_item = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)

    cart, created = Cart.objects.get_or_create(user=request.user)

    existing_item = CartItem.objects.filter(
        cart=cart,
        product=wishlist_item.product,
        color=wishlist_item.color,
        variant=wishlist_item.variant
    ).first()

    if existing_item:
        existing_item.quantity += 1
        existing_item.save()
    else:
        CartItem.objects.create(
            cart=cart,
            product=wishlist_item.product,
            color=wishlist_item.color,
            variant=wishlist_item.variant,
            quantity=1
        )

    wishlist_item.delete()
    messages.success(request, "Moved to cart.")
    return redirect('wishlist:view_wishlist')