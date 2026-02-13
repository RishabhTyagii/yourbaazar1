# seller_products/forms.py
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet

from .models import SellerProductDraft, DraftColor, DraftVariant

class SellerProductDraftForm(forms.ModelForm):
    class Meta:
        model = SellerProductDraft
        fields = [
            'category', 'subcategory', 'product_type',
            'category_other', 'subcategory_other', 'product_type_other',
            'name', 'sku', 'short_description', 'description',
            'thumbnail',
            'payment_mode', 'shipping_by',
            'length_cm', 'width_cm', 'height_cm', 'weight_kg',
            'minimum_shipping',
            'brand',
            
            'size_price_explanation',
        ]
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 2}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'size_price_explanation': forms.Textarea(attrs={'rows': 2}),
        }
        

class DraftColorForm(forms.ModelForm):
    class Meta:
        model = DraftColor
        fields = ['color_name', 'color_code', 'image_main', 'image1', 'image2', 'image3']

class DraftVariantForm(forms.ModelForm):
    class Meta:
        model = DraftVariant
        fields = ['size', 'stock', 'price_before_discount', 'discount', 'price_we_buy']

class RequiredBaseInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False

ColorFormSet = inlineformset_factory(
    SellerProductDraft, DraftColor, form=DraftColorForm,
    fields=None, extra=1, can_delete=True
)

VariantFormSet = inlineformset_factory(
    DraftColor, DraftVariant, form=DraftVariantForm,
    fields=None, extra=1, can_delete=True
)


# --- forms.py (add these to your existing file) ---
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet, formset_factory

from .models import SellerProductDraft, DraftColor, DraftVariant, SellerProductMeta
from product.models import product as Product, ProductColor, ProductVariant


class ProductEditForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "short_description",
            "description",
            "thumbnail",
            "image",  # keep if your model has it
            "base_price",
            "cod_available",
            "shipping_charge",
            "brand",
            "is_available",
        ]
        widgets = {
            "short_description": forms.Textarea(attrs={"rows": 2}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "shipping_charge": forms.NumberInput(attrs={"readonly": "readonly"})
        }


class ProductColorForm(forms.ModelForm):
    class Meta:
        model = ProductColor
        fields = [
            "color_name",
            "color_code",
            "image_main",
            "image1",
            "image2",
            "image3",
        ]


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = [
            "size",
            "stock",
            "price_before_discount",
            "discount",
            "price_we_buy",
        ]


class SellerProductMetaForm(forms.ModelForm):
    class Meta:
        model = SellerProductMeta
        fields = [
            "payment_mode",
            "shipping_by",
            "minimum_shipping",
            "length_cm",
            "width_cm",
            "height_cm",
            "weight_kg",
            "brand",
            "size_price_explanation",

        ]
        widgets = {
            "minimum_shipping": forms.NumberInput(attrs={"readonly": "readonly"}),
        }

# Inline FS for ProductColor under Product
ProductColorFormSet = inlineformset_factory(
    parent_model=Product,
    model=ProductColor,
    form=ProductColorForm,
    extra=0,
    can_delete=True,
)

# Simple (non-inline) FS for ProductVariant we will link manually per color like your draft create flow
ProductVariantSimpleFormSet = formset_factory(ProductVariantForm, extra=0, can_delete=True)



# seller_products/forms.py
from django import forms
from dal import autocomplete
from .models import SellerProductDraft

class SellerProductDraftAdminForm(forms.ModelForm):
    class Meta:
        model = SellerProductDraft
        fields = '__all__'
        widgets = {
            'category': autocomplete.ModelSelect2(
                url='product:category-autocomplete'
            ),
            'subcategory': autocomplete.ModelSelect2(
                url='product:subcategory-autocomplete',
                forward=['category'],
            ),
            'product_type': autocomplete.ModelSelect2(
                url='product:product-type-autocomplete',
                forward=['category', 'subcategory'],
            ),
        }





