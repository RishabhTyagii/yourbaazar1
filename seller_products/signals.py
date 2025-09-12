from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SellerProductDraft, SellerProductMeta

@receiver(post_save, sender=SellerProductDraft)
def create_or_update_seller_meta(sender, instance, **kwargs):
    """
    जब draft approve होकर product बनता है, तब SellerProductMeta हमेशा
    update_or_create से handle होगा — duplicate कभी नहीं बनेगा।
    """
    if instance.status == SellerProductDraft.Status.APPROVED and instance.approved_product:
        SellerProductMeta.objects.update_or_create(
            product=instance.approved_product,
            seller=instance.seller,
            defaults={
                "payment_mode": instance.payment_mode,
                "shipping_by": instance.shipping_by,
                "minimum_shipping": instance.minimum_shipping,
                "length_cm": instance.length_cm,
                "width_cm": instance.width_cm,
                "height_cm": instance.height_cm,
                "weight_kg": instance.weight_kg,
                "brand": instance.brand,
                "size_price_explanation": instance.size_price_explanation,
                "is_extended_color_of_existing": instance.is_extended_color_of_existing,
                "existing_product": instance.existing_product,
            }
        )
