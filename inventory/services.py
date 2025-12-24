# inventory/services.py
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional

from django.db import transaction
from django.utils import timezone


# -----------------------------
# Helpers
# -----------------------------
def _d(v) -> Decimal:
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal("0")


def _try_generate_barcode_png(barcode_value: str) -> Optional[bytes]:
    """
    Tries to generate barcode PNG bytes.
    Requires python-barcode + pillow:
        pip install python-barcode pillow
    If not installed, returns None (system still works without image).
    """
    try:
        import barcode  # type: ignore
        from barcode.writer import ImageWriter  # type: ignore
        from io import BytesIO

        code128 = barcode.get("code128", barcode_value, writer=ImageWriter())
        buff = BytesIO()
        code128.write(buff)
        return buff.getvalue()
    except Exception:
        return None


# -----------------------------
# Barcode Service (signals.py depends on this)
# -----------------------------
def ensure_product_barcode(product, force: bool = False) -> bool:
    """
    Generates barcode only when product is ACTIVE.
    Uses queryset.update() to avoid triggering post_save recursion again.
    Returns True if updated.
    """
    Product = product.__class__

    is_active = bool(getattr(product, "is_active", False))
    if not is_active:
        return False

    barcode_value = getattr(product, "barcode_value", None) or getattr(product, "barcode", None)

    # already has barcode
    if barcode_value and not force:
        return False

    # Prefer SKU as barcode
    sku = (getattr(product, "sku", "") or getattr(product, "SKU", "") or "").strip()
    new_barcode_value = sku or f"P{product.pk or ''}{timezone.now().strftime('%H%M%S')}"

    # optional image generation (not mandatory)
    _ = _try_generate_barcode_png(new_barcode_value)

    update_kwargs = {}
    if hasattr(product, "barcode_value"):
        update_kwargs["barcode_value"] = new_barcode_value
    elif hasattr(product, "barcode"):
        update_kwargs["barcode"] = new_barcode_value
    else:
        return False

    Product.objects.filter(pk=product.pk).update(**update_kwargs)
    return True


# -----------------------------
# Invoice / Return services (Industry Standard)
# -----------------------------
@dataclass
class LineItem:
    sku: str
    qty: int
    price: Decimal | None = None


def _balance_for_update(location, product):
    from .models import StockBalance  # local import

    bal, _ = StockBalance.objects.select_for_update().get_or_create(
        location=location,
        product=product,
        defaults={"on_hand_qty": 0, "reserved_qty": 0},
    )
    return bal


@transaction.atomic
def create_invoice_with_lines(*, location, customer=None, items: Iterable[LineItem], created_by=None):
    """
    - create invoice
    - create invoice lines
    - decrease stock (StockBalance)
    - add stock ledger OUT
    """
    from .models import Product, Invoice, InvoiceLine, StockLedger

    invoice = Invoice.objects.create(
        location=location,
        customer=customer,
        status="POSTED",
        created_by=created_by,
        created_at=timezone.now(),
    )

    total = Decimal("0")

    for it in items:
        product = Product.objects.select_for_update().get(sku=it.sku)
        qty = int(it.qty)

        unit_price = _d(it.price) if it.price is not None else _d(
            getattr(product, "selling_price", None) or getattr(product, "price", None) or 0
        )
        line_total = unit_price * qty

        # stock check + minus
        bal = _balance_for_update(location, product)
        if int(bal.on_hand_qty) < qty:
            raise ValueError(f"Insufficient stock for {product.sku}. On hand: {bal.on_hand_qty}")

        InvoiceLine.objects.create(
            invoice=invoice,
            product=product,
            qty=qty,
            unit_price=unit_price,
            line_total=line_total,
        )

        bal.on_hand_qty = int(bal.on_hand_qty) - qty
        bal.last_updated = timezone.now()
        bal.save(update_fields=["on_hand_qty", "last_updated"])

        StockLedger.objects.create(
            date_time=timezone.now(),
            product=product,
            location=location,
            movement_type="OUT",
            qty=qty,
            unit_cost=_d(getattr(product, "cost", None) or 0),
            unit_selling_price=unit_price,
            reference_type="INV",
            reference_no=getattr(invoice, "invoice_no", "") or str(invoice.pk),
            customer_name=(customer.name if customer else ""),
            notes="Sale",
        )

        total += line_total

    # invoice total
    if hasattr(invoice, "total_amount"):
        invoice.total_amount = total
        invoice.save(update_fields=["total_amount"])

    return invoice


@transaction.atomic
def create_return_with_lines(*, location, invoice=None, customer=None, items: Iterable[LineItem], created_by=None):
    """
    - create return doc
    - create return lines
    - increase stock (StockBalance)
    - add stock ledger RETURN
    """
    from .models import Product, Return, ReturnLine, StockLedger

    ret = Return.objects.create(
        location=location,
        invoice=invoice,
        customer=customer,
        status="POSTED",
        created_by=created_by,
        created_at=timezone.now(),
    )

    total = Decimal("0")

    for it in items:
        product = Product.objects.select_for_update().get(sku=it.sku)
        qty = int(it.qty)

        unit_price = _d(it.price) if it.price is not None else _d(
            getattr(product, "selling_price", None) or getattr(product, "price", None) or 0
        )
        line_total = unit_price * qty

        ReturnLine.objects.create(
            return_doc=ret,
            product=product,
            qty=qty,
            unit_price=unit_price,
            line_total=line_total,
        )

        bal = _balance_for_update(location, product)
        bal.on_hand_qty = int(bal.on_hand_qty) + qty
        bal.last_updated = timezone.now()
        bal.save(update_fields=["on_hand_qty", "last_updated"])

        StockLedger.objects.create(
            date_time=timezone.now(),
            product=product,
            location=location,
            movement_type="RETURN",
            qty=qty,
            unit_cost=_d(getattr(product, "cost", None) or 0),
            unit_selling_price=unit_price,
            reference_type="RET",
            reference_no=getattr(ret, "return_no", "") or str(ret.pk),
            customer_name=(customer.name if customer else ""),
            notes=f"Return against {getattr(invoice, 'invoice_no', '')}" if invoice else "Return",
        )

        total += line_total

    if hasattr(ret, "total_amount"):
        ret.total_amount = total
        ret.save(update_fields=["total_amount"])

    return ret
