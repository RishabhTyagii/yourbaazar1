from django.shortcuts import render, get_object_or_404,redirect
from django.http import HttpResponse
from .models import product, category, subcategory, product_type
from product.models import ProductVariant
from decimal import Decimal
from django.contrib.auth.decorators import login_required
import random
from django.template.loader import render_to_string
from django.http import HttpResponse
from dal import autocomplete

# from .forms import ProductForm 
from django.http import JsonResponse


from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import product as Product, product_type, ProductVariant, ProductColor
from product_review.models import ReviewImage
from django.db.models import Sum
from basicinfo.models import NavImage,collection_card,shop_sale,HeroImage

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def clear_order_success(request):
    if request.method == 'POST':
        if 'order_success_data' in request.session:
            request.session.pop('order_success_data')
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)



def indexpage(request):
    hero=HeroImage.objects.all()
    categories1 = category.objects.exclude(name__iexact='sales') 
    subcategory1= subcategory.objects.all()
    
    def get_sneakers(subcat_name):
        return ProductVariant.objects.filter(
            color__product__product_type__name__icontains='sneaker',
            color__product__subcategory__name__iexact=subcat_name,
            color__product__is_available=True,
            stock__gt=0
        ).select_related('color', 'color__product')[:8]
    mens_sneakers = get_sneakers('Mens')
    womens_sneakers = get_sneakers('Womens')
    kids_sneakers = get_sneakers('Kids')


    sale_products = ProductVariant.objects.filter(
    color__product__category__name__iexact='sales',
    color__product__subcategory__name__iexact='sales',
    color__product__product_type__name__iexact='sales',
    color__product__is_available=True,
    stock__gt=0
).select_related('color', 'color__product')[:8]
    
    
    product_list= product.objects.all().order_by('-created_at')
    # sales_list = sales_product.objects.all().order_by('-created_at')

    paginator1 = Paginator(product_list, 8)
    # paginator2 = Paginator(sales_list, 8)

    page_number = request.GET.get('page')
    page_obj1 = paginator1.get_page(page_number)
    # page_obj2 = paginator2.get_page(page_number)

    recent_products = []
    recently_viewed_ids = request.session.get('recently_viewed', [])
    if recently_viewed_ids:
        recent_products = Product.objects.filter(id__in=recently_viewed_ids)

    hero_image_obj = NavImage.objects.first()
    collection = collection_card.objects.first()
    sales = shop_sale.objects.all()
    # suggested product 
    all_products = list(product.objects.all())
    random_products = random.sample(all_products, min(len(all_products), 10))
    new_coupons = request.session.pop('new_coupons', None)
    kitchen_category = category.objects.filter(name__iexact="Kitchen Appliances").first()
    
    products = []
    if kitchen_category:
        # Order randomly and limit to 8 items (or any number you want)
        products = product.objects.filter(category=kitchen_category).order_by('?')[:8]
    return render(request, 'index.html', {
        'page_obj': page_obj1,
        'hero':hero,
        'collection': collection,
        'hero_image': hero_image_obj,
        'sales': sales,
        'categories': categories1,
        'subcategory':subcategory1,
        'mens_sneakers': mens_sneakers,
        'womens_sneakers': womens_sneakers,
        'kids_sneakers': kids_sneakers,
        'sale_products': sale_products,
        'recent_products': recent_products,  # ✅ pass to template
        'suggested_products': random_products,
        'new_coupons': new_coupons,
        'kitchen_appliances': kitchen_category,
        'products': products
        
    })


def all_sales_products(request):
    sale_products = ProductVariant.objects.filter(
        color__product__category__name__iexact='sales',
        color__product__subcategory__name__iexact='sales',
        color__product__product_type__name__iexact='sales',
        color__product__is_available=True,
        stock__gt=0
    ).select_related('color', 'color__product')

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(sale_products, 17)  # Show 12 products per page

    try:
        sale_products_paginated = paginator.page(page)
    except PageNotAnInteger:
        sale_products_paginated = paginator.page(1)
    except EmptyPage:
        sale_products_paginated = paginator.page(paginator.num_pages)

    context = {
        'sale_products': sale_products_paginated,
    }
    return render(request, 'sales_product.html', context)


    
def homepage_view(request):
    sneakers_variants = ProductVariant.objects.filter(
        color__product__product_type__name__iexact="Sneakers",
        color__product__is_available=True,
        stock__gt=0
    ).select_related('color', 'color__product')[:12]

    print("Total variants found:", sneakers_variants.count())
    for v in sneakers_variants:
        print(
            "Product:", v.color.product.name,
            "| Color:", v.color.color_name,
            "| Size:", v.size,
            "| Price:", v.price_after_discount,
            "| Image:", v.color.image_main.url if v.color.image_main else "No Image"
        )

    return render(request, 'index.html', {'sneakers': sneakers_variants})

