from django.urls import path
from .api_views import (
    ScanProduct, CreateInvoice,
    InvoiceDetail, CreateReturn
)

urlpatterns = [
    path("scan/", ScanProduct.as_view()),
    path("invoices/create/", CreateInvoice.as_view()),
    path("invoices/detail/", InvoiceDetail.as_view()),
    path("returns/create/", CreateReturn.as_view()),
]
