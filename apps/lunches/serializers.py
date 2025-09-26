from rest_framework import serializers
from datetime import timedelta
from django.utils import timezone
from datetime import time
from decimal import Decimal
from apps.lateness.models import Lateness
from .models import Lunch
from apps.employees.serializers import EmployeeSerializer

def time_to_minutes(t: time) -> int:
  return t.hour * 60 + t.minute if t else 0

class LunchSerializer(serializers.ModelSerializer):
  employee = serializers.SerializerMethodField()
  employee_id = serializers.IntegerField()

  class Meta:
    model = Lunch
    fields = '__all__'
    read_only_fields = ('updated_at', 'created_at', 'deleted_at')

  def get_employee(self, obj):
    if obj.employee:
      EmployeeSerializer.Meta.model = obj.employee.__class__
      return EmployeeSerializer(obj.employee).data
    return None

  def create(self, validated_data):
    lunch = super().create(validated_data)

    if lunch.late_minutes:
      late_minutes_int = time_to_minutes(lunch.late_minutes)

      if late_minutes_int > 0:
        lives_used = self._calculate_lives_used(lunch.employee, late_minutes_int, lunch.date)
        discount = self._calculate_discount(lunch.employee, lives_used, late_minutes_int, lunch.date)

        # Crear registro de tardanza
        Lateness.objects.create(
          employee=lunch.employee,
          date=lunch.date,
          lateness_type="lunch_return",
          minutes_late=late_minutes_int,  # Guardamos como número de minutos en Lateness
          lives_used=lives_used,
          discount_amount=discount
        )

    return lunch

  def update(self, instance, validated_data):
    # Actualizar el almuerzo
    lunch = super().update(instance, validated_data)

    # Si hay cambios en los minutos de retraso, actualizar el registro de tardanza
    if 'late_minutes' in validated_data:
      self._update_lateness_record(lunch)
    
    return lunch

  def _create_lateness_record(self, lunch):
    lives_used = self._calculate_lives_used(lunch.employee, lunch.late_minutes, lunch.date)
    discount_amount = self._calculate_discount(lunch.employee, lives_used, lunch.late_minutes, lunch.date)

    Lateness.objects.create(
      employee=lunch.employee,
      date=lunch.date,
      lateness_type="lunch_return",
      minutes_late=lunch.late_minutes,
      lives_used=lives_used,
      discount_amount=discount_amount
    )

  def _update_lateness_record(self, lunch):
    try:
      lateness_record = Lateness.objects.get(
        employee=lunch.employee,
        date=lunch.date,
        lateness_type="lunch_return"
      )
      lives_used = self._calculate_lives_used(lunch.employee, lunch.late_minutes, lunch.date)
      discount_amount = self._calculate_discount(lunch.employee, lives_used, lunch.late_minutes, lunch.date)
      lateness_record.minutes_late = lunch.late_minutes
      lateness_record.lives_used = lives_used
      lateness_record.discount_amount = discount_amount
      lateness_record.save()
    except Lateness.DoesNotExist:
      if lunch.late_minutes > 0:
        self._create_lateness_record(lunch)

  def _calculate_lives_used(self, employee, late_minutes, attendance_date=None, exclude_id=None):
    if late_minutes <= 0:
      return 0

    today = attendance_date or timezone.now().date()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    monthly_lateness = Lateness.objects.filter(
      employee=employee,
      date__range=[first_day_of_month, last_day_of_month]
    )

    # Excluir el registro actual si existe (para no contarlo doble)
    if exclude_id:
      monthly_lateness = monthly_lateness.exclude(id=exclude_id)

    total_lives_used = sum(record.lives_used for record in monthly_lateness)

    lives_for_this = (late_minutes + 4) // 5
    lives_for_this = min(lives_for_this, 3)

    accumulated_lives = total_lives_used + lives_for_this
    if accumulated_lives > 3:
      accumulated_lives = 3

    return accumulated_lives

  def _calculate_discount(self, employee, lives_used, late_minutes, attendance_date=None, exclude_id=None):
    today = attendance_date or timezone.now().date()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    monthly_lateness = Lateness.objects.filter(
      employee=employee,
      date__range=[first_day_of_month, last_day_of_month]
    )
    if exclude_id:
      monthly_lateness = monthly_lateness.exclude(id=exclude_id)

    # --- 1. Solo contar vidas antes del día actual ---
    prev_month_lateness = monthly_lateness.filter(date__lt=today)
    prev_lives_used = sum(record.lives_used for record in prev_month_lateness)

    # --- 2. Calcular minutos protegidos disponibles hasta ese día ---
    protected_minutes = max(0, (3 - prev_lives_used) * 5)

    # --- 3. Exceso SOLO de este evento ---
    excess_minutes = max(0, late_minutes - protected_minutes)

    # --- 4. Aplicar escala SOLO a este evento ---
    if excess_minutes == 0:
      return Decimal('0.00')
    elif excess_minutes <= 5:
      return Decimal('5.00')
    elif excess_minutes <= 10:
      return Decimal('10.00')
    elif excess_minutes <= 20:
      return Decimal('15.00')
    else:
      return Decimal('30.00')