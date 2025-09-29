from django.urls import re_path
from .views import BannerAPIView

urlpatterns = [
  re_path(r'^banners/?$', BannerAPIView.as_view(), name='banners'),
]