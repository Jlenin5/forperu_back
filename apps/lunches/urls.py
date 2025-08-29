from django.urls import re_path
from .views import LunchAPIView

urlpatterns = [
  re_path(r'^lunches/?$', LunchAPIView.as_view(), name='lunches'),
  re_path(r'^lunches/(?P<pk>\d+)/?$', LunchAPIView.as_view(), name='lunch-detail'),
]