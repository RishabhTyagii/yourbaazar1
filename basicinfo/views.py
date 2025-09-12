from django.shortcuts import render
# from.models import nav_image, footer, social_media, contact_us
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator
from django.shortcuts import render
from .models import contact_us, NavImage, footer, social_media
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from order.models import Order, OrderItem
from django.db.models import Sum, Count, F, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, ExtractWeekDay
# from django.core.paginator import Paginator

from django.db.models import Q
def contactus(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Save the contact information to the database
        contact_entry = contact_us(
            user=request.user if request.user.is_authenticated else None,
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )
        contact_entry.save()

        # Optionally, you can send a confirmation email or redirect to a success page
        return render(request, 'index.html')

    return render(request, 'basicinfo/contactus/contact_us.html')

@login_required
def contact_query_list(request):
    search_query = request.GET.get('q', '')
    queries = contact_us.objects.all()

    if search_query:
        queries = queries.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(subject__icontains=search_query)
        )

    paginator = Paginator(queries.order_by('-created_at'), 3)  # 10 queries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/contact_query_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
    })
@require_POST
@login_required
def toggle_query_status(request):
    query_id = request.POST.get('id')
    try:
        query = contact_us.objects.get(id=query_id)
        query.is_resolved = not query.is_resolved
        query.save()
        new_status_display = "✅ Resolved" if query.is_resolved else "❌ Unresolved"
        return JsonResponse({'success': True, 'new_status_display': new_status_display})
    except contact_us.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Query not found'})

def footer_data(request):
    footer_entries = footer.objects.all()
    social_links = social_media.objects.first()  # assuming only one record

    return render(request, 'partials/footer.html', {
        'footer_data': footer_entries,
        'social_links': social_links
    })
    
def ajax_navbar(request):
    nav_image_logo= NavImage.objects.all()
    return render(request, 'partials/nav.html',{
        'nav_image_logo':nav_image_logo
    })



def terms_and_conditions(request):
    context = {
        'title': 'Your Baazaar - Terms and Conditions',
        'last_updated': 'July 29, 2025',
    }
    return render(request, 'basicinfo/Terms_and_Conditions/Terms_and_Conditions.html', context)


def privacy_policy(request):
    return render(request, 'basicinfo/Privacy_Policy/Privacy_Policy.html', {
        'title': 'Privacy Policy | YourBaazar',
        # Add any dynamic data here if needed
    })
    
def about_us(request):
    return render(request, 'basicinfo/about_us/about_us.html', {
        'title': 'About US | YourBaazar',
        # Add any dynamic data here if needed
    })

def deliveryinfo(request):
    return render(request, 'basicinfo/deliveryinfo/deliveryinfo.html', {
        'title': 'deliveryinfo | YourBaazar',
        # Add any dynamic data here if needed
    })
    

logger = logging.getLogger(__name__)

def sales_dashboard(request):
    # Default time periods (last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    context = {
        'default_start': start_date.strftime('%Y-%m-%d'),
        'default_end': end_date.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin/sales_analysis.html', context)

