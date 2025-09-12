from decimal import Decimal, ROUND_HALF_UP
import csv
from io import StringIO
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Value
from django.db.models.functions import TruncMonth, Coalesce
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator

from seller.models import Seller
from order.models import OrderItem
from seller_products.models import SellerProductMeta
from product.models import product as ProductModel
from wallet import services as wallet_services  # uses resolve_commission_for_product / compute_fees

# reuse your existing require_seller_login decorator from seller_products.views
from seller_products.views import require_seller_login  # adjust import if needed

# ---- Constants ----
DECIMAL12_2 = DecimalField(max_digits=12, decimal_places=2)
ZERO_DECIMAL = Value(0, output_field=DECIMAL12_2)

EXCLUDE_ORDER_STATUSES = ["Cancelled", "Returned", "Refunded"]
EXCLUDE_ITEM_STATUSES = ["cancelled", "returned"]


# ---- Helpers ----
def _seller_product_ids(seller):
    return list(SellerProductMeta.objects.filter(seller=seller).values_list("product_id", flat=True))


def _line_total_expr():
    return ExpressionWrapper(
        (F("price") - Coalesce(F("discount_price"), ZERO_DECIMAL)) * 
        ExpressionWrapper(F("quantity"), output_field=DECIMAL12_2),
        output_field=DECIMAL12_2
    )


