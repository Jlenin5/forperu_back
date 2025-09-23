from django.urls import re_path
from .views import PlanAPIView

urlpatterns = [
  re_path(r'^plans/?$', PlanAPIView.as_view(), name='plans'),
  re_path(r'^plans/(?P<pk>\d+)/?$', PlanAPIView.as_view(), name='plan-detail'),
]