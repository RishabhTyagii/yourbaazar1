
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.apps import apps
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone
from .models import SellerWallet, WalletTransaction, WithdrawalRequest, CommissionRule
from seller.models import Seller

def get_or_create_wallet(seller):
    wallet, _ = SellerWallet.objects.get_or_create(seller=seller)
    return wallet

def get_seller_for_product(product):
    SellerProductMeta = apps.get_model("seller_products", "SellerProductMeta")
    meta = SellerProductMeta.objects.filter(product=product).select_related("seller").first()
    return meta.seller if meta else None

def minimum_shipping_for_product(product):
    SellerProductMeta = apps.get_model("seller_products", "SellerProductMeta")
    meta = SellerProductMeta.objects.filter(product=product).first()
    val = getattr(meta, "minimum_shipping", None) if meta else None
    try:
        return Decimal(str(val)).quantize(Decimal("0.01")) if val is not None else Decimal("0.00")
    except Exception:
        return Decimal("0.00")

def compute_fees(gross_amount, payment_method: str):
    payment_method = (payment_method or "").lower()
    if payment_method == "cod":
        return Decimal("0.00")
    # Approx Razorpay/PG fee: 2% of gross (ignore flat for simplicity)
    pg_fee = (gross_amount * Decimal("0.02")).quantize(Decimal("0.01"))
    return pg_fee

def resolve_commission_for_product(product, as_of=None):
    as_of = as_of or timezone.now()
    q = CommissionRule.objects.filter(active=True).order_by("-scope")

    SellerProductMeta = apps.get_model("seller_products", "SellerProductMeta")
    spm = SellerProductMeta.objects.filter(product=product).first()
    if spm:
        rule = q.filter(product=spm).first()
        if rule and rule.is_active(as_of):
            return rule

    global_rule = q.filter(scope=CommissionRule.Scope.GLOBAL).first()
    if global_rule and global_rule.is_active(as_of):
        return global_rule

    # Fallback: 10% global (not saved instance)
    return CommissionRule(scope=CommissionRule.Scope.GLOBAL, commission_type="percent", rate_percent=Decimal("10.00"))