def nav(request):
    categories = category.objects.all()
    subcategory2 = subcategory.objects.all()
    product_search2 = product.objects.all()
    product_type_search2 = product_type.objects.all()

    return render(request, 'partials/nav.html', {
        'categories': categories,
        'subcategory_1': subcategory2,
        'product_search': product_search2,
        'product_type_search': product_type_search2,
    })

def category_list(request):
    categories = category.objects.all()
    return render(request, 'index.html', {'categories1': categories})

def subcategory_list(request, category_id):

    try:
        # Get the category object
        category_obj = get_object_or_404(category, id=category_id)
        # Get subcategories related to that category
        subcategories = subcategory.objects.filter(category=category_obj)
        # Render the response
        return render(request, 'subcategorypage.html', {
            'category': category_obj,
            'subcategories': subcategories
        })

    except Exception as e:
        return HttpResponse(f"Error occurred: {e}")
    


def collection_view(request, collection_type):
    collection_type = collection_type.lower()

    # Get products by category or subcategory
    if collection_type == "accessories":
        products = product.objects.filter(category__name__iexact='Accessories')
    else:
        products = product.objects.filter(subcategory__name__istartswith=collection_type)

    products = products.distinct()

    # Calculate discount percentage on first variant
    for p in products:
        try:
            variant = p.productcolor_set.first().productvariant_set.first()
            if variant and variant.price_before_discount and variant.price_before_discount > variant.price:
                discount = variant.price_before_discount - variant.price
                discount_percent = (discount / variant.price_before_discount) * 100
                variant.discount_percent = round(discount_percent)
            else:
                variant.discount_percent = 0
        except Exception:
            pass

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'collection_page.html', {
        'products': page_obj,
        'collection_type': collection_type.title(),
        'page_obj': page_obj,
    })


def product_type_list(request, category_id, subcategory_id):
    try:
        # Get the subcategory object
        subcategory_obj = get_object_or_404(subcategory, id=subcategory_id, category_id=category_id)
        # Get product types related to that subcategory
        product_types = product_type.objects.filter(subcategory=subcategory_obj, category_id=category_id)
        # Render the response
        return render(request, 'subcategorypage.html', {
            'subcategory': subcategory_obj,
            'product_types': product_types,
            'category': subcategory_obj.category
        })
    except Exception as e:
        return HttpResponse(f"Error occurred: {e}")  
def product_list(request, category_id, subcategory_id, product_type_id):
    try:
        product_obj = get_object_or_404(
            product_type,
            id=product_type_id,
            subcategory_id=subcategory_id,
            category_id=category_id
        )
        
        # Filter variants
        variants = ProductVariant.objects.filter(
            color__product__category_id=category_id,
            color__product__subcategory_id=subcategory_id,
            color__product__product_type_id=product_type_id,
            color__product__is_available=True
        ).select_related('color', 'color__product')

        # 🔹 Add pagination
        paginator = Paginator(variants, 20)  # 12 variants per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'productlist.html', {
            'category': product_obj.category,
            'subcategory': product_obj.subcategory,
            'product_type': product_obj,
            'variants': page_obj,  # 🔸 Replace with paginated object
        })

    except Exception as e:
        return HttpResponse(f"Error occurred: {e}")
from django.core.paginator import Paginator

