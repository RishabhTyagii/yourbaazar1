from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.admin.views.decorators import staff_member_required
from django.forms import  formset_factory
from seller.models import Seller
from product.models import category, subcategory, product_type, product, ProductColor, ProductVariant
from django.http import JsonResponse
from .models import SellerProductDraft, DraftColor, DraftVariant, SellerProductMeta
from .forms import SellerProductDraftForm, ColorFormSet, VariantFormSet,DraftVariantForm,ProductEditForm,ProductColorFormSet,ProductVariantSimpleFormSet, SellerProductMetaForm
from .utils import notify_admin_new_draft, notify_seller_approved, notify_seller_rejected
from django.db.models import Q,Sum, F, DecimalField, Value
from product_review.models import Review
from django.db.models import Avg
from django.db.models.functions import Coalesce
# 
from django.db.models import Prefetch
from decimal import Decimal
from product.models import product as Product, ProductColor, ProductVariant
from order.models import Order, OrderItem, ORDER_STATUS_CHOICES





def require_seller_login(view_func):
    def wrapper(request, *args, **kwargs):
        seller_id = request.session.get("seller_id")
        if not seller_id:
            messages.error(request, "Please log in as seller.")
            return redirect("seller:seller_login")
        request.seller = get_object_or_404(Seller, id=seller_id)
        return view_func(request, *args, **kwargs)
    return wrapper

from django.core.paginator import Paginator
from django.db.models import Q

@require_seller_login
def seller_draft_list(request):
    drafts = SellerProductDraft.objects.filter(seller=request.seller).order_by("-created_at")

    query = request.GET.get("q", "").strip()
    if query:
        drafts = drafts.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query)
        )
    
    status = request.GET.get("status", "").strip()
    if status:
        drafts = drafts.filter(status=status)

    # Pagination
    paginator = Paginator(drafts, 10)  # 10 drafts per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "seller_products/draft_list.html", {
        "page_obj": page_obj,
        "query": query,
        "selected_status": status,
        "is_paginated": page_obj.has_other_pages(),
    })


from django.db.models import Q
from django.core.paginator import Paginator





@require_seller_login
@transaction.atomic
def seller_draft_create(request):
    seller = request.seller
    if not seller.is_approved:
        messages.error(request, "Your seller account is not approved yet.")
        return redirect("seller:product_list")

    if request.method == "POST":
        draft_form = SellerProductDraftForm(request.POST, request.FILES)
        color_formset = ColorFormSet(request.POST, request.FILES, queryset=DraftColor.objects.none(), prefix="color")

        # Build per-color variant formsets with dynamic prefixes
        variant_formsets = []
        total_colors = int(request.POST.get("color-TOTAL_FORMS", 0))
        for i in range(total_colors):
            # अगर color delete हो रहा है, तो उसके variants ignore
            if request.POST.get(f"color-{i}-DELETE") == 'on':
                continue
            VariantFormSet = formset_factory(DraftVariantForm, extra=1, can_delete=True)
            vfs = VariantFormSet(request.POST, prefix=f"variant-{i}")
            variant_formsets.append((i, vfs))

        # Validate all
        all_valid = draft_form.is_valid() and color_formset.is_valid() and all(vfs.is_valid() for _, vfs in variant_formsets)

        if all_valid:
            # Save draft
            draft = draft_form.save(commit=False)
            draft.seller = seller
            draft.status = SellerProductDraft.Status.PENDING
            draft.save()

            # Save colors and map index -> saved color obj
            saved_colors_by_index = {}
            for idx, cform in enumerate(color_formset.forms):
                if cform.cleaned_data.get('DELETE'):
                    continue
                color_obj = cform.save(commit=False)
                color_obj.draft = draft
                color_obj.save()
                saved_colors_by_index[idx] = color_obj

            # Save variants for each color index
            for color_idx, vfs in variant_formsets:
                color_obj = saved_colors_by_index.get(color_idx)
                if not color_obj:
                    continue
                for vform in vfs.forms:
                    if vform.cleaned_data.get('DELETE'):
                        continue
                    if not vform.cleaned_data:
                        continue
                    var_obj = vform.save(commit=False)
                    # आवश्यक minimal validation: size हो
                    if not var_obj.size:
                        continue
                    var_obj.color = color_obj
                    var_obj.save()

            # Notify admin
            notify_admin_new_draft(seller.email, seller.username, draft.id, draft.name, draft.sku)
            messages.success(request, "Draft submitted with colors and variants. Admin will review it.")
            return redirect("seller_products:draft_detail", draft_id=draft.id)
        else:
            messages.error(request, "Please fix the errors below.")
            # fall-through to render with bound forms below
            # साथ में एक default variant formset row ensure करें ताकि खाली न लगे
            variant_formsets = ensure_at_least_one_variant_formset(request, total_colors)

    else:
        draft_form = SellerProductDraftForm()
        color_formset = ColorFormSet(queryset=DraftColor.objects.none(), prefix="color")

        # Initially one color row and its variants block
        VariantFormSet = formset_factory(DraftVariantForm, extra=1, can_delete=True)
        variant_formsets = [(0, VariantFormSet(prefix="variant-0"))]

    return render(request, "seller_products/draft_create.html", {
        "draft_form": draft_form,
        "color_formset": color_formset,
        "variant_formsets": variant_formsets,
    })

