# inventory/views.py
from __future__ import annotations

from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .models import (
    Product,
    Customer,
    StockLocation,
    StockBalance,
    StockLedger,
)
from .services import ensure_product_barcode
from .forms import StockLocationForm, CustomerForm


# ---------------------------
# Dashboard
# ---------------------------
def dashboard(request):
    return render(request, "dashboard.html")


# ---------------------------
# Products
# ---------------------------
def products_list(request):
    qs = Product.objects.all().order_by("-id")
    # NOTE: keep same template name you already have
    return render(request, "products.html", {"products": qs})


@require_http_methods(["GET", "POST"])
def product_create(request):
    """
    Works even if you don't use forms.ProductForm.
    Auto barcode generate if active.
    """
    from django.forms import ModelForm

    class ProductForm(ModelForm):
        class Meta:
            model = Product
            fields = "__all__"

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            p = form.save()
            ensure_product_barcode(p)
            messages.success(request, "Product created successfully ✅")
            return redirect("products_list")
        messages.error(request, "Please fix the errors and try again.")
    else:
        form = ProductForm()

    return render(request, "product_create.html", {"form": form})


@require_http_methods(["GET", "POST"])
def product_edit(request, pk: int):
    from django.forms import ModelForm

    product = get_object_or_404(Product, pk=pk)

    class ProductForm(ModelForm):
        class Meta:
            model = Product
            fields = "__all__"

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            p = form.save()
            ensure_product_barcode(p)
            messages.success(request, "Product updated successfully ✅")
            return redirect("products_list")
        messages.error(request, "Please fix the errors and try again.")
    else:
        form = ProductForm(instance=product)

    return render(request, "product_edit.html", {"form": form, "product": product})


@require_POST
def product_activate(request, pk: int):
    product = get_object_or_404(Product, pk=pk)

    if hasattr(product, "is_active"):
        product.is_active = True
        product.save(update_fields=["is_active"])
        ensure_product_barcode(product, force=True)
        messages.success(request, "Product activated & barcode generated ✅")
    else:
        messages.error(request, "This Product model has no is_active field.")

    return redirect("products_list")


def product_barcode_print(request, pk: int):
    p = get_object_or_404(Product, pk=pk)
    # Make sure template exists: inventory/templates/barcode_print.html
    return render(request, "barcode_print.html", {"p": p})


# ---------------------------
# Stock In  (✅ FIX: locations dropdown + stock update)
# ---------------------------
@require_http_methods(["GET", "POST"])
def stock_in(request):
    locations = StockLocation.objects.all().order_by("name")

    if request.method == "POST":
        location_id = request.POST.get("location_id")
        sku = (request.POST.get("sku") or "").strip()
        qty_raw = request.POST.get("qty") or "0"
        reference_no = (request.POST.get("reference_no") or "").strip()
        notes = (request.POST.get("notes") or "").strip()

        try:
            qty = int(qty_raw)
        except Exception:
            qty = 0

        if not location_id or not sku or qty <= 0:
            messages.error(request, "Location, SKU, Qty required.")
            return render(request, "stock_in.html", {"locations": locations})

        location = get_object_or_404(StockLocation, pk=location_id)
        product = get_object_or_404(Product, sku=sku)

        with transaction.atomic():
            bal, _ = StockBalance.objects.select_for_update().get_or_create(
                location=location,
                product=product,
                defaults={"on_hand_qty": 0, "reserved_qty": 0},
            )
            bal.on_hand_qty = int(bal.on_hand_qty) + qty
            bal.last_updated = timezone.now()
            bal.save(update_fields=["on_hand_qty", "last_updated"])

            StockLedger.objects.create(
                date_time=timezone.now(),
                product=product,
                location=location,
                movement_type="IN",
                qty=qty,
                unit_cost=Decimal(product.cost or 0),
                unit_selling_price=Decimal(product.selling_price or 0),
                reference_type="PO",
                reference_no=reference_no,
                customer_name="",
                notes=notes,
            )

        messages.success(request, f"Stock added ✅ {sku} +{qty}")
        return redirect("stock_in")

    return render(request, "stock_in.html", {"locations": locations})


# ---------------------------
# Invoice / Return / Reports (templates required)
# ---------------------------
def invoice_new(request):
    locations = StockLocation.objects.all().order_by("name")
    customers = Customer.objects.all().order_by("name")
    return render(request, "invoice_new.html", {"locations": locations, "customers": customers})


def return_new(request):
    locations = StockLocation.objects.all().order_by("name")
    customers = Customer.objects.all().order_by("name")
    return render(request, "return_new.html", {"locations": locations, "customers": customers})


def reports(request):
    return render(request, "reports.html")


# ---------------------------
# ✅ Custom Admin UI (your templates)
# ---------------------------
def admin_home(request):
    return render(request, "admin_home.html")


def admin_locations(request):
    locations = StockLocation.objects.all().order_by("name")
    return render(request, "admin_locations.html", {"locations": locations})


@require_http_methods(["GET", "POST"])
def admin_location_create(request):
    if request.method == "POST":
        form = StockLocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Location created ✅")
            return redirect("admin_locations")
    else:
        form = StockLocationForm()

    return render(request, "admin_location_create.html", {"form": form})


def admin_customers(request):
    customers = Customer.objects.all().order_by("name")
    return render(request, "admin_customers.html", {"customers": customers})


@require_http_methods(["GET", "POST"])
def admin_customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer created ✅")
            return redirect("admin_customers")
    else:
        form = CustomerForm()

    return render(request, "admin_customer_create.html", {"form": form})

from .models import Product, Customer, StockLocation

def dashboard(request):
    return render(request, "dashboard.html", {
        "products_count": Product.objects.count(),
        "customers_count": Customer.objects.count(),
        "locations_count": StockLocation.objects.count(),
    })
