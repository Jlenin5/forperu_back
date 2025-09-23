from django.db import models
from apps.systems.models import System

class ElectronicInvoicingProvider(models.Model):
  system = models.ForeignKey(
    System,
    on_delete=models.CASCADE,
    db_column="system_id",
    related_name="electronic_invoicing_providers"
  )
  name = models.CharField(max_length=100)
  description = models.TextField(null=True, blank=True)
  api_url = models.TextField()
  api_token = models.TextField(null=True, blank=True)
  status = models.BooleanField(default=1)

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(null=True, blank=True)
  deleted_at = models.DateTimeField(null=True, blank=True)

  class Meta:
    db_table = "electronic_invoicing_providers"
    ordering = ["name"]

  def __str__(self):
    return f"{self.name} ({self.system.name})"