def ensure_at_least_one_variant_formset(request, total_colors):
    from django.forms import formset_factory
    VariantFormSet = formset_factory(DraftVariantForm, extra=1, can_delete=True)
    result = []
    if total_colors == 0:
        result.append((0, VariantFormSet(prefix="variant-0")))
    else:
        # हर रंग ब्लॉक के लिए एक-एक variant formset हो
        for i in range(total_colors):
            result.append((i, VariantFormSet(prefix=f"variant-{i}")))
    return result

def load_subcategories(request):
    category_id = request.GET.get("category_id")
    subcategories = subcategory.objects.filter(category_id=category_id).values("id", "name")
    return JsonResponse(list(subcategories), safe=False)

def load_product_types(request):
    subcategory_id = request.GET.get("subcategory_id")
    product_types = product_type.objects.filter(subcategory_id=subcategory_id).values("id", "name")
    return JsonResponse(list(product_types), safe=False)
@require_seller_login
def seller_draft_detail(request, draft_id):
    draft = get_object_or_404(SellerProductDraft, id=draft_id, seller=request.seller)
    colors = draft.colors.all().prefetch_related('variants')
    return render(request, "seller_products/draft_detail.html", {"draft": draft, "colors": colors})

@require_seller_login
def seller_draft_delete(request, draft_id):
    draft = get_object_or_404(SellerProductDraft, id=draft_id, seller=request.seller)
    if draft.status != SellerProductDraft.Status.PENDING:
        messages.error(request, "Only pending drafts can be deleted.")
        return redirect("seller_products:draft_detail", draft_id=draft.id)
    draft.delete()
    messages.success(request, "Draft deleted.")
    return redirect("seller_products:draft_list")


# ===============================================
def _seller_owns_product(seller, product_obj):
    """Check ownership via SellerProductMeta link created at approval time."""
    return SellerProductMeta.objects.filter(seller=seller, product=product_obj).exists()






from django.db.models import Sum, IntegerField, Value, Case, When, Q




LOW_STOCK_THRESHOLD = 5  # keep or adjust

@require_seller_login
def seller_product_list(request):
    # Variants that belong to products owned by this seller
    owned_product_ids = SellerProductMeta.objects.filter(
        seller=request.seller
    ).values_list("product_id", flat=True)

    variants = (
        ProductVariant.objects
        .filter(color__product_id__in=owned_product_ids)
        .select_related("color", "color__product")  # avoid N+1
    )

    # Search across product name, SKU, color_name, size
    q = request.GET.get("q", "").strip()
    if q:
        variants = variants.filter(
            Q(color__product__name__icontains=q) |
            Q(color__product__sku__icontains=q) |
            Q(color__color_name__icontains=q) |
            Q(size__icontains=q)
        )  # [1]

    # Annotations for safety (stock default) and unit price after discount if needed
    variants = variants.annotate(
        stock_s=Coalesce(F("stock"), Value(0), output_field=IntegerField())
    )  # [1]

    # Cards (computed per-variant)
    total_variants = variants.count()  # [1]
    in_stock_count = variants.filter(stock_s__gt=0).count()  # [1]
    low_stock_count = variants.filter(stock_s__gt=0, stock_s__lte=LOW_STOCK_THRESHOLD).count()  # [1]
    out_of_stock_count = variants.filter(stock_s=0).count()  # [1]

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(variants.order_by("-id"), 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)  # [1]

    context = {
        "variants": page_obj.object_list,
        "page_obj": page_obj,
        "query": q,
        "cards": {
            "total": total_variants,
            "in_stock": in_stock_count,
            "low_stock": low_stock_count,
            "out_of_stock": out_of_stock_count,
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
        },
    }  # [1]

    return render(request, "seller_products/product_list.html", context)  # [1]



