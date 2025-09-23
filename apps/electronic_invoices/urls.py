from django.urls import re_path
from .views import ElectronicInvoiceAPIView

urlpatterns = [
  re_path(r'^electronic-invoices/?$', ElectronicInvoiceAPIView.as_view(), name='electronic-invoices'),
  re_path(r'^electronic-invoices/(?P<pk>\d+)/?$', ElectronicInvoiceAPIView.as_view(), name='electronic-invoice-detail'),
]