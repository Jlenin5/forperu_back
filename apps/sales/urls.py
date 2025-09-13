from django.urls import re_path

from apps.electronic_invoices.views import ElectronicInvoiceAPIView
from .views import SaleAPIView, SalePDFTicketView, SalePDFA4View

urlpatterns = [
  re_path(r'^sales/?$', SaleAPIView.as_view(), name='sales'),
  re_path(r'^sales/(?P<pk>\d+)/?$', SaleAPIView.as_view(), name='sale-detail'),
  re_path(r"^sales/pdf/document-(?P<bill>[\w-]+)/?$", SalePDFTicketView.as_view(), name="sale-pdf-ticket"),
  re_path(r"^sales/pdfA4/document-(?P<bill>[\w-]+)/?$", SalePDFA4View.as_view(), name="sale-pdf-a4"),
  re_path(r'^sales/(?P<sale_id>\d+)/electronic-invoice/?$', ElectronicInvoiceAPIView.as_view(), name='sale-electronic-invoice'),
]