@require_seller_login
def seller_product_detail(request, product_id):
    # SellerProductMeta
    meta = get_object_or_404(SellerProductMeta, product_id=product_id, seller=request.seller)
    product = meta.product

    # Get all colors
    colors = product.colors.all()

    # Prepare colors + images + variants
    colors_with_images = []
    for color in colors:
        images = [img for img in [color.image_main, color.image1, color.image2, color.image3] if img]
        variants = color.variants.all()  # ✅ attach variants here
        colors_with_images.append({
            "color": color,
            "images": images,
            "variants": variants,
        })

    context = {
        "product": product,
        "meta": meta,
        "colors_with_images": colors_with_images,
    }
    return render(request, "seller_products/product_detail.html", context)



@require_seller_login
@transaction.atomic
def seller_product_reviews(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews_qs = Review.objects.filter(product=product).order_by("-created_at")

    # Pagination setup
    paginator = Paginator(reviews_qs, 8)  # 8 reviews per page
    page_number = request.GET.get("page")
    reviews = paginator.get_page(page_number)

    # Calculate average rating
    avg_rating = reviews_qs.aggregate(avg=Avg("rating"))["avg"] or 0  

    context = {
        "product": product,
        "reviews": reviews,
        "avg_rating": avg_rating,
    }
    return render(request, "seller_products/product_reviews.html", context)


@require_seller_login
@transaction.atomic
def seller_product_edit(request, product_id):
    product_obj = get_object_or_404(Product, id=product_id)
    if not _seller_owns_product(request.seller, product_obj):
        messages.error(request, "You are not allowed to edit this product.")
        return redirect("seller_products:product_list")

    meta = get_object_or_404(SellerProductMeta, product=product_obj, seller=request.seller)

    if request.method == "POST":
        pform = ProductEditForm(request.POST, request.FILES, instance=product_obj)
        cformset = ProductColorFormSet(request.POST, request.FILES, instance=product_obj, prefix="pcolor")
        meta_form = SellerProductMetaForm(request.POST, instance=meta, prefix="meta")

        variant_formsets = []
        total_colors = int(request.POST.get("pcolor-TOTAL_FORMS", 0))
        for i in range(total_colors):
            vfs = ProductVariantSimpleFormSet(request.POST, prefix=f"pvariant-{i}")
            variant_formsets.append((i, vfs))

        all_valid = (
            pform.is_valid()
            and cformset.is_valid()
            and meta_form.is_valid()
            and all(vfs.is_valid() for _, vfs in variant_formsets)
        )

        if all_valid:
            # save live product + meta
            product_obj = pform.save()
            meta = meta_form.save()

            # sync shipping_charge (Product) with minimum_shipping (Meta)
            product_obj.shipping_charge = meta.minimum_shipping
            product_obj.save()

            # handle live product colors
            saved_colors_by_index = {}
            cformset.save(commit=False)

            for c_form in cformset.deleted_forms:
                if c_form.instance.pk:
                    c_form.instance.delete()

            for idx, c_form in enumerate(cformset.forms):
                if c_form in cformset.deleted_forms:
                    continue
                color_obj = c_form.save(commit=False)
                color_obj.product = product_obj
                color_obj.save()
                saved_colors_by_index[idx] = color_obj

            # handle variants
            for color_idx, vfs in variant_formsets:
                color_obj = saved_colors_by_index.get(color_idx)
                if not color_obj:
                    continue

                existing = {pv.pk: pv for pv in ProductVariant.objects.filter(color=color_obj)}
                seen_pks = set()
                for vform in vfs.forms:
                    if vform.cleaned_data.get("DELETE"):
                        continue
                    data = vform.cleaned_data
                    if not data:
                        continue

                    form_id = vform.data.get(vform.add_prefix("id"))
                    if form_id:
                        try:
                            pv = ProductVariant.objects.get(pk=form_id, color=color_obj)
                            pv.size = data.get("size")
                            pv.stock = data.get("stock")
                            pv.price_before_discount = data.get("price_before_discount")
                            pv.discount = data.get("discount")
                            pv.price_we_buy = data.get("price_we_buy")
                            pv.save()
                            seen_pks.add(pv.pk)
                            continue
                        except ProductVariant.DoesNotExist:
                            pass

                    pv = ProductVariant(
                        color=color_obj,
                        size=data.get("size"),
                        stock=data.get("stock"),
                        price_before_discount=data.get("price_before_discount"),
                        discount=data.get("discount"),
                        price_we_buy=data.get("price_we_buy"),
                    )
                    if pv.size:
                        pv.save()
                        seen_pks.add(pv.pk)

                for pk, obj in existing.items():
                    if pk not in seen_pks:
                        obj.delete()

            # -------------------------------
            # 🔑 SYNC DRAFT ALSO
            # -------------------------------
            draft, created = SellerProductDraft.objects.get_or_create(
                approved_product=product_obj,
                seller=request.seller,
                defaults={
                    "name": product_obj.name,
                    "sku": product_obj.sku,
                    "short_description": product_obj.short_description,
                    "description": product_obj.description,
                    "brand": product_obj.brand,
                    "base_price": product_obj.base_price,
                    "payment_mode": meta.payment_mode,
                    "shipping_by": meta.shipping_by,
                    "minimum_shipping": meta.minimum_shipping,
                    "length_cm": meta.length_cm,
                    "width_cm": meta.width_cm,
                    "height_cm": meta.height_cm,
                    "weight_kg": meta.weight_kg,
                    "status": SellerProductDraft.Status.PENDING,
                }
            )

            if not created:
                draft.name = product_obj.name
                draft.sku = product_obj.sku
                draft.short_description = product_obj.short_description
                draft.description = product_obj.description
                draft.brand = product_obj.brand
                draft.base_price = product_obj.base_price
                draft.payment_mode = meta.payment_mode
                draft.shipping_by = meta.shipping_by
                draft.minimum_shipping = meta.minimum_shipping
                draft.length_cm = meta.length_cm
                draft.width_cm = meta.width_cm
                draft.height_cm = meta.height_cm
                draft.weight_kg = meta.weight_kg
                
                draft.save()

            # clear old draft colors + variants, rebuild
            draft.colors.all().delete()
            for color in ProductColor.objects.filter(product=product_obj):
                dcolor = DraftColor.objects.create(
                    draft=draft,
                    color_name=color.color_name,
                    color_code=color.color_code,
                    image_main=color.image_main,
                    image1=color.image1,
                    image2=color.image2,
                    image3=color.image3,
                )
                for pv in ProductVariant.objects.filter(color=color):
                    DraftVariant.objects.create(
                        color=dcolor,
                        size=pv.size,
                        stock=pv.stock,
                        price_before_discount=pv.price_before_discount,
                        discount=pv.discount,
                        price_we_buy=pv.price_we_buy,
                    )

            # -------------------------------

            messages.success(request, "Product updated successfully (draft updated for admin review).")
            return redirect("seller_products:product_list")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        pform = ProductEditForm(instance=product_obj)
        cformset = ProductColorFormSet(instance=product_obj, prefix="pcolor")
        meta_form = SellerProductMetaForm(instance=meta, prefix="meta")

        variant_formsets = []
        for idx, c_form in enumerate(cformset.forms):
            color_instance = c_form.instance
            initial = []
            for pv in ProductVariant.objects.filter(color=color_instance):
                initial.append(
                    {
                        "size": pv.size,
                        "stock": pv.stock,
                        "price_before_discount": pv.price_before_discount,
                        "discount": pv.discount,
                        "price_we_buy": pv.price_we_buy,
                        "id": pv.id,
                    }
                )
            vfs = ProductVariantSimpleFormSet(prefix=f"pvariant-{idx}", initial=initial)
            variant_formsets.append((idx, vfs))

    return render(
        request,
        "seller_products/product_edit.html",
        {
            "product": product_obj,
            "pform": pform,
            "cformset": cformset,
            "meta_form": meta_form,
            "variant_formsets": variant_formsets,
        },
    )






# admin start hai yha se 


@staff_member_required
def admin_draft_list(request):
    status = request.GET.get("status")
    qs = SellerProductDraft.objects.all().order_by("-created_at")
    if status:
        qs = qs.filter(status=status)
    return render(request, "seller_products/admin/draft_list.html", {"drafts": qs, "status": status})

@staff_member_required
def admin_draft_detail(request, draft_id):
    draft = get_object_or_404(SellerProductDraft, id=draft_id)
    colors = draft.colors.all().prefetch_related('variants')
    return render(request, "seller_products/admin/draft_detail.html", {"draft": draft, "colors": colors})

@staff_member_required
@transaction.atomic
def admin_draft_approve(request, draft_id):
    draft = get_object_or_404(SellerProductDraft, id=draft_id)
    if draft.status != SellerProductDraft.Status.PENDING:
        messages.error(request, "Only pending drafts can be approved.")
        return redirect("seller_products:admin_draft_detail", draft_id=draft.id)

    # Resolve category/subcategory/product_type (prefer actual FK, else ensure created already by admin)
    cat = draft.category
    sub = draft.subcategory
    ptype = draft.product_type

    if not cat and draft.category_other:
        messages.error(request, "Assign a real category before approval (currently 'Other').")
        return redirect("seller_products:admin_draft_detail", draft_id=draft.id)
    if not sub and draft.subcategory_other:
        messages.error(request, "Assign a real subcategory before approval (currently 'Other').")
        return redirect("seller_products:admin_draft_detail", draft_id=draft.id)
    if not ptype and draft.product_type_other:
        messages.error(request, "Assign a real product type before approval (currently 'Other').")
        return redirect("seller_products:admin_draft_detail", draft_id=draft.id)
    if not draft.colors.exists():
        messages.error(request, "At least one color is required before approval.")
        return redirect("seller_products:admin_draft_detail", draft_id=draft.id)

    from .models import DraftVariant
    if not DraftVariant.objects.filter(color__draft=draft).exists():
        messages.error(request, "At least one variant is required before approval.")
        return redirect("seller_products:admin_draft_detail", draft_id=draft.id)

    from product.models import product as ProductModel
    if ProductModel.objects.filter(sku=draft.sku).exists():
        messages.error(request, f"SKU '{draft.sku}' already exists. Please update the draft SKU.")
        return redirect("seller_products:admin_draft_detail", draft_id=draft.id)
    # Create product
    try:
        new_product = product.objects.create(
            sku=draft.sku,
            category=cat,
            subcategory=sub,
            product_type=ptype,
            name=draft.name,
            thumbnail=draft.thumbnail,
            description=draft.description or "",
            brand=draft.brand or "",
            is_available=True,
            slug=f"{draft.sku}-{draft.id}",  # Adjust your slug policy
            image=draft.thumbnail,  # optional
            base_price=draft.base_price,
            cod_available=True if draft.payment_mode in ['cod', 'both'] else False,
            shipping_charge=Decimal(str(draft.minimum_shipping or 0)),
            short_description=draft.short_description or "",
            length_cm=draft.length_cm,
            width_cm=draft.width_cm,
            height_cm=draft.height_cm,
            weight_kg=draft.weight_kg,
        )
        print("✅ Product saved:", new_product.shipping_charge)
        print("✅ Product saved:", new_product.id)
    except Exception as e:
        print("❌ Error while saving product:", e)  

    # Colors and variants
    for dcolor in draft.colors.all():
        pcolor = ProductColor.objects.create(
            product=new_product,
            color_name=dcolor.color_name,
            color_code=dcolor.color_code,
            image_main=dcolor.image_main,
            image1=dcolor.image1,
            image2=dcolor.image2,
            image3=dcolor.image3,
        )
        for dvar in dcolor.variants.all():
            ProductVariant.objects.create(
                color=pcolor,
                size=dvar.size,
                stock=dvar.stock,
                price_before_discount=dvar.price_before_discount,
                discount=dvar.discount,
                price_we_buy=dvar.price_we_buy,
            )

    # Meta
    SellerProductMeta.objects.create(
        seller=draft.seller,
        product=new_product,
        payment_mode=draft.payment_mode,
        shipping_by=draft.shipping_by,
        minimum_shipping=draft.minimum_shipping,
        length_cm=draft.length_cm,
        width_cm=draft.width_cm,
        height_cm=draft.height_cm,
        weight_kg=draft.weight_kg,
        brand=draft.brand,
        size_price_explanation=draft.size_price_explanation,
    
    )

    # Update draft
    draft.status = SellerProductDraft.Status.APPROVED
    draft.approved_product = new_product
    draft.rejection_reason = ""
    draft.save()

    # Notify seller
    notify_seller_approved(draft.seller.email, draft.name, new_product.id)
    messages.success(request, f"Approved draft {draft.id} and created product {new_product.id}.")
    return redirect("seller_products:admin_draft_detail", draft_id=draft.id)

@staff_member_required
def admin_draft_reject(request, draft_id):
    draft = get_object_or_404(SellerProductDraft, id=draft_id)
    if draft.status != SellerProductDraft.Status.PENDING:
        messages.error(request, "Only pending drafts can be rejected.")
        return redirect("seller_products:admin_draft_detail", draft_id=draft.id)

    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()
        if not reason:
            messages.error(request, "Please provide a valid reason.")
            return redirect("seller_products:admin_draft_reject", draft_id=draft.id)
        draft.status = SellerProductDraft.Status.REJECTED
        draft.rejection_reason = reason
        draft.save()
        notify_seller_rejected(draft.seller.email, draft.name, draft.id, reason)
        messages.success(request, "Draft rejected and seller notified.")
        return redirect("seller_products:admin_draft_detail", draft_id=draft.id)

    return render(request, "seller_products/admin/draft_reject.html", {"draft": draft})

# seller_products/views.py



# Helper: किसी seller के product_ids
# 
# from product.models import product as Product  # only if you want Product.shipping_charge option

def _seller_product_ids(seller):
    return list(
        SellerProductMeta.objects.filter(seller=seller).values_list("product_id", flat=True)
    )

def _seller_order_metrics(seller, start=None, end=None, q=None):
    # Your existing metrics helper (unchanged) or keep as earlier
    product_ids = _seller_product_ids(seller)
    if not product_ids:
        return {
            "total_orders": 0,
            "cod_sales": Decimal("0.00"),
            "online_sales": Decimal("0.00"),
        }

    items_qs = OrderItem.objects.filter(product_id__in=product_ids).select_related("order")

    if q:
        items_qs = items_qs.filter(
            Q(order__order_number__icontains=q) |
            Q(order__customer_name__icontains=q) |
            Q(order__shipping_city__icontains=q)
        )

    if start and end:
        items_qs = items_qs.filter(order__created_at__date__range=(start, end))

    total_orders = items_qs.values_list("order_id", flat=True).distinct().count()

    price = F("price")
    disc = Coalesce(F("discount_price"), Value(0))
    qty = F("quantity")
    unit = Coalesce(price - disc, Value(0), output_field=DecimalField(max_digits=12, decimal_places=2))
    line_total = unit * qty

    exclude_statuses = ["Cancelled", "Returned", "Refunded"]

    cod_sales = items_qs.filter(
        order__payment_method__iexact="cod"
    ).exclude(order__status__in=exclude_statuses).aggregate(
        s=Coalesce(Sum(line_total, output_field=DecimalField(max_digits=12, decimal_places=2)),
                   Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)))
    )["s"]

    online_sales = items_qs.exclude(order__payment_method__iexact="cod").filter(
        order__payment_status__in=["completed", "pending", "failed", "refunded"]  # adjust as per policy
    ).exclude(order__status__in=exclude_statuses).aggregate(
        s=Coalesce(Sum(line_total, output_field=DecimalField(max_digits=12, decimal_places=2)),
                   Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)))
    )["s"]

    return {
        "total_orders": total_orders or 0,
        "cod_sales": cod_sales or Decimal("0.00"),
        "online_sales": online_sales or Decimal("0.00"),
    }

