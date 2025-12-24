from rest_framework import serializers
from .models import Product, Invoice, InvoiceLine, Return, ReturnLine

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id", "product_name", "color", "size", "sku",
            "cost", "price", "selling_price",
            "barcode_value", "barcode_image", "product_image"
        ]

class InvoiceLineInputSerializer(serializers.Serializer):
    sku = serializers.CharField()
    qty = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

class InvoiceCreateSerializer(serializers.Serializer):
    location_id = serializers.IntegerField()
    customer_id = serializers.IntegerField(required=False)
    customer_name_fallback = serializers.CharField(required=False, allow_blank=True)
    lines = InvoiceLineInputSerializer(many=True)

class ReturnLineInputSerializer(serializers.Serializer):
    sku = serializers.CharField()
    qty = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

class ReturnCreateSerializer(serializers.Serializer):
    location_id = serializers.IntegerField()
    invoice_no = serializers.CharField(required=False, allow_blank=True)
    customer_id = serializers.IntegerField(required=False)
    lines = ReturnLineInputSerializer(many=True)
