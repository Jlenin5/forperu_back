from django.urls import re_path
from .views import ElectronicInvoicingProviderAPIView

urlpatterns = [
  re_path(r'^electronic-invoicing-providers/?$', ElectronicInvoicingProviderAPIView.as_view(), name='electronic-invoicing-providers'),
  re_path(r'^electronic-invoicing-providers/(?P<pk>\d+)/?$', ElectronicInvoicingProviderAPIView.as_view(), name='electronic-invoicing-provider-detail'),
]