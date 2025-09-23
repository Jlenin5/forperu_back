from django.urls import re_path
from .views import PurchaseRequestAPIView

urlpatterns = [
  re_path(r'^purchase-requests/?$', PurchaseRequestAPIView.as_view(), name='purchase-requests'),
  re_path(r'^purchase-requests/(?P<pk>\d+)/?$', PurchaseRequestAPIView.as_view(), name='purchase-request-detail'),
]