from django import forms
from .models import Product, StockLocation, Customer


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "product_name", "color", "size", "sku",
            "cost", "price", "selling_price",
            "product_image", "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # new product default active
        self.fields["is_active"].initial = True


class StockLocationForm(forms.ModelForm):
    class Meta:
        model = StockLocation
        fields = ["name"]


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "address", "customer_type"]
