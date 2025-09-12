from django.contrib import admin

# Register your models here.
from . models import SellerWallet,CommissionRule,WithdrawalRequest,WalletTransaction
admin.site.register(SellerWallet)

admin.site.register(CommissionRule)
admin.site.register(WithdrawalRequest)
admin.site.register(WalletTransaction)