def get_sales_data(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    period = request.GET.get('period', 'day')  # default to daily
    page = request.GET.get('page', 1)  # default to first page
    items_per_page = 10  # items per page for pagination

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except Exception as e:
        return JsonResponse({'error': 'Invalid date format.'}, status=400)

    # Filter completed orders
    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        status__in=['Delivered', 'Shipped']
    ).select_related('user').prefetch_related('items')

    # Choose truncation method for period grouping
    if period == 'week':
        trunc_func = TruncWeek
    elif period == 'month':
        trunc_func = TruncMonth
    else:
        trunc_func = TruncDay

    # Main sales data aggregation with pagination
    sales_data = (
        orders.annotate(period=trunc_func('created_at'))
              .values('period')
              .annotate(
                  total_sales=Sum('total_amount'),
                  order_count=Count('id'),
                  avg_order_value=Avg('total_amount')
              )
              .order_by('period')
    )
    
    # Paginate the sales data
    paginator = Paginator(sales_data, items_per_page)
    paginated_data = paginator.get_page(page)
    
    # Prepare chart data (using all data, not just paginated)
    labels = [entry['period'].strftime('%Y-%m-%d') for entry in sales_data]
    sales = [float(entry['total_sales'] or 0 )for entry in sales_data]
    order_counts = [entry['order_count'] or 0 for entry in sales_data]
    avg_order_values = [float(entry['avg_order_value'] or 0) for entry in sales_data]

    # Calculate summary metrics
    total_sales = sum(sales)
    total_orders = orders.count()
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0
    
    # Top products by revenue with pagination
    top_products = (
        OrderItem.objects.filter(order__in=orders)
        .values('product__name')
        .annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('price'))
        )
        .order_by('-total_revenue')
    )
    top_products_paginator = Paginator(top_products, items_per_page)
    top_products_page = top_products_paginator.get_page(page)
    
    # Sales by day of week
    day_of_week_data = (
        orders.annotate(day_of_week=ExtractWeekDay('created_at'))
        .values('day_of_week')
        .annotate(
            total_sales=Sum('total_amount'),
            order_count=Count('id')
        )
        .order_by('day_of_week')
    )
    
    # Convert day numbers to names
    day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    day_of_week_labels = []
    day_of_week_sales = [0] * 7
    day_of_week_counts = [0] * 7
    
    for entry in day_of_week_data:
        day_index = entry['day_of_week'] - 1  # Django returns 1-7 (Sun-Sat)
        day_of_week_sales[day_index] = float(entry['total_sales'] or 0)
        day_of_week_counts[day_index] = entry['order_count'] or 0
    
    day_of_week_labels = day_names
    
    # Customer metrics
    new_customers = orders.values('user').distinct().count()
    repeat_customers = orders.values('user').annotate(
        order_count=Count('id')
    ).filter(order_count__gt=1).count()
    
    # Payment method breakdown
    payment_methods = (
        orders.values('payment_method')
        .annotate(
            total_sales=Sum('total_amount'),
            order_count=Count('id')
        )
        .order_by('-total_sales')
    )
    
    # Status distribution
    status_distribution = (
        orders.values('status')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    return JsonResponse({
        'labels': labels,
        'sales': sales,
        'order_counts': order_counts,
        'avg_order_values': avg_order_values,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'top_products': {
            'data': list(top_products_page.object_list),
            'has_next': top_products_page.has_next(),
            'has_previous': top_products_page.has_previous(),
            'page_number': top_products_page.number,
            'total_pages': top_products_page.paginator.num_pages
        },
        'day_of_week': {
            'labels': day_of_week_labels,
            'sales': day_of_week_sales,
            'counts': day_of_week_counts
        },
        'customer_metrics': {
            'new_customers': new_customers,
            'repeat_customers': repeat_customers
        },
        'payment_methods': list(payment_methods),
        'status_distribution': list(status_distribution),
        'pagination': {
            'has_next': paginated_data.has_next(),
            'has_previous': paginated_data.has_previous(),
            'page_number': paginated_data.number,
            'total_pages': paginated_data.paginator.num_pages
        }
    })
# ===========================================

from django.shortcuts import render
from decimal import Decimal
from collections import defaultdict
from order.models import OrderItem  # adjust import path if different

def profit_analysis_view(request):
    # Fetch delivered, non-free items with required related fields
    order_items = OrderItem.objects.select_related(
        'variant', 'product', 'order', 'variant__color'
    ).filter(
        order__status='Delivered',
        is_free=False,
        variant__isnull=False,
        variant__price_we_buy__isnull=False,
    ).order_by('-order__created_at')

    # Precompute total quantity per order (for proportional shipping share)
    order_quantity_map = {}
    for item in order_items:
        order_quantity_map.setdefault(item.order_id, 0)
        order_quantity_map[item.order_id] += item.quantity

    data = []
    total_revenue = Decimal('0')
    total_cost = Decimal('0')
    total_shipping = Decimal('0')  # sum of order-level shipping once each
    total_gross_profit = Decimal('0')  # before shipping
    total_net_profit = Decimal('0')    # after shipping
    processed_orders_for_shipping = set()

    # Detailed per order-item breakdown
    for item in order_items:
        unit_selling_price = item.get_unit_price()
        unit_cost_price = item.variant.price_we_buy
        quantity = item.quantity

        revenue = unit_selling_price * quantity
        cost = unit_cost_price * quantity
        profit_before_shipping = revenue - cost

        # Proportional shipping share for this item
        order_total_qty = order_quantity_map.get(item.order_id, 1)
        shipping_share = Decimal('0')
        if order_total_qty > 0:
            shipping_share = item.order.shipping_cost * (Decimal(quantity) / Decimal(order_total_qty))

        profit_after_shipping = profit_before_shipping - shipping_share

        # Count order-level shipping once
        if item.order.id not in processed_orders_for_shipping:
            total_shipping += item.order.shipping_cost
            processed_orders_for_shipping.add(item.order.id)

        total_revenue += revenue
        total_cost += cost
        total_gross_profit += profit_before_shipping
        total_net_profit += profit_after_shipping

        data.append({
            'order_number': item.order.order_number,
            'product': item.product.name,
            'variant': f"{item.variant.color.color_name} - {item.variant.size}",
            'quantity': quantity,
            'selling_price': unit_selling_price,
            'cost_price': unit_cost_price,
            'shipping_share': shipping_share.quantize(Decimal('0.01')),
            'total_revenue': revenue.quantize(Decimal('0.01')),
            'total_cost': cost.quantize(Decimal('0.01')),
            'profit_before_shipping': profit_before_shipping.quantize(Decimal('0.01')),
            'profit_after_shipping': profit_after_shipping.quantize(Decimal('0.01')),
            'order_date': item.order.created_at.date(),
        })

    # Variant-level aggregation (with shipping share)
    variant_summary = defaultdict(lambda: {
        'product': '',
        'variant': '',
        'quantity': 0,
        'revenue': Decimal('0'),
        'cost': Decimal('0'),
        'shipping': Decimal('0'),
        'profit_before_shipping': Decimal('0'),
        'profit_after_shipping': Decimal('0'),
    })

    for item in order_items:
        key = item.variant.id
        unit_selling_price = item.get_unit_price()
        unit_cost_price = item.variant.price_we_buy
        quantity = item.quantity

        revenue = unit_selling_price * quantity
        cost = unit_cost_price * quantity
        profit_before = revenue - cost

        order_total_qty = order_quantity_map.get(item.order_id, 1)
        shipping_share = Decimal('0')
        if order_total_qty > 0:
            shipping_share = item.order.shipping_cost * (Decimal(quantity) / Decimal(order_total_qty))
        profit_after = profit_before - shipping_share

        variant_summary[key]['product'] = item.product.name
        variant_summary[key]['variant'] = f"{item.variant.color.color_name} - {item.variant.size}"
        variant_summary[key]['quantity'] += quantity
        variant_summary[key]['revenue'] += revenue
        variant_summary[key]['cost'] += cost
        variant_summary[key]['shipping'] += shipping_share
        variant_summary[key]['profit_before_shipping'] += profit_before
        variant_summary[key]['profit_after_shipping'] += profit_after

    # Normalize / quantize for display
    variant_data = []
    for v in variant_summary.values():
        variant_data.append({
            'product': v['product'],
            'variant': v['variant'],
            'quantity': v['quantity'],
            'revenue': v['revenue'].quantize(Decimal('0.01')),
            'cost': v['cost'].quantize(Decimal('0.01')),
            'shipping': v['shipping'].quantize(Decimal('0.01')),
            'profit_before_shipping': v['profit_before_shipping'].quantize(Decimal('0.01')),
            'profit_after_shipping': v['profit_after_shipping'].quantize(Decimal('0.01')),
        })

    context = {
        'data': data,
        'variant_data': variant_data,
        'total_revenue': total_revenue.quantize(Decimal('0.01')),
        'total_cost': total_cost.quantize(Decimal('0.01')),
        'total_shipping': total_shipping.quantize(Decimal('0.01')),
        'gross_profit': total_gross_profit.quantize(Decimal('0.01')),
        'total_profit': total_net_profit.quantize(Decimal('0.01')),  # after shipping
        'order_count': len(processed_orders_for_shipping),
    }

    return render(request, 'admin/profit_analysis.html', context)

























 
