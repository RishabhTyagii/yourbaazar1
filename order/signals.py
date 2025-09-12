

from django.db.models.signals import post_save
from django.dispatch import receiver
from order.models import Order, OrderItem

@receiver(post_save, sender=Order)
def update_order_items_status_on_delivery(sender, instance, **kwargs):
    if instance.status.lower() == 'delivered':
        items = instance.items.exclude(item_status__iexact='delivered')
        for item in items:
            item.item_status = 'delivered'
            item.save()
