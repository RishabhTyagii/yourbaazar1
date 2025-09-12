from django.db.models.signals import post_save
from django.dispatch import receiver
from order.models import Order, OrderItem
from wallet.services import post_settlement_credit
from wallet.services import get_seller_for_product  # use service helper

@receiver(post_save, sender=Order)
def update_order_items_on_order_delivery(sender, instance, created, **kwargs):
    if not created and (instance.status or "").lower() == "delivered":
        # Mark undelivered items delivered (as before)
        for item in instance.items.exclude(item_status__iexact="delivered"):
            item.item_status = "delivered"
            item.save(update_fields=["item_status"])
        # Group items by seller and run one settlement per seller per order
        sellers = set()
        for oi in instance.items.all():
            s = get_seller_for_product(oi.product)
            if s:
                sellers.add(s)
        for s in sellers:
            try:
                post_settlement_credit(instance, s)  # new signature: (order, seller)
            except Exception as e:
                print(f"Settlement failed for order {instance.id} seller {getattr(s,'id',None)}: {e}")

@receiver(post_save, sender=OrderItem)
def orderitem_post_save_wallet_credit(sender, instance, created, **kwargs):
    if not created and (instance.item_status or "").lower() == "delivered":
        # Optional: skip here because Order post_save already handles per-seller settlement
        # But if needed, support partial deliveries:
        try:
            order = instance.order
            seller = get_seller_for_product(instance.product)
            if seller:
                post_settlement_credit(order, seller)
        except Exception as e:
            print(f"Settlement failed for OrderItem {instance.id}: {e}")


from django.db.models.signals import post_save
from django.dispatch import receiver
from order.models import Order, OrderItem
from wallet.services import post_settlement_reversal, get_seller_for_product

CANCELLED_STATES = {"cancelled", "returned", "refunded"}

@receiver(post_save, sender=Order)
def reverse_on_order_status(sender, instance, created, **kwargs):
    if created:
        return
    status = (instance.status or "").lower()
    if status in CANCELLED_STATES:
        # Reverse per seller against earlier settlements
        sellers = set()
        for oi in instance.items.all():
            s = get_seller_for_product(oi.product)
            if s:
                sellers.add(s)
        for s in sellers:
            try:
                post_settlement_reversal(instance, s, reason=status)
            except Exception as e:
                print(f"Reversal failed for order {instance.id} seller {getattr(s,'id',None)}: {e}")

@receiver(post_save, sender=OrderItem)
def reverse_on_item_status(sender, instance, created, **kwargs):
    if created:
        return
    istatus = (instance.item_status or "").lower()
    if istatus in CANCELLED_STATES:
        try:
            order = instance.order
            seller = get_seller_for_product(instance.product)
            if seller:
                # For partial returns/cancellations, reverse proportionally:
                # Option A: recompute amount for this item only and post a separate DEBIT with meta.item_id
                # Option B (simpler): if you always settle entire orders at once, skip item-level reversal to avoid double count.
                post_settlement_reversal(order, seller, reason=istatus)
        except Exception as e:
            print(f"Reversal failed for OrderItem {instance.id}: {e}")
