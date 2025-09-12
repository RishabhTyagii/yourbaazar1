
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from .models import SellerWallet, WalletTransaction, WithdrawalRequest
from .services import request_withdrawal, reject_withdrawal,approve_withdrawal
from seller.views import require_seller_login
from django.contrib.admin.views.decorators import staff_member_required
from seller_products.models import Seller
from django.utils import timezone
from datetime import date

@require_seller_login
def wallet_dashboard(request):
    seller = request.seller
    wallet = SellerWallet.objects.filter(seller=seller).first()
    transactions_qs = wallet.transactions.order_by("-created_at") if wallet else WalletTransaction.objects.none()
    
    paginator = Paginator(transactions_qs, 10)  # 10 per page
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    # Total COD and ONLINE
    cod_total = transactions_qs.filter(meta__payment_method__iexact='cod').aggregate(
        total=Sum('amount'))['total'] or Decimal('0.00')
    online_total = transactions_qs.filter(meta__payment_method__iexact='online').aggregate(
        total=Sum('amount'))['total'] or Decimal('0.00')

    return render(request, 'wallet/seller_wallet.html', {
        "wallet": wallet,
        "transactions": transactions,
        "cod_total": cod_total,
        "online_total": online_total
    })

# @require_seller_login
# def withdrawal_request_view(request):
#     seller = request.seller
#     if request.method == "POST":
#         amount_str = (request.POST.get('amount') or "").strip()

#         try:
#             amount = Decimal(amount_str)
#         except InvalidOperation:
#             messages.error(request, "Invalid amount")
#             return redirect('wallet:withdraw_request')  # error → isi page par

#         try:
#             request_withdrawal(seller, amount)
#             messages.success(request, "Withdrawal requested")
#             return redirect('wallet:wallet_dashboard')  # ✅ success → dashboard
#         except Exception as e:
#             messages.error(request, str(e))
#             return redirect('wallet:withdraw_request')  # error → isi page par

#     return render(request, 'wallet/withdraw_request.html')

@require_seller_login
def withdrawal_request_view(request):
    seller = request.seller
    wallet = SellerWallet.objects.filter(seller=seller).first()
    # Sirf Saturday (5) aur Sunday (6) allow
    today = timezone.now().weekday()  # Monday=0 ... Sunday=6
    if today not in [1,3,5, 6]:
        messages.error(request, "Withdrawal requests are only allowed on Saturday and Sunday.")
        return render(request, "wallet/withdraw_request.html", {"seller": seller})

    if request.method == "POST":
        amount_str = (request.POST.get('amount') or "").strip()
        try:
            amount = Decimal(amount_str)
        except InvalidOperation:
            messages.error(request, "Invalid amount")
            return render(request, "wallet/withdraw_request.html", {"seller": seller})

        try:
            request_withdrawal(seller, amount)
            messages.success(request, "Withdrawal requested successfully")
            return redirect("wallet:wallet_dashboard")
        except Exception as e:
            messages.error(request, str(e))
            return render(request, "wallet/withdraw_request.html", {"seller": seller})

    return render(request, "wallet/withdraw_request.html", {"seller": seller,'wallet': wallet})





@staff_member_required
def admin_transactions(request):
    seller_id = request.GET.get("seller")
    sellers = Seller.objects.all()

    selected_seller = None
    wallet = None
    pending_requests = []
    transactions = []
    withdrawal_history = []  # ✅ Initialize empty
    cod_total = Decimal("0.00")
    online_total = Decimal("0.00")

    if seller_id:
        selected_seller = get_object_or_404(Seller, id=seller_id)
        wallet, _ = SellerWallet.objects.get_or_create(seller=selected_seller)

        # Withdrawal requests
        pending_requests = WithdrawalRequest.objects.filter(
            seller=selected_seller,
            status=WithdrawalRequest.Status.REQUESTED
        ).order_by("-requested_at")

        # Completed/Rejected Withdrawal History
        withdrawal_history = WithdrawalRequest.objects.filter(
            seller=selected_seller
        ).exclude(status=WithdrawalRequest.Status.REQUESTED).order_by("-requested_at")

        # Transactions queryset
        transactions_qs = WalletTransaction.objects.filter(
            wallet=wallet
        ).order_by("-created_at")

        # Pagination
        paginator = Paginator(transactions_qs, 10)  # 10 per page
        page_number = request.GET.get("page")
        transactions = paginator.get_page(page_number)

        # COD / ONLINE Totals
        cod_total = transactions_qs.filter(meta__payment_method__iexact="cod").aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

        online_total = transactions_qs.filter(meta__payment_method__iexact="online").aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

    context = {
        "sellers": sellers,
        "selected_seller": selected_seller,
        "wallet": wallet,
        "pending_requests": pending_requests,
        "transactions": transactions,
        "withdrawal_history": withdrawal_history,  # ✅ Pass to template
        "cod_total": cod_total,
        "online_total": online_total,
    }
    return render(request, "wallet/admin_transactions.html", context)




@staff_member_required
def admin_approve_withdrawal(request, wr_id):
    wr = get_object_or_404(
        WithdrawalRequest, id=wr_id, status=WithdrawalRequest.Status.REQUESTED
    )

    try:
        approve_withdrawal(wr, note="Approved by admin")
        messages.success(request, f"Withdrawal of ₹{wr.amount} approved for {wr.seller.username}")
    except ValueError as e:
        messages.error(request, str(e))

    return redirect("wallet:admin_transactions")


@staff_member_required
def admin_reject_withdrawal(request, wr_id):
    wr = get_object_or_404(
        WithdrawalRequest, id=wr_id, status=WithdrawalRequest.Status.REQUESTED
    )
    note = request.POST.get("note", "Rejected by admin")

    reject_withdrawal(wr, note=note)
    messages.warning(request, f"Withdrawal of ₹{wr.amount} rejected for {wr.seller.username}")

    return redirect("wallet:admin_transactions")



