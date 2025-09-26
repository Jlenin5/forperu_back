from django.urls import re_path
from .views import (
  LatenessListCreateView,
  LatenessDetailView,
  EmployeeLatenessSummaryListView,
  EmployeeLatenessSummaryDetailView,
)

urlpatterns = [
  # ----- Lateness -----
  re_path(r'^lateness/?$', LatenessListCreateView.as_view(), name="lateness-list-create"),
  re_path(r'^lateness/(?P<pk>\d+)/$', LatenessDetailView.as_view(), name="lateness-detail"),

  # ----- Summaries -----
  re_path(r'^lateness-summaries/?$', EmployeeLatenessSummaryListView.as_view(), name="lateness-summary-list"),
  re_path(r'^lateness-summaries/(?P<pk>\d+)/$', EmployeeLatenessSummaryDetailView.as_view(), name="lateness-summary-detail"),
]