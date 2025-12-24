# inventory/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Product
from .services import ensure_product_barcode


@receiver(post_save, sender=Product)
def product_post_save(sender, instance: Product, created, **kwargs):
    # only when active
    if not getattr(instance, "is_active", False):
        return

    # only when barcode missing
    barcode_value = getattr(instance, "barcode_value", None) or getattr(instance, "barcode", None)
    if barcode_value:
        return

    ensure_product_barcode(instance)
