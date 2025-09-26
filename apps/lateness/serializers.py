from rest_framework import serializers
from .models import Lateness, EmployeeLatenessSummary
from datetime import date
from math import ceil

class LatenessSerializer(serializers.ModelSerializer):
  # Mostrar datos del empleado en cada registro de tardanza
  employee = serializers.SerializerMethodField()

  class Meta:
    model = Lateness
    fields = "__all__"

  def get_employee(self, obj):
    # Usamos el serializer de empleados pero solo mostramos campos básicos
    return {
      "id": obj.employee.id,
      "names": obj.employee.names,
      "surname": obj.employee.surname,
      "second_surname": obj.employee.second_surname,
      "document_number": obj.employee.document_number,
    }

  def create(self, validated_data):
    employee = validated_data["employee"]
    minutes_late = validated_data.get("minutes_late", 0)

    # 1 vida por cada 5 min
    lives_used = ceil(minutes_late / 5) if minutes_late > 0 else 0
    validated_data["lives_used"] = lives_used

    # Obtener o crear el resumen mensual
    lateness_date = validated_data.get("date", date.today())
    summary, created = EmployeeLatenessSummary.objects.get_or_create(
      employee=employee,
      month=lateness_date.month,
      year=lateness_date.year,
      defaults={
        "total_lives": 3,
        "lives_remaining": 3,
        "total_minutes_late": 0,
        "total_discount": 0,
      },
    )

    # Actualizar vidas y descuento
    discount_amount = 0
    if summary.lives_remaining > 0:
      if lives_used <= summary.lives_remaining:
        summary.lives_remaining -= lives_used
      else:
        # Se pasan de las vidas restantes
        over = lives_used - summary.lives_remaining
        summary.lives_remaining = 0
        discount_amount = over * 5.00
    else:
      discount_amount = lives_used * 5.00

    summary.total_minutes_late += minutes_late
    summary.total_discount += discount_amount
    summary.save()

    validated_data["discount_amount"] = discount_amount

    return super().create(validated_data)

class EmployeeLatenessSummarySerializer(serializers.ModelSerializer):
  employee = serializers.SerializerMethodField()

  class Meta:
    model = EmployeeLatenessSummary
    fields = "__all__"

  def get_employee(self, obj):
    # Devolvemos información básica del empleado
    return {
      "id": obj.employee.id,
      "names": obj.employee.names,
      "surname": obj.employee.surname,
      "second_surname": obj.employee.second_surname,
      "document_number": obj.employee.document_number,
    }