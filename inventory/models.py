from django.db import models
from django.utils import timezone

class Customer(models.Model):
    TYPE_CHOICES = [
        ("retail", "Retail"),
        ("wholesale", "Wholesale"),
        ("local_supply", "Local Supply"),
    ]
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    customer_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="retail")

    def __str__(self):
        return self.name

class StockLocation(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    product_name = models.CharField(max_length=200)
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=50, blank=True)
    sku = models.CharField(max_length=80, unique=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    product_image = models.ImageField(upload_to="products/", blank=True, null=True)

    barcode_value = models.CharField(max_length=120, blank=True)  # default = sku
    barcode_image = models.ImageField(upload_to="barcodes/", blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.product_name} ({self.sku})"

class StockBalance(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE)
    on_hand_qty = models.IntegerField(default=0)
    reserved_qty = models.IntegerField(default=0)
    last_updated = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("product", "location")

    @property
    def available_qty(self):
        return self.on_hand_qty - self.reserved_qty

class StockLedger(models.Model):
    MOVE_CHOICES = [
        ("IN", "IN"),
        ("OUT", "OUT"),
        ("RETURN", "RETURN"),
        ("ADJUST", "ADJUST"),
    ]
    date_time = models.DateTimeField(default=timezone.now)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    location = models.ForeignKey(StockLocation, on_delete=models.PROTECT)

    movement_type = models.CharField(max_length=10, choices=MOVE_CHOICES)
    qty = models.IntegerField()  # positive qty
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    reference_type = models.CharField(max_length=30, blank=True)
    reference_no = models.CharField(max_length=60, blank=True)
    customer_name = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.movement_type} {self.product.sku} x{self.qty}"

class Invoice(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("FINAL", "Final"),
        ("CANCELLED", "Cancelled"),
    ]
    invoice_no = models.CharField(max_length=40, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True)
    customer_name_fallback = models.CharField(max_length=200, blank=True)
    location = models.ForeignKey(StockLocation, on_delete=models.PROTECT)

    date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def customer_display(self):
        return self.customer.name if self.customer else (self.customer_name_fallback or "Walk-in")

class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="lines", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.IntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

class Return(models.Model):
    return_no = models.CharField(max_length=40, unique=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True)
    location = models.ForeignKey(StockLocation, on_delete=models.PROTECT)
    date = models.DateTimeField(default=timezone.now)
    total_refund = models.DecimalField(max_digits=12, decimal_places=2, default=0)

class ReturnLine(models.Model):
    return_doc = models.ForeignKey(Return, related_name="lines", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.IntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
