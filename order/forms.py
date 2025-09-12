from django import forms
from order.models import Order,ReturnRequest, OrderItem 

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'customer_name',
            'customer_email', 
            'customer_phone',
            'shipping_address',
            'shipping_city',
            'shipping_state',
            'shipping_pin_code'
        ]
        
    # Add labels/placeholders if needed
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer_name'].label = 'Full Name'
        self.fields['customer_email'].label = 'Email Address'
        self.fields['customer_phone'].label = 'Phone Number'
        self.fields['shipping_address'].label = 'Street Address'
        self.fields['shipping_city'].label = 'City'
        self.fields['shipping_state'].label = 'State'
        self.fields['shipping_pin_code'].label = 'PIN Code'


class OrderStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']


# forms.py
from django import forms
from order.models import Order, ReturnRequest, OrderItem

class ReturnRequestForm(forms.ModelForm):
    class Meta:
        model = ReturnRequest
        fields = [
            'order',
            'order_item',
            'customer_name',
            'customer_email',
            'customer_phone',
            'reason',
            'image1', 'image2', 'image3', 'image4',
        ]
        widgets = {
            'order_item': forms.RadioSelect
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['order_item'].queryset = OrderItem.objects.none()

        if user:
            self.fields['order'].queryset = Order.objects.filter(user=user, status__iexact='Delivered')

        if 'order' in self.data:
            try:
                order_id = int(self.data.get('order'))
                delivered_items = OrderItem.objects.filter(order_id=order_id, item_status__iexact='delivered')
                already_returned = ReturnRequest.objects.filter(order_id=order_id).values_list('order_item_id', flat=True)
                eligible_items = delivered_items.exclude(id__in=already_returned)
                self.fields['order_item'].queryset = eligible_items
            except Exception:
                pass

    def clean(self):
        cleaned_data = super().clean()
        order_item = cleaned_data.get('order_item')

        if order_item:
            if ReturnRequest.objects.filter(order_item=order_item).exists():
                raise forms.ValidationError("This item already has a return request.")
            if order_item.item_status.lower() != 'delivered':
                raise forms.ValidationError("This product is not marked as 'delivered'.")

        if not any(cleaned_data.get(f'image{i}') for i in range(1, 5)):
            raise forms.ValidationError("Upload at least one image.")

        return cleaned_data