def product_detail(request, product_id):
    product_obj = get_object_or_404(
        Product.objects.select_related('category', 'subcategory', 'product_type')
                      .prefetch_related('colors__variants'),
        id=product_id
    )

    # Recently Viewed
    recently_viewed = request.session.get('recently_viewed', [])
    if product_obj.id in recently_viewed:
        recently_viewed.remove(product_obj.id)
    recently_viewed.insert(0, product_obj.id)
    recently_viewed = recently_viewed[:10]
    request.session['recently_viewed'] = recently_viewed

    recent_products = product.objects.filter(id__in=recently_viewed).exclude(id=product_obj.id)

    selected_color_id = request.GET.get('color')
    if selected_color_id:
        selected_color = get_object_or_404(product_obj.colors, id=selected_color_id)
    else:
        selected_color = product_obj.colors.first()

    color_images = []
    if selected_color:
        color_images = [
            img for img in [
                selected_color.image_main,
                selected_color.image1,
                selected_color.image2,
                selected_color.image3
            ] if img
        ]

    recommended_products = product.objects.filter(
        product_type=product_obj.product_type,
        subcategory=product_obj.subcategory
    ).exclude(id=product_obj.id)[:8]

    reviews = product_obj.reviews.all().order_by('-created_at')
    total_rating_stars = reviews.aggregate(Sum('rating'))['rating__sum'] or 0
    total_reviews = reviews.count()
    unique_reviewers = reviews.values('user').distinct().count()
    average_rating = round(total_rating_stars / total_reviews, 1) if total_reviews > 0 else 0

    review_paginator = Paginator(reviews, 3)
    review_page_number = request.GET.get('page')
    review_page_obj = review_paginator.get_page(review_page_number)

    # Paginate review images (9 per page)
    review_images_all = ReviewImage.objects.filter(review__product=product_obj)
    image_paginator = Paginator(review_images_all, 9)
    image_page_number = request.GET.get('image_page')
    image_page_obj = image_paginator.get_page(image_page_number)

    return render(request, 'productdetail.html', {
        'product': product_obj,
        'selected_color': selected_color,
        'color_images': color_images,
        'all_colors': product_obj.colors.all(),
        'variants': selected_color.variants.all() if selected_color else [],
        'recommended_products': recommended_products,
        'recent_products': recent_products,
        'page_obj': review_page_obj,
        'total_reviews': total_reviews,
        'unique_reviewers': unique_reviewers,
        'total_rating_stars': total_rating_stars,
        'average_rating': average_rating,
        'review_images': image_page_obj,  # ✅ paginated
        'review_images_has_next': image_page_obj.has_next(),  # for "view more" logic
        'user': request.user,
    })


def get_color_data(request, color_id):
    color = get_object_or_404(ProductColor, id=color_id)
    
    variants = []
    for variant in color.variants.all():
        variants.append({
            'id': variant.id,
            'size': variant.size,
            'price': str(variant.price_after_discount),
            'stock': variant.stock,
            'is_available': variant.stock > 0
        })
    
    images = []
    if color.image_main: images.append(color.image_main.url)
    if color.image1: images.append(color.image1.url)
    if color.image2: images.append(color.image2.url)
    if color.image3: images.append(color.image3.url)
    
    return JsonResponse({
        'images': images,
        'variants': variants,
        'color_name': color.color_name
    })

def ajax_search(request):
    query = request.GET.get('q', '')

    categories = category.objects.filter(name__icontains=query)[:5]
    subcategories = subcategory.objects.filter(name__icontains=query)[:5]
    product_types = product_type.objects.filter(name__icontains=query)[:5]
    products = product.objects.filter(name__icontains=query)[:5]

    # ✅ EVALUATE THE SUBQUERY INTO A LIST TO AVOID LIMIT-IN-SUBQUERY ERROR
    product_ids = list(products.values_list('id', flat=True))

    product_variants = ProductVariant.objects.select_related(
        'color', 'color__product', 'color__product__subcategory', 'color__product__category'
    ).filter(
        color__product__id__in=product_ids
    ).distinct()[:10]

    context = {
        'categories': categories,
        'subcategory2': subcategories,
        'product_type_search': product_types,
        'product_search': products,
        'product_variants': product_variants,
        'request': request,
    }

    html = render_to_string('partials/search_results.html', context)
    return HttpResponse(html)
import json

from django.core.paginator import Paginator
from django.db.models import Q

def stock_list(request):
    query = request.GET.get('q', '')
    filter_param = request.GET.get('filter', 'all')
    
    variants = ProductVariant.objects.select_related('color__product').all()
    
    if query:
        variants = variants.filter(
            Q(color__product__name__icontains=query) |
            Q(color__color_name__icontains=query) |
            Q(size__icontains=query)
        ).distinct()
    
    # Count all statuses
    all_count = variants.count()
    in_stock_count = variants.filter(stock__gte=15).count()
    low_stock_count = variants.filter(stock__lt=15, stock__gt=0).count()
    out_of_stock_count = variants.filter(stock=0).count()
    
    # Apply filter if specified
    if filter_param == 'in-stock':
        variants = variants.filter(stock__gte=15)
    elif filter_param == 'low-stock':
        variants = variants.filter(stock__lt=15, stock__gt=0)
    elif filter_param == 'out-of-stock':
        variants = variants.filter(stock=0)
    
    # Pagination
    paginator = Paginator(variants, 250)  # Show 20 variants per page
    page_number = request.GET.get('page')
    variants_page = paginator.get_page(page_number)
    
    return render(request, 'inventory_dashboard/stock_list.html', {
        'variants': variants_page,
        'all_count': all_count,
        'in_stock_count': in_stock_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count
    })
