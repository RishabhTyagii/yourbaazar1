from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from seller.models import Seller
from .models import SellerTestimonial
from .forms import SellerTestimonialForm

def _require_seller(request):
    sid = request.session.get("seller_id")
    if not sid:
        return None
    return Seller.objects.filter(id=sid).first()

def testimonial_list(request):
    q = request.GET.get("q", "").strip()
    page_size = int(request.GET.get("page_size", 12))
    qs = SellerTestimonial.objects.filter(is_approved=True).select_related("seller").order_by("-created_at")
    if q:
        qs = qs.filter(
            Q(display_name__icontains=q) |
            Q(business_name__icontains=q) |
            Q(experience__icontains=q) |
            Q(seller__username__icontains=q)
        )
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    return render(request, "seller_reviews/testimonial_list.html", {
        "page_obj": page_obj,
        "testimonials": page_obj.object_list,
        "q": q,
    })
def testimonial_create(request):
    seller = _require_seller(request)
    if not seller:
        messages.error(request, "Please log in as seller.")
        return redirect("seller:seller_login")

    instance = SellerTestimonial.objects.filter(seller=seller).first()

    if request.method == "POST":
        form = SellerTestimonialForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.seller = seller
            if not obj.display_name:
                obj.display_name = seller.owner_name or seller.username
            if not obj.business_name:
                obj.business_name = seller.business_name or ""
            obj.save()
            messages.success(request, "Thanks! Your review has been saved.")
            return redirect("seller:seller_landing")
        else:
            # DEBUG: remove after fix
            print("Form errors:", form.errors.as_json())
            messages.error(request, "Please fix the errors below.")
    else:
        initial = {
            "display_name": (instance.display_name if instance else (seller.owner_name or seller.username)),
            "business_name": (instance.business_name if instance else (seller.business_name or "")),
        }
        form = SellerTestimonialForm(instance=instance, initial=initial)

    return render(request, "seller_reviews/testimonial_create.html", {
        "form": form,
        "instance": instance,
        "seller": seller,
    })
