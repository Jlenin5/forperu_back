from django.urls import re_path
from .views import SubscriptionAPIView

urlpatterns = [
  re_path(r'^subscriptions/?$', SubscriptionAPIView.as_view(), name='subscriptions'),
  re_path(r'^subscriptions/(?P<pk>\d+)/?$', SubscriptionAPIView.as_view(), name='subscription-detail'),
]