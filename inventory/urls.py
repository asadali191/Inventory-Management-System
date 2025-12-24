# inventory/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Main
    path("", views.dashboard, name="dashboard"),

    # Products
    path("products/", views.products_list, name="products_list"),
    path("products/new/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/activate/", views.product_activate, name="product_activate"),
    path("products/<int:pk>/barcode/", views.product_barcode_print, name="product_barcode_print"),

    # Stock / Sales / Returns / Reports
    path("stock/in/", views.stock_in, name="stock_in"),
    path("invoice/new/", views.invoice_new, name="invoice_new"),
    path("return/new/", views.return_new, name="return_new"),
    path("reports/", views.reports, name="reports"),

    # ✅ Custom Admin UI
    path("admin-ui/", views.admin_home, name="admin_home"),
    path("admin-ui/locations/", views.admin_locations, name="admin_locations"),
    path("admin-ui/locations/new/", views.admin_location_create, name="admin_location_create"),
    path("admin-ui/customers/", views.admin_customers, name="admin_customers"),
    path("admin-ui/customers/new/", views.admin_customer_create, name="admin_customer_create"),
]
