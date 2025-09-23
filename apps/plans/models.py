from django.db import models

class Plan(models.Model):
  title = models.CharField(max_length=100)
  subtitle = models.CharField(max_length=200, null=True, blank=True)
  price = models.DecimalField(max_digits=14, decimal_places=2)
  max_branch_offices = models.PositiveSmallIntegerField(default=0)
  max_warehouses = models.PositiveSmallIntegerField(default=0)
  max_purchases = models.PositiveSmallIntegerField(default=0)
  max_users = models.PositiveSmallIntegerField(default=0)
  max_products = models.PositiveSmallIntegerField(default=0)
  max_services = models.PositiveSmallIntegerField(default=0)
  max_documents = models.PositiveIntegerField(default=0)
  status = models.BooleanField(default=True)

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(null=True, blank=True)
  deleted_at = models.DateTimeField(null=True, blank=True)

  class Meta:
    db_table = "plans"

  def __str__(self):
    return f"{self.title} ({self.price})"