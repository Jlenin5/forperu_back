from django.urls import re_path
from .views import SaleOrderAPIView

urlpatterns = [
  re_path(r'^sale-orders/?$', SaleOrderAPIView.as_view(), name='sale-orders'),
  re_path(r'^sale-orders/(?P<pk>\d+)/?$', SaleOrderAPIView.as_view(), name='sale-order-detail'),
]