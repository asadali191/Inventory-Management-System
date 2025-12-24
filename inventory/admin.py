from django.contrib import admin
from .models import (
    Product, Customer, StockLocation, StockBalance, StockLedger,
    Invoice, InvoiceLine, Return, ReturnLine
)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("product_name", "sku", "color", "size", "selling_price", "is_active")
    search_fields = ("product_name", "sku", "barcode_value")

admin.site.register(Customer)
admin.site.register(StockLocation)
admin.site.register(StockBalance)
admin.site.register(StockLedger)
admin.site.register(Invoice)
admin.site.register(InvoiceLine)
admin.site.register(Return)
admin.site.register(ReturnLine)
