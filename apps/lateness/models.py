from django.db import models
from apps.employees.models import Employee


class Lateness(models.Model):
  TYPE_CHOICES = [
    ("work_start", "Work Start"),
    ("lunch_return", "Lunch Return"),
  ]

  employee = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column="employee_id")
  date = models.DateField()
  lateness_type = models.CharField(max_length=20, choices=TYPE_CHOICES)  # entrada o regreso de almuerzo
  minutes_late = models.PositiveIntegerField(default=0)  # minutos tarde
  lives_used = models.PositiveSmallIntegerField(default=0)  # cuántas vidas se gastaron (cada 5 minutos = 1 vida)
  discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # descuento generado ese día
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    managed = True
    db_table = "lateness"
    ordering = ["-date"]

class EmployeeLatenessSummary(models.Model):
  employee = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column="employee_id")
  month = models.PositiveSmallIntegerField()  # 1–12
  year = models.PositiveSmallIntegerField()
  total_lives = models.PositiveSmallIntegerField(default=3)  # siempre 3 vidas por mes
  lives_remaining = models.PositiveSmallIntegerField(default=3)
  total_minutes_late = models.PositiveIntegerField(default=0)
  total_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

  class Meta:
    managed = True
    db_table = "employee_lateness_summaries"
    unique_together = ("employee", "month", "year")