@staff_member_required
def admin_seller_orders(request):
    # Filters
    seller_id = request.GET.get("seller_id", "").strip()
    q = request.GET.get("q", "").strip()
    start = request.GET.get("start", "").strip()
    end = request.GET.get("end", "").strip()
    status = request.GET.get("status", "").strip()
    payment_method = request.GET.get("payment_method", "").strip()

    sellers = Seller.objects.order_by("username")

    selected_seller = None
    orders = Order.objects.none()
    page_obj = None
    metrics = {"total_orders": 0, "cod_sales": Decimal("0.00"), "online_sales": Decimal("0.00")}

    # Seller-shared maps for the table
    seller_subtotals = {}
    seller_shipping_map = {}
    seller_totals = {}

    if seller_id:
        selected_seller = get_object_or_404(Seller, id=seller_id)

        # सभी orders जिनमें seller के products हैं
        product_ids = _seller_product_ids(selected_seller)
        if product_ids:
            # पहले relevant order_ids निकालें
            seller_order_ids_qs = OrderItem.objects.filter(product_id__in=product_ids)

            if q:
                seller_order_ids_qs = seller_order_ids_qs.filter(
                    Q(order__order_number__icontains=q) |
                    Q(order__customer_name__icontains=q) |
                    Q(order__shipping_city__icontains=q)
                )
            if start and end:
                seller_order_ids_qs = seller_order_ids_qs.filter(order__created_at__date__range=(start, end))
            if status:
                seller_order_ids_qs = seller_order_ids_qs.filter(order__status__iexact=status)
            if payment_method:
                seller_order_ids_qs = seller_order_ids_qs.filter(order__payment_method__iexact=payment_method)

            order_ids = list(seller_order_ids_qs.values_list("order_id", flat=True).distinct())
            orders = (
                Order.objects.filter(id__in=order_ids)
                .order_by("-created_at")
            )

            # Pagination
            paginator = Paginator(orders, 20)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)

            # Metrics (cards)
            metrics = _seller_order_metrics(selected_seller, start or None, end or None, q or None)

            # --------- Seller subtotal per order (items total after discount) ----------
            price = F("price")
            disc = Coalesce(F("discount_price"), Value(0))
            qty = F("quantity")
            unit = Coalesce(price - disc, Value(0), output_field=DecimalField(max_digits=12, decimal_places=2))
            line_total = unit * qty

            seller_subtotals_qs = (
                OrderItem.objects
                .filter(order_id__in=order_ids, product_id__in=product_ids)
                .values("order_id")
                .annotate(total=Coalesce(
                    Sum(line_total, output_field=DecimalField(max_digits=12, decimal_places=2)),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                ))
            )
            seller_subtotals = {row["order_id"]: row["total"] for row in seller_subtotals_qs}

            # --------- Seller shipping per order (per DISTINCT product, not per quantity) ----------
            # Option A (recommended): SellerProductMeta.minimum_shipping
            min_ship_by_product = {
                row["product_id"]: row["minimum_shipping"]
                for row in SellerProductMeta.objects
                    .filter(seller=selected_seller, product_id__in=product_ids)
                    .values("product_id", "minimum_shipping")
            }

            distinct_rows = (
                OrderItem.objects
                .filter(order_id__in=order_ids, product_id__in=product_ids)
                .values("order_id", "product_id")
                .distinct()
            )

            seller_shipping_map = {oid: Decimal("0") for oid in order_ids}
            for row in distinct_rows:
                pid = row["product_id"]
                seller_shipping_map[row["order_id"]] += Decimal(str(min_ship_by_product.get(pid, 0)))

            # Option B (alternative): Product.shipping_charge per distinct product
            # ship_by_product = {
            #     p.id: (p.shipping_charge or 0)
            #     for p in Product.objects.filter(id__in=product_ids).only("id", "shipping_charge")
            # }
            # seller_shipping_map = {oid: Decimal("0") for oid in order_ids}
            # for row in distinct_rows:
            #     pid = row["product_id"]
            #     seller_shipping_map[row["order_id"]] += Decimal(str(ship_by_product.get(pid, 0)))

            # --------- Total per order (seller) ----------
            for oid in order_ids:
                st = seller_subtotals.get(oid, Decimal("0"))
                sh = seller_shipping_map.get(oid, Decimal("0"))
                seller_totals[oid] = st + sh

    context = {
        "sellers": sellers,
        "selected_seller": selected_seller,
        "page_obj": page_obj,
        "orders": page_obj.object_list if page_obj else [],
        "q": q,
        "start": start,
        "end": end,
        "status": status,
        "payment_method": payment_method,
        "metrics": metrics,
        "ORDER_STATUS_CHOICES": ORDER_STATUS_CHOICES,

        # new maps for template
        "seller_subtotals": seller_subtotals,
        "seller_shipping_map": seller_shipping_map,
        "seller_totals": seller_totals,
    }
    return render(request, "seller_products/admin/seller_orders.html", context)

