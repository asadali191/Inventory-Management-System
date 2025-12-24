# inventory/api_views.py
from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.db.models import Sum

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import (
    Product,
    Invoice,
    InvoiceLine,
    ReturnLine,
    StockLocation,
    Customer,
)
from .services import (
    LineItem,
    create_invoice_with_lines,
    create_return_with_lines,
)


# -------------------------------------------------
# Scan Product (SKU / Barcode)
# -------------------------------------------------
class ScanProduct(APIView):
    """
    GET /api/scan/?code=SLG42
    GET /api/scan/?code=BARCODE123
    """

    def get(self, request):
        code = (request.query_params.get("code") or "").strip()
        if not code:
            return Response({"detail": "Provide code."}, status=400)

        product = (
            Product.objects.filter(sku=code).first()
            or Product.objects.filter(barcode_value=code).first()
            or Product.objects.filter(barcode=code).first()
        )

        if not product:
            return Response({"detail": "Product not found."}, status=404)

        return Response({
            "sku": product.sku,
            "name": product.product_name,
            "price": str(
                getattr(product, "selling_price", None)
                or getattr(product, "price", None)
                or "0"
            ),
            "active": bool(getattr(product, "is_active", False)),
        })


# -------------------------------------------------
# Create Invoice (POS)
# -------------------------------------------------
class CreateInvoice(APIView):
    """
    POST:
    {
      "location_id": 1,
      "customer_id": 2,   # optional
      "items": [
        {"sku": "SLG42", "qty": 2, "price": "2500"}
      ]
    }
    """

    def post(self, request):
        location = get_object_or_404(
            StockLocation, pk=request.data.get("location_id")
        )

        customer_id = request.data.get("customer_id")
        customer = (
            get_object_or_404(Customer, pk=customer_id)
            if customer_id else None
        )

        items_in = request.data.get("items") or []
        if not items_in:
            return Response({"detail": "No items provided."}, status=400)

        items: list[LineItem] = []
        for i in items_in:
            try:
                sku = i["sku"]
                qty = int(i["qty"])
                price = i.get("price")
            except Exception:
                return Response({"detail": "Invalid item payload."}, status=400)

            if not sku or qty <= 0:
                return Response(
                    {"detail": "Each item requires sku and qty >= 1."},
                    status=400,
                )

            items.append(LineItem(sku=sku, qty=qty, price=price))

        try:
            invoice = create_invoice_with_lines(
                location=location,
                customer=customer,
                items=items,
                created_by=request.user if request.user.is_authenticated else None,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        return Response(
            {
                "invoice_id": invoice.id,
                "invoice_no": getattr(invoice, "invoice_no", None),
            },
            status=status.HTTP_201_CREATED,
        )


# -------------------------------------------------
# Invoice Detail (Return UI helper)
# -------------------------------------------------
class InvoiceDetail(APIView):
    """
    GET /api/invoices/detail/?invoice_no=INV-00012
    """

    def get(self, request):
        invoice_no = (request.query_params.get("invoice_no") or "").strip()
        if not invoice_no:
            return Response({"detail": "Provide invoice_no."}, status=400)

        invoice = get_object_or_404(Invoice, invoice_no=invoice_no)

        # Sold quantities per SKU
        sold_rows = (
            InvoiceLine.objects
            .filter(invoice=invoice)
            .values("product__sku", "product__product_name", "unit_price")
            .annotate(sold_qty=Sum("qty"))
        )

        # Already returned quantities per SKU
        ret_rows = (
            ReturnLine.objects
            .filter(return_doc__invoice=invoice)
            .values("product__sku")
            .annotate(ret_qty=Sum("qty"))
        )
        ret_map = {r["product__sku"]: int(r["ret_qty"] or 0) for r in ret_rows}

        lines = []
        for r in sold_rows:
            sku = r["product__sku"]
            sold_qty = int(r["sold_qty"] or 0)
            already_ret = ret_map.get(sku, 0)
            remaining = max(sold_qty - already_ret, 0)

            lines.append({
                "sku": sku,
                "name": r["product__product_name"],
                "sold_qty": sold_qty,
                "already_returned": already_ret,
                "remaining_allowed": remaining,
                "unit_price": str(r["unit_price"]),
            })

        return Response({
            "id": invoice.id,
            "invoice_no": invoice.invoice_no,
            "total": str(getattr(invoice, "total_amount", "0")),
            "lines": lines,
        })


# -------------------------------------------------
# Create Return (WITH VALIDATION)
# -------------------------------------------------
class CreateReturn(APIView):
    """
    POST:
    {
      "location_id": 1,
      "invoice_id": 10,
      "items": [
        {"sku": "SLG42", "qty": 1, "price": "2500"}
      ]
    }
    """

    def post(self, request):
        location = get_object_or_404(
            StockLocation, pk=request.data.get("location_id")
        )
        invoice = get_object_or_404(
            Invoice, pk=request.data.get("invoice_id")
        )
        customer = invoice.customer

        items_in = request.data.get("items") or []
        if not items_in:
            return Response({"detail": "No items provided."}, status=400)

        # ---- requested return qty map ----
        req_map: dict[str, int] = {}
        for i in items_in:
            sku = (i.get("sku") or "").strip()
            try:
                qty = int(i.get("qty") or 0)
            except Exception:
                qty = 0

            if not sku or qty <= 0:
                return Response(
                    {"detail": "Each item requires sku and qty >= 1."},
                    status=400,
                )

            req_map[sku] = req_map.get(sku, 0) + qty

        # ---- sold qty per SKU ----
        sold_rows = (
            InvoiceLine.objects
            .filter(invoice=invoice)
            .values("product__sku")
            .annotate(sold_qty=Sum("qty"))
        )
        sold_map = {
            r["product__sku"]: int(r["sold_qty"] or 0)
            for r in sold_rows
        }

        # ---- already returned qty per SKU ----
        ret_rows = (
            ReturnLine.objects
            .filter(return_doc__invoice=invoice)
            .values("product__sku")
            .annotate(ret_qty=Sum("qty"))
        )
        ret_map = {
            r["product__sku"]: int(r["ret_qty"] or 0)
            for r in ret_rows
        }

        errors = []
        for sku, want_qty in req_map.items():
            sold_qty = sold_map.get(sku, 0)
            already_ret = ret_map.get(sku, 0)
            remaining = sold_qty - already_ret

            if sold_qty <= 0:
                errors.append({
                    "sku": sku,
                    "error": "This item was not sold on this invoice.",
                })
            elif want_qty > remaining:
                errors.append({
                    "sku": sku,
                    "error": "Return qty exceeds allowed.",
                    "sold": sold_qty,
                    "already_returned": already_ret,
                    "remaining_allowed": max(remaining, 0),
                    "requested": want_qty,
                })

        if errors:
            return Response(
                {
                    "detail": "Return validation failed.",
                    "items": errors,
                },
                status=400,
            )

        # ---- build LineItems ----
        items = [
            LineItem(
                sku=i["sku"],
                qty=int(i["qty"]),
                price=i.get("price"),
            )
            for i in items_in
        ]

        ret = create_return_with_lines(
            location=location,
            invoice=invoice,
            customer=customer,
            items=items,
            created_by=request.user if request.user.is_authenticated else None,
        )

        return Response(
            {
                "return_id": ret.id,
                "return_no": getattr(ret, "return_no", None),
            },
            status=status.HTTP_201_CREATED,
        )
