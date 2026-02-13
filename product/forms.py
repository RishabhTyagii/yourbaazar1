# product/forms.py
from django import forms
from dal import autocomplete
from .models import product, product_type

class ProductForm(forms.ModelForm):
    class Meta:
        model = product
        fields = '__all__'
        widgets = {
            'category': autocomplete.ModelSelect2(url='product:category-autocomplete'),
            'subcategory': autocomplete.ModelSelect2(
                url='product:subcategory-autocomplete',
                forward=['category'],
            ),
            'product_type': autocomplete.ModelSelect2(
                url='product:product-type-autocomplete',
                forward=['category', 'subcategory'],
            ),
        }

class ProductTypeForm(forms.ModelForm):
    class Meta:
        model = product_type
        fields = '__all__'
        widgets = {
            'category': autocomplete.ModelSelect2(url='product:category-autocomplete'),
            'subcategory': autocomplete.ModelSelect2(
                url='product:subcategory-autocomplete',
                forward=['category'],
            ),
        }