# ---- Views ----
@require_seller_login
def profit_dashboard(request):
    seller = request.seller

    # Filters
    start = request.GET.get("start")
    end = request.GET.get("end")
    payment_method = request.GET.get("payment_method")
    status = request.GET.get("status")

    common_filters = {}
    if start and end:
        common_filters["order__created_at__date__range"] = (start, end)
    if payment_method:
        common_filters["order__payment_method__iexact"] = payment_method
    if status:
        common_filters["order__status__iexact"] = status

    product_ids = _seller_product_ids(seller)
    if not product_ids:
        return render(request, "seller/reports_profit.html", {"seller": seller, "message": "No products found for this seller."})

    # ALL sales
    all_items_qs = OrderItem.objects.filter(product_id__in=product_ids)
    if common_filters:
        all_items_qs = all_items_qs.filter(**common_filters)

    total_orders_all = all_items_qs.values_list("order_id", flat=True).distinct().count()
    total_sales_all = all_items_qs.aggregate(
        total=Coalesce(Sum(_line_total_expr(), output_field=DECIMAL12_2), ZERO_DECIMAL)
    )["total"]

    # NET sales
    net_items_qs = OrderItem.objects.filter(product_id__in=product_ids).exclude(order__status__in=EXCLUDE_ORDER_STATUSES).exclude(item_status__in=EXCLUDE_ITEM_STATUSES)
    if common_filters:
        net_items_qs = net_items_qs.filter(**common_filters)

    total_sales_net = net_items_qs.aggregate(
        total=Coalesce(Sum(_line_total_expr(), output_field=DECIMAL12_2), ZERO_DECIMAL)
    )["total"]

    # Commission calc (optimized)
    product_ids_in_net = list(net_items_qs.values_list("product_id", flat=True).distinct())
    commission_rule_by_pid = {}
    for pid in product_ids_in_net:
        try:
            p = ProductModel.objects.get(id=pid)
            commission_rule_by_pid[pid] = wallet_services.resolve_commission_for_product(p, as_of=timezone.now())
        except ProductModel.DoesNotExist:
            commission_rule_by_pid[pid] = None

    product_agg = net_items_qs.values("product_id").annotate(
        qty_sum=Coalesce(Sum(ExpressionWrapper(F("quantity"), output_field=DECIMAL12_2)), ZERO_DECIMAL),
        gross_sum=Coalesce(Sum(_line_total_expr(), output_field=DECIMAL12_2), ZERO_DECIMAL)
)

    commission_total = Decimal("0.00")
    for row in product_agg:
        pid = row["product_id"]
        gross = Decimal(str(row["gross_sum"] or 0))
        qty = Decimal(str(row["qty_sum"] or 0))

        per_unit_price = (gross / qty) if qty > 0 else Decimal("0.00")
        rule = commission_rule_by_pid.get(pid)
        per_unit_comm = Decimal("0.00")
        if rule:
            ctype = getattr(rule, "commission_type", "").lower()
            if ctype == "percent" and getattr(rule, "rate_percent", None) is not None:
                per_unit_comm = (per_unit_price * Decimal(str(rule.rate_percent)) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            elif ctype == "flat" and getattr(rule, "flat_amount", None) is not None:
                per_unit_comm = Decimal(str(rule.flat_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        commission_total += (per_unit_comm * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # PG Fees
    order_agg = net_items_qs.values("order_id", "order__payment_method").annotate(
        order_gross=Coalesce(Sum((F("price") - Coalesce(F("discount_price"), ZERO_DECIMAL)) * F("quantity"), output_field=DECIMAL12_2), ZERO_DECIMAL)
    )
    pg_fee_total = Decimal("0.00")
    for o in order_agg:
        gross = Decimal(str(o["order_gross"] or 0))
        payment_method = (o.get("order__payment_method") or "").lower()
        try:
            pg_fee_total += wallet_services.compute_fees(gross, payment_method)
        except Exception:
            pass

    # Shipping
    shipping_total = Decimal(str(net_items_qs.aggregate(s=Coalesce(Sum("shipping_cost"), ZERO_DECIMAL))["s"] or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Refunds
    refund_qs = OrderItem.objects.filter(product_id__in=product_ids, order__status__in=["Refunded", "Returned"])
    if common_filters:
        refund_qs = refund_qs.filter(**common_filters)
    refunds_total = Decimal(str(refund_qs.aggregate(
        total=Coalesce(Sum((F("price") - Coalesce(F("discount_price"), ZERO_DECIMAL)) * F("quantity"), output_field=DECIMAL12_2), ZERO_DECIMAL)
    )["total"] or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Profit
    net_profit = (Decimal(str(total_sales_net or 0)) - commission_total - pg_fee_total - refunds_total ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Top Products
    product_profit_map = {}
    for row in product_agg:
        pid = row["product_id"]
        gross = Decimal(str(row["gross_sum"] or 0))
        qty = Decimal(str(row["qty_sum"] or 0))
        rule = commission_rule_by_pid.get(pid)
        per_unit_price = (gross / qty) if qty > 0 else Decimal("0")
        per_unit_comm = Decimal("0.00")
        if rule:
            if getattr(rule, "commission_type", "").lower() == "percent" and getattr(rule, "rate_percent", None) is not None:
                per_unit_comm = (per_unit_price * Decimal(str(rule.rate_percent)) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            elif getattr(rule, "commission_type", "").lower() == "flat" and getattr(rule, "flat_amount", None) is not None:
                per_unit_comm = Decimal(str(rule.flat_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        prof = gross - (per_unit_comm * qty)
        product_profit_map[pid] = prof

    sorted_products = sorted(product_profit_map.items(), key=lambda x: x[1], reverse=True)
    product_ids_sorted = [pid for pid, _ in sorted_products]
    products_qs = ProductModel.objects.filter(id__in=product_ids_sorted)
    products_by_id = {p.id: p for p in products_qs}
    product_rows = [{"product": products_by_id[pid], "profit": prof} for pid, prof in sorted_products if pid in products_by_id]

    page = request.GET.get("page", 1)
    paginator = Paginator(product_rows, 10)
    page_obj = paginator.get_page(page)

    context = {
        "seller": seller,
        "total_orders_all": total_orders_all,
        "total_sales_all": total_sales_all,
        "total_sales_net": total_sales_net,
        "commission_total": commission_total,
        "pg_fee_total": pg_fee_total,
        "shipping_total": shipping_total,
        "refunds_total": refunds_total,
        "net_profit": net_profit,
        "top_products_page": page_obj,
        "start": start,
        "end": end,
        "payment_method_filter": payment_method,
        "status_filter": status,
    }
    return render(request, "seller/reports_profit.html", context)


@require_GET
@require_seller_login
def profit_chart_data(request):
    seller = request.seller
    start = request.GET.get("start")
    end = request.GET.get("end")

    product_ids = _seller_product_ids(seller)
    qs = OrderItem.objects.filter(product_id__in=product_ids).exclude(order__status__in=EXCLUDE_ORDER_STATUSES).exclude(item_status__in=EXCLUDE_ITEM_STATUSES)
    if start and end:
        qs = qs.filter(order__created_at__date__range=(start, end))

    rows = (
        qs.annotate(month=TruncMonth("order__created_at"))
          .values("month")
          .annotate(gross=Coalesce(Sum((F("price") - Coalesce(F("discount_price"), ZERO_DECIMAL)) * F("quantity"), output_field=DECIMAL12_2), ZERO_DECIMAL))
          .order_by("month")
    )

    labels, gross_values, commission_values = [], [], []

    for r in rows:
        month = r["month"]
        labels.append(month.strftime("%Y-%m"))
        gross = Decimal(str(r["gross"] or 0))
        gross_values.append(float(gross))
        

        month_items = qs.filter(order__created_at__year=month.year, order__created_at__month=month.month)
        month_prod_agg = month_items.values("product_id").annotate(
            # qty_sum=Coalesce(Sum("quantity"), ZERO_DECIMAL),
            qty_sum=Coalesce(
    Sum(ExpressionWrapper(F("quantity"), output_field=DECIMAL12_2)),
    ZERO_DECIMAL
),
            gross_sum=Coalesce(Sum((F("price") - Coalesce(F("discount_price"), ZERO_DECIMAL)) * F("quantity"), output_field=DECIMAL12_2), ZERO_DECIMAL)
        )
        month_comm = Decimal("0.00")
        rules = {}
        for pid in [m["product_id"] for m in month_prod_agg]:
            try:
                p = ProductModel.objects.get(id=pid)
                rules[pid] = wallet_services.resolve_commission_for_product(p, as_of=timezone.now())
            except ProductModel.DoesNotExist:
                rules[pid] = None

        for m in month_prod_agg:
            pid, qty, gross_sum = m["product_id"], Decimal(str(m["qty_sum"] or 0)), Decimal(str(m["gross_sum"] or 0))
            per_unit = (gross_sum / qty) if qty > 0 else Decimal("0")
            rule = rules.get(pid)
            per_unit_comm = Decimal("0.00")
            if rule:
                if getattr(rule, "commission_type", "").lower() == "percent" and getattr(rule, "rate_percent", None) is not None:
                    per_unit_comm = (per_unit * Decimal(str(rule.rate_percent)) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                elif getattr(rule, "commission_type", "").lower() == "flat" and getattr(rule, "flat_amount", None) is not None:
                    per_unit_comm = Decimal(str(rule.flat_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            month_comm += (per_unit_comm * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        commission_values.append(float(month_comm))

    return JsonResponse({"labels": labels, "gross": gross_values, "commission": commission_values})


@require_seller_login
def export_profit_csv(request):
    seller = request.seller
    start = request.GET.get("start")
    end = request.GET.get("end")
    payment_method = request.GET.get("payment_method")
    status = request.GET.get("status")

    common_filters = {}
    if start and end:
        common_filters["order__created_at__date__range"] = (start, end)
    if payment_method:
        common_filters["order__payment_method__iexact"] = payment_method
    if status:
        common_filters["order__status__iexact"] = status

    product_ids = _seller_product_ids(seller)
    qs = OrderItem.objects.filter(product_id__in=product_ids)
    if common_filters:
        qs = qs.filter(**common_filters)

    header = ["Order ID", "Order Date", "Product ID", "Product Name", "Qty", "Unit Price", "Discount", "Line Gross", "Commission (est)", "Shipping Cost", "Order Status", "Payment Method"]
    rows, rules = [], {}

    for pid in qs.values_list("product_id", flat=True).distinct():
        try:
            p = ProductModel.objects.get(id=pid)
            rules[pid] = wallet_services.resolve_commission_for_product(p, as_of=timezone.now())
        except ProductModel.DoesNotExist:
            rules[pid] = None

    for oi in qs.select_related("order", "product"):
        unit_price = (oi.price or Decimal("0")) - (oi.discount_price or Decimal("0"))
        qty = Decimal(oi.quantity or 0)
        line_gross = (unit_price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        rule, per_unit_comm = rules.get(oi.product_id), Decimal("0.00")
        if rule:
            if getattr(rule, "commission_type", "").lower() == "percent" and getattr(rule, "rate_percent", None) is not None:
                per_unit_comm = (unit_price * Decimal(str(rule.rate_percent)) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            elif getattr(rule, "commission_type", "").lower() == "flat" and getattr(rule, "flat_amount", None) is not None:
                per_unit_comm = Decimal(str(rule.flat_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        commission_line = (per_unit_comm * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        rows.append([
            str(oi.order_id),
            oi.order.created_at.strftime("%Y-%m-%d"),
            str(oi.product_id),
            getattr(oi.product, "name", ""),
            str(int(qty)),
            str(unit_price),
            str(oi.discount_price or 0),
            str(line_gross),
            str(commission_line),
            str(oi.shipping_cost or 0),
            oi.order.status,
            oi.order.payment_method,
        ])

    csvfile = StringIO()
    writer = csv.writer(csvfile)
    writer.writerow(header)
    writer.writerows(rows)
    csvfile.seek(0)
    resp = HttpResponse(csvfile.read(), content_type="text/csv")
    fname = f"seller_{seller.id}_profit_{start or 'all'}_{end or 'all'}.csv"
    resp["Content-Disposition"] = f'attachment; filename="{fname}"'
    return resp
