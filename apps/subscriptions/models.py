from django.db import models
from apps.companies.models import Company
from apps.plans.models import Plan

class Subscription(models.Model):
  STATUS_CHOICES = [
    ("active", "Activa"),
    ("expired", "Expirada"),
    ("canceled", "Cancelada"),
  ]

  company = models.ForeignKey(
    Company,
    on_delete=models.CASCADE,
    db_column="company_id",
    related_name="subscriptions"
  )
  plan = models.ForeignKey(
    Plan,
    on_delete=models.CASCADE,
    db_column="plan_id",
    related_name="subscriptions"
  )
  start_date = models.DateTimeField(auto_now_add=True)
  end_date = models.DateTimeField()
  status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(null=True, blank=True)
  deleted_at = models.DateTimeField(null=True, blank=True)

  class Meta:
    db_table = "subscriptions"

  def __str__(self):
    return f"{self.company.name} - {self.plan.title} ({self.status})"