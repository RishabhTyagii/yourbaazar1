from decimal import Decimal
from django.db import models
from django.utils import timezone
from seller.models import Seller

class SellerWallet(models.Model):
    seller = models.OneToOneField(Seller, on_delete=models.CASCADE, related_name='wallet')
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    pending_payout = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.seller.username} Wallet"

class WalletTransaction(models.Model):
    class Type(models.TextChoices):
        CREDIT = 'credit', 'Credit'
        DEBIT = 'debit', 'Debit'   # 👈 yeh add kar
        HOLD = 'hold', 'Hold'
        RELEASE = 'release', 'Release'
        REVERT = 'revert', 'Revert'

    class Status(models.TextChoices):
        SUCCESS = 'success', 'Success'
        PENDING = 'pending', 'Pending'
        FAILED = 'failed', 'Failed'

    class Source(models.TextChoices):
        ORDER_SETTLEMENT = 'order_settlement', 'Order Settlement'
        WITHDRAWAL = 'withdrawal', 'Withdrawal'

    wallet = models.ForeignKey(SellerWallet, on_delete=models.CASCADE, related_name='transactions')
    order = models.ForeignKey('order.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    txn_type = models.CharField(max_length=10, choices=Type.choices)
    source = models.CharField(max_length=20, choices=Source.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reference_id = models.CharField(max_length=100, blank=True, null=True)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.wallet.seller.username} | {self.txn_type} | {self.amount}"

class WithdrawalRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'requested', 'Requested'
        PROCESSING = 'processing', 'Processing'
        FAILED = 'failed', 'Failed'
        REJECTED = 'rejected', 'Rejected'
        COMPLETED = 'completed', 'Completed'
    
    # 👇 New fields
    account_holder_name = models.CharField(max_length=150, blank=True, null=True)
    bank_account_no = models.CharField(max_length=40, blank=True, null=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)

    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.REQUESTED)
    admin_note = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.seller.username} | {self.amount} | {self.status}"

class CommissionRule(models.Model):
    class Scope(models.TextChoices):
        GLOBAL = 'global', 'Global'
        PRODUCT = 'product', 'Product'

    class Type(models.TextChoices):
        PERCENT = 'percent', 'Percent'
        FLAT = 'flat', 'Flat'

    scope = models.CharField(max_length=10, choices=Scope.choices, default=Scope.GLOBAL)
    product = models.ForeignKey('seller_products.SellerProductMeta', on_delete=models.CASCADE, null=True, blank=True)
    commission_type = models.CharField(max_length=10, choices=Type.choices, default=Type.PERCENT)
    rate_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    flat_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_active(self, as_of=None):
        return self.active

    def __str__(self):
        if self.scope == self.Scope.GLOBAL:
            return f"Global {self.commission_type} Commission"
        return f"Product {self.product.product.name} {self.commission_type} Commission"


