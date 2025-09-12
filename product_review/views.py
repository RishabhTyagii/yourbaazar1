from django.shortcuts import render, get_object_or_404, redirect



from .models import Review, ReviewImage
from .forms import ReviewForm
from product.models import product


def submit_review(request, product_id):
    if request.method == 'POST':
        product1 = get_object_or_404(product, id=product_id)
        form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.product = product1
            review.user = request.user
            review.save()

            for i, image_file in enumerate(request.FILES.getlist('images')):
                if i >= 4:
                    break
                ReviewImage.objects.create(review=review, image=image_file)

             # ✅ Redirect to product detail page after success
            return redirect('product:product_detail', product_id=product1.id)

        # Optional: handle invalid form
        return redirect('product:product_detail', product_id=product1.id)

    return redirect('product:product_detail', product_id=product_id)