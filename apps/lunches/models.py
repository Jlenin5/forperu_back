from django.db import models
from apps.employees.models import Employee

# Create your models here.
class Lunch(models.Model):
  employee = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column='employee_id')
  date = models.DateField()
  start = models.TimeField(null=True, blank=True)
  back_to = models.TimeField(null=True, blank=True)
  calculated_time = models.TimeField(null=True, blank=True)
  late_minutes = models.TimeField(null=True, blank=True)
  observation = models.TextField(null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(null=True, blank=True)
  deleted_at = models.DateTimeField(null=True, blank=True)

  class Meta:
    managed = True
    db_table = 'lunches'