@staff_member_required
def admin_order_status_update(request):
    # AJAX POST: order_id, new_status
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Invalid request"}, status=400)

    from django.http import JsonResponse
    order_id = request.POST.get("order_id")
    new_status = request.POST.get("status")
    if not order_id or not new_status:
        return JsonResponse({"ok": False, "error": "Missing parameters"}, status=400)

    order = get_object_or_404(Order, id=order_id)

    # Validate status
    valid_statuses = [s[0] for s in ORDER_STATUS_CHOICES]
    if new_status not in valid_statuses:
        return JsonResponse({"ok": False, "error": "Invalid status"}, status=400)

    order.status = new_status
    order.save(update_fields=["status", "updated_at"])
    return JsonResponse({"ok": True, "status": new_status})




@staff_member_required
def admin_seller_order_detail(request, order_id, seller_id):
    order = get_object_or_404(Order, id=order_id)
    seller = get_object_or_404(Seller, id=seller_id)

    product_ids = _seller_product_ids(seller)
    if not product_ids:
        messages.error(request, "This seller has no linked products.")
        return redirect("seller_products:admin_seller_orders")

    # Ensure this order actually contains items for this seller
    has_items = OrderItem.objects.filter(order_id=order.id, product_id__in=product_ids).exists()
    if not has_items:
        messages.error(request, "This order has no items for the selected seller.")
        return redirect("seller_products:admin_seller_orders")

    # Fetch only the seller's items for this order
    items = (
        OrderItem.objects
        .filter(order=order, product_id__in=product_ids)
        .select_related("product", "variant", "variant__color")
        .order_by("id")
    )

    # Helper: unit price after discount (respect is_free)
    def unit_price(it):
        if getattr(it, "is_free", False):
            return Decimal("0")
        price = it.price or Decimal("0")
        disc = it.discount_price or Decimal("0")
        unit = price - disc
        return unit if unit > 0 else Decimal("0")

    # Build prepared rows to avoid math in templates
    rows = []
    for it in items:
        u = unit_price(it)
        rows.append({
            "product": it.product,
            "variant": it.variant,
            "quantity": it.quantity,
            "unit": u,                         # Decimal
            "line_total": u * it.quantity,     # Decimal
            "is_free": getattr(it, "is_free", False),
        })

    # Subtotal = sum of seller rows line_total
    seller_subtotal = sum((r["line_total"] for r in rows), Decimal("0"))

    # Shipping per DISTINCT product (once per product), using SellerProductMeta.minimum_shipping (seller-specific)
    min_ship_by_product = {
        row["product_id"]: row["minimum_shipping"]
        for row in SellerProductMeta.objects
            .filter(seller=seller, product_id__in=product_ids)
            .values("product_id", "minimum_shipping")
    }

    distinct_pids = (
        OrderItem.objects
        .filter(order=order, product_id__in=product_ids)
        .values_list("product_id", flat=True)
        .distinct()
    )

    seller_shipping = Decimal("0")
    for pid in distinct_pids:
        seller_shipping += Decimal(str(min_ship_by_product.get(pid, 0)))

    seller_total = seller_subtotal + seller_shipping

    context = {
        "order": order,
        "seller": seller,
        "rows": rows,  # use rows in template instead of items to show unit/line totals safely
        "seller_subtotal": seller_subtotal,
        "seller_shipping": seller_shipping,
        "seller_total": seller_total,
    }
    return render(request, "seller_products/admin/seller_order_detail.html", context)