def search_stock(request):
    query = request.GET.get('q', '')
    
    if len(query) > 2:
        variants = ProductVariant.objects.select_related('color__product').filter(
            Q(color__product__name__icontains=query) |
            Q(color__color_name__icontains=query) |
            Q(size__icontains=query)
        ).distinct()
        
        results = []
        for variant in variants:
            results.append({
                'id': variant.id,
                'name': variant.color.product.name,
                'color': variant.color.color_name,
                'color_code': variant.color.hex_code,
                'size': variant.size,
                'stock': variant.stock
            })
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})

def stock_list_all(request):
    variants = ProductVariant.objects.select_related('color__product').all()
    data = [{
        'id': v.id,
        'name': v.color.product.name,
        'color': v.color.color_name,
        'color_code': v.color.hex_code,
        'size': v.size,
        'stock': v.stock
    } for v in variants]
    return JsonResponse(data, safe=False)


def update_stock(request, variant_id):
    if request.method == 'POST':
        try:
            variant = ProductVariant.objects.get(id=variant_id)
            new_stock = int(request.POST.get('stock', 0))
            variant.stock = new_stock
            variant.save()
            return HttpResponse(
                json.dumps({'success': True, 'new_stock': variant.stock}),
                content_type='application/json'
            )
        except Exception as e:
            return HttpResponse(
                json.dumps({'success': False, 'error': str(e)}),
                content_type='application/json',
                status=400
            )
    return HttpResponse(
        json.dumps({'success': False, 'error': 'Invalid request'}),
        status=405
    )


# ---------- Category ----------
class CategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return category.objects.none()
        qs = category.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs

# ---------- Subcategory (filtered by category) ----------
class SubcategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return subcategory.objects.none()
        qs = subcategory.objects.all()
        cat_id = self.forwarded.get('category')
        if cat_id:
            qs = qs.filter(category_id=cat_id)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs

# ---------- NEW: ProductType (filtered by category + subcategory) ----------
class ProductTypeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return product_type.objects.none()
        qs = product_type.objects.all()
        cat_id = self.forwarded.get('category')
        subcat_id = self.forwarded.get('subcategory')
        if cat_id:
            qs = qs.filter(category_id=cat_id)
        if subcat_id:
            qs = qs.filter(subcategory_id=subcat_id)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs
    
from decimal import Decimal
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from cart.cart import CartService   # apna cart service import kar


# product/views.py
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import product
from order.shiprocket import ShiprocketClient
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

@login_required
def check_pincode(request):
    product_id = request.GET.get("product_id")
    pincode = request.GET.get("pincode")

    if not pincode or not product_id:
        return JsonResponse({"available": False, "error": "Product or pincode missing"})

    # ✅ Save pincode in session
    request.session['pincode'] = pincode

    try:
        product_obj = product.objects.get(id=product_id)
    except product.DoesNotExist:
        return JsonResponse({"available": False, "error": "Product not found"})

    # ✅ COD true
    cod_flag = True

    # ✅ Calculate actual + volumetric weight
    actual_weight = (product_obj.weight_kg or Decimal("0.5"))
    length = product_obj.length_cm or Decimal("10.0")
    breadth = product_obj.width_cm or Decimal("10.0")
    height = product_obj.height_cm or Decimal("10.0")
    volumetric_weight = (length * breadth * height) / Decimal("5000")
    final_weight = max(actual_weight, volumetric_weight)

    # ✅ Shiprocket API call
    sr = ShiprocketClient()
    res = sr.calculate_shipping(pincode, final_weight)

    if res.get("success") and res.get("couriers"):
        best = min(res["couriers"], key=lambda x: x["rate"])
        result = {
            "product": product_obj.name,
            "eta": best.get("etd", "N/A"),
            "available": True,
            "cod": cod_flag
        }
    else:
        result = {
            "product": product_obj.name,
            "rate": "0",
            "eta": "N/A",
            "available": False,
            "cod": cod_flag,
            "error": res.get("error", "No courier available")
        }

    return JsonResponse(result)
from django.http import JsonResponse



@login_required
@require_POST
def update_shipping_by_pincode(request):
    """AJAX endpoint to update shipping cost dynamically based on pincode"""
    pincode = request.POST.get("pincode")
    if not pincode:
        return JsonResponse({"success": False, "error": "No pincode provided"}, status=400)

    # ✅ Session me save
    request.session["delivery_pincode"] = pincode
    request.session.modified = True

    # ✅ Recalculate using CartService (jo Shiprocket ko call karta hai)
    cart_service = CartService(request)
    summary = cart_service.get_summary()

    return JsonResponse({
        "success": True,
        "summary": {
            "subtotal": float(summary["subtotal"]),
            "shipping": float(summary["shipping"]),
            "discount": float(summary["discount"]),
            "tax": float(summary["tax"]),
            "total": float(summary["total"]),
        }
    })