@transaction.atomic
def post_settlement_credit(order, seller, as_of=None):
    as_of = as_of or timezone.now()
    wallet = get_or_create_wallet(seller)

    # Prevent duplicate settlement
    if WalletTransaction.objects.filter(
        wallet=wallet,
        source=WalletTransaction.Source.ORDER_SETTLEMENT,
        reference_id=str(order.id),
        txn_type=WalletTransaction.Type.CREDIT,
    ).exists():
        print("Duplicate settlement detected, exiting.")
        return Decimal("0.00")

    # Seller-specific order items
    order_items = [oi for oi in order.items.all() if get_seller_for_product(oi.product) == seller]
    if not order_items:
        print("No seller items, exiting.")
        return Decimal("0.00")

    gross_total = Decimal("0.00")
    commission_total = Decimal("0.00")
    items_meta = []

    def commission_per_unit_from_rule(rule, unit_price):
        if not rule:
            return Decimal("0.00")
        ctype = getattr(rule, "commission_type", "")
        if ctype == "percent" and getattr(rule, "rate_percent", None) is not None:
            return (unit_price * Decimal(str(rule.rate_percent)) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if ctype == "flat" and getattr(rule, "flat_amount", None) is not None:
            return Decimal(str(rule.flat_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return Decimal("0.00")

    for oi in order_items:
        qty = Decimal(oi.quantity or 1)
        unit_price = Decimal(oi.price or 0) - Decimal(oi.discount_price or 0)
        unit_price = max(unit_price, Decimal("0.00"))

        item_gross = (unit_price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gross_total += item_gross

        # Commission calculation
        effective_rule = resolve_commission_for_product(oi.product, as_of=as_of)
        per_unit_comm = commission_per_unit_from_rule(effective_rule, unit_price)
        item_commission_total = (per_unit_comm * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        commission_total += item_commission_total

        items_meta.append({
            "order_item_id": oi.id,
            "product_id": oi.product.id,
            "qty": int(qty),
            "unit_price": str(unit_price),
            "gross": str(item_gross),
            "commission_per_unit": str(per_unit_comm),
            "commission_total": str(item_commission_total),
        })

        print(f"Item ID: {oi.product.id}, Unit: {unit_price}, Qty: {qty}, Gross: {item_gross}, Commission/unit: {per_unit_comm}, Item Commission: {item_commission_total}, Shipping: {oi.shipping_cost}")

    # Shipping total
    shipping_total = sum(Decimal(oi.shipping_cost or 0) for oi in order_items)
    shipping_total = shipping_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # PG Fee
    payment_method = (getattr(order, "payment_method", "") or "").strip().lower()
    pg_fee = Decimal("0.00")
    if payment_method not in ["cod", "cash on delivery"]:
        pg_fee = compute_fees(gross_total, payment_method).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Net payout: gross + shipping - commission - PG fee
    net = (gross_total-shipping_total-commission_total - pg_fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    print(f"DEBUG => gross: {gross_total}, shipping: {shipping_total}, commission: {commission_total}, pg_fee: {pg_fee}, net: {net}")

    new_balance = (wallet.available_balance + net).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    WalletTransaction.objects.create(
        wallet=wallet,
       
        txn_type=WalletTransaction.Type.CREDIT,
        source=WalletTransaction.Source.ORDER_SETTLEMENT,
        amount=net,
        balance_after=new_balance,
        status=WalletTransaction.Status.SUCCESS,
        reference_id=str(order.id),
      
        meta={
            "order_id": order.id,
            
            "payment_method": payment_method,
            "gross_total": str(gross_total),
            "commission_total": str(commission_total),
            "shipping_applied": str(shipping_total),
            "pg_fee": str(pg_fee),
            "items": items_meta,
        },
    )

    wallet.available_balance = new_balance
    wallet.save(update_fields=["available_balance", "updated_at"])

    # Email notification
    if seller.email:
        subject = f"Wallet Credited: ₹{net}"
        message = f"""
Hello {seller.username},

Your wallet has been credited with ₹{net} for Order #{order.id}.

Gross Amount: ₹{gross_total}
Commission Deducted: ₹{commission_total}
Shipping Applied: ₹{shipping_total}
Payment Gateway Fee: ₹{pg_fee}

New Wallet Balance: ₹{new_balance}

Thank you,
Your Marketplace Team
"""
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [seller.email], fail_silently=True)

    print(f"Net Payout Credited: {net}, New Wallet Balance: {new_balance}")

    return net




@transaction.atomic
def post_settlement_reversal(order, seller, reason: str = "cancelled"):
    wallet, _ = SellerWallet.objects.get_or_create(seller=seller)

    # Find original credit for this order+seller
    orig = WalletTransaction.objects.filter(
        wallet=wallet,
        source=WalletTransaction.Source.ORDER_SETTLEMENT,
        reference_id=str(order.id),
        txn_type=WalletTransaction.Type.CREDIT,
        status=WalletTransaction.Status.SUCCESS,
    ).order_by("-id").first()
    if not orig or orig.amount <= 0:
        return Decimal("0.00")

    # Idempotency: has a matching reversal been posted?
    already = WalletTransaction.objects.filter(
        wallet=wallet,
        source=WalletTransaction.Source.ORDER_SETTLEMENT,
        reference_id=str(order.id),
        txn_type=WalletTransaction.Type.DEBIT,
        status=WalletTransaction.Status.SUCCESS,
        meta__reversal_for_txn=orig.id,
    ).exists()
    if already:
        return Decimal("0.00")

    amt = Decimal(orig.amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    new_balance = (wallet.available_balance - amt).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    WalletTransaction.objects.create(
        wallet=wallet,
        txn_type=WalletTransaction.Type.DEBIT,
        source=WalletTransaction.Source.ORDER_SETTLEMENT,
        amount=amt,
        balance_after=new_balance,
        status=WalletTransaction.Status.SUCCESS,
        reference_id=str(order.id),
        meta={
            **(orig.meta or {}),
            "reversal_for_txn": orig.id,
            "reason": reason,
        },
        order=getattr(orig, "order", None),  # optional
    )

    wallet.available_balance = new_balance
    wallet.save(update_fields=["available_balance", "updated_at"])

    # Optional: email notify seller
    # ...
     # Email notification
    if getattr(seller, "email", None):
        subject = f"Wallet Debited: ₹{amt}"
        message = f"""
Hello {getattr(seller, "username", "Seller")},

Your wallet has been debited with ₹{amt} due to Order #{order.id} being {reason.upper()}.

Debited Amount: ₹{amt}
Reason: {reason.capitalize()}
New Wallet Balance: ₹{new_balance}

Thank you,
Your Marketplace Team
"""
        try:
            send_mail(
                subject,
                message,
                getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@yourbaazarseller.com"),
                [seller.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send reversal email: {e}")

    print(f"Wallet debited {amt} for Order {order.id}, Seller {seller.id}, New Balance {new_balance}")

    return amt






@transaction.atomic
def request_withdrawal(seller, amount: Decimal, admin_note: str = None):
    amount = Decimal(amount).quantize(Decimal("0.01"))
    wallet = get_or_create_wallet(seller)

    if amount < 500:
        raise ValueError("Minimum withdrawal amount is ₹500.")

    if amount <= 0:
        raise ValueError("Amount must be > 0")

    # ✅ Seller ke wallet me at least 50 rs rehna chahiye
    if wallet.available_balance - amount < Decimal("500.00"):
        raise ValueError("You must leave a minimum balance of ₹500 in your wallet.")

    if wallet.available_balance < amount:
        raise ValueError("Insufficient balance")

    wallet.available_balance -= amount
    wallet.pending_payout += amount
    wallet.save(update_fields=["available_balance", "pending_payout", "updated_at"])
     # Deduct amount
    WalletTransaction.objects.create(
        wallet=wallet,
        txn_type=WalletTransaction.Type.HOLD,
        source=WalletTransaction.Source.WITHDRAWAL,
        amount=amount,
        balance_after=wallet.available_balance,
        status=WalletTransaction.Status.PENDING,
        meta={"note": admin_note or ""},
    )

    wr = WithdrawalRequest.objects.create(
        seller=seller,
        amount=amount,
        account_holder_name=seller.bank_account_name,
        bank_account_no=seller.bank_account_no,
        upi_id=seller.upi_id,
        status=WithdrawalRequest.Status.REQUESTED,
        admin_note=admin_note or "",
    )

    seller_email = getattr(seller, "email", None)
    if seller_email:
        try:
            send_mail(
                subject="Withdrawal Requested",
                message=f"Your withdrawal request of ₹{amount} has been submitted.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[seller_email],
                fail_silently=True,
            )
        except Exception:
            pass
    

    return wr

@transaction.atomic
def approve_withdrawal(wr: WithdrawalRequest, note: str = None):
    """
    Approve a seller withdrawal request
    """
    if wr.status != WithdrawalRequest.Status.REQUESTED:
        return wr  # Only requested withdrawal can be approved

    wallet = get_or_create_wallet(wr.seller)

    if wallet.available_balance + wallet.pending_payout < wr.amount:
        raise ValueError("Insufficient wallet balance to approve this withdrawal")

    # Deduct from pending payout
    wallet.pending_payout -= wr.amount
    wallet.save(update_fields=["pending_payout", "updated_at"])

    # Record wallet transaction
    WalletTransaction.objects.create(
        wallet=wallet,
        txn_type=WalletTransaction.Type.DEBIT,
        source=WalletTransaction.Source.WITHDRAWAL,
        amount=wr.amount,
        balance_after=wallet.available_balance,
        status=WalletTransaction.Status.SUCCESS,
        meta={"admin_note": note or ""},
    )

    # Update withdrawal request
    wr.status = WithdrawalRequest.Status.COMPLETED
    wr.admin_note = note or wr.admin_note
    wr.processed_at = timezone.now()
    wr.save(update_fields=["status", "admin_note", "processed_at"])

    # Send email
    seller_email = getattr(wr.seller, "email", None)
    if seller_email:
        try:
            send_mail(
                subject="Withdrawal Approved",
                message=f"Your withdrawal request of ₹{wr.amount} has been approved and processed.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[seller_email],
                fail_silently=True,
            )
        except Exception:
            pass

    return wr


@transaction.atomic
def reject_withdrawal(wr: WithdrawalRequest, note: str = None):
    if wr.status not in [
        WithdrawalRequest.Status.REQUESTED,
        WithdrawalRequest.Status.PROCESSING,
        WithdrawalRequest.Status.FAILED,
    ]:
        return wr

    wallet = get_or_create_wallet(wr.seller)
    wallet.available_balance += wr.amount
    wallet.pending_payout -= wr.amount
    wallet.save(update_fields=["available_balance", "pending_payout", "updated_at"])

    WalletTransaction.objects.create(
        wallet=wallet,
        txn_type=WalletTransaction.Type.REVERT,
        source=WalletTransaction.Source.WITHDRAWAL,
        amount=wr.amount,
        balance_after=wallet.available_balance,
        status=WalletTransaction.Status.SUCCESS,
        meta={"admin_note": note or ""},
    )

    wr.status = WithdrawalRequest.Status.REJECTED
    wr.admin_note = note or wr.admin_note
    wr.processed_at = timezone.now()
    wr.save(update_fields=["status", "admin_note", "processed_at"])

    seller_email = getattr(wr.seller, "email", None)
    if seller_email:
        try:
            send_mail(
                subject="Withdrawal Rejected",
                message=f"Your withdrawal request of ₹{wr.amount} has been rejected. Note: {note or ''}",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[seller_email],
                fail_silently=True,
            )
        except Exception:
            pass

    return wr

