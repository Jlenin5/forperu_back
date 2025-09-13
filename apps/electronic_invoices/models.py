from django.db import models
from apps.electronic_invoicing_providers.models import ElectronicInvoicingProvider
from apps.sales.models import Sale

class ElectronicInvoice(models.Model):
  STATUS_CHOICES = [
    ("pending", "Pendiente"),
    ("sent", "Enviado"),
    ("accepted", "Aceptado"),
    ("rejected", "Rechazado"),
    ("canceled", "Anulado"),
  ]
  sale = models.ForeignKey(
    Sale,
    on_delete=models.CASCADE,
    db_column="sale_id",
    related_name="electronic_invoices"
  )
  provider = models.ForeignKey(
    ElectronicInvoicingProvider,
    on_delete=models.CASCADE,
    db_column="provider_id",
    related_name="electronic_invoices"
  )
  document_type = models.CharField(max_length=10)  # invoice, ticket, credit_note
  series = models.CharField(max_length=4)
  number = models.IntegerField()
  external_id = models.CharField(max_length=100, null=True, blank=True)
  status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
  response_message = models.TextField(null=True, blank=True)
  pdf_url = models.TextField(null=True, blank=True)
  cdr_url = models.TextField(null=True, blank=True)
  xml_url = models.TextField(null=True, blank=True)
  sent_at = models.DateTimeField(null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(null=True, blank=True)

  class Meta:
    db_table = "electronic_invoices"
    ordering = ["-created_at"]

  def __str__(self):
    return f"{self.document_type.upper()} {self.series}-{str(self.number).zfill(6)} ({self.get_status_display()})"