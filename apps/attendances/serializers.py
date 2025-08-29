from datetime import timedelta
from django.utils import timezone
from decimal import Decimal
from rest_framework import serializers
from .models import Attendance
from apps.employees.serializers import EmployeeSerializer
from apps.lateness.models import Lateness

class AttendanceSerializer(serializers.ModelSerializer):
  employee = serializers.SerializerMethodField()
  employee_id = serializers.IntegerField()
  
  class Meta:
    model = Attendance
    fields = '__all__'
    read_only_fields = ('updated_at', 'created_at', 'deleted_at')
  
  def get_employee(self, obj):
    if obj.employee:
      EmployeeSerializer.Meta.model = obj.employee.__class__
      return EmployeeSerializer(obj.employee).data
    return None
  
  def create(self, validated_data):
    # Crear la asistencia primero
    attendance = super().create(validated_data)
    
    # Crear registro de tardanza si hay minutos de retraso
    if attendance.late_minutes and attendance.late_minutes > 0:
      self._create_lateness_record(attendance)
    
    return attendance
  
  def update(self, instance, validated_data):
    # Actualizar la asistencia
    attendance = super().update(instance, validated_data)
    
    # Si hay cambios en los minutos de retraso, actualizar el registro de tardanza
    if 'late_minutes' in validated_data:
      self._update_lateness_record(attendance)
    
    return attendance
  
  def _create_lateness_record(self, attendance):
    lives_used = self._calculate_lives_used(attendance.employee, attendance.late_minutes, attendance.date)
    discount_amount = self._calculate_discount(attendance.employee, lives_used, attendance.late_minutes, attendance.date)

    Lateness.objects.create(
      employee=attendance.employee,
      date=attendance.date,
      lateness_type="work_start",
      minutes_late=attendance.late_minutes,
      lives_used=lives_used,
      discount_amount=discount_amount
    )
  
  def _update_lateness_record(self, attendance):
    try:
      lateness_record = Lateness.objects.get(
        employee=attendance.employee,
        date=attendance.date,
        lateness_type="work_start"
      )
      # ¡IMPORTANTE! pasar attendance.date
      lives_used = self._calculate_lives_used(attendance.employee, attendance.late_minutes, attendance.date)
      discount_amount = self._calculate_discount(attendance.employee, lives_used, attendance.late_minutes, attendance.date)
      lateness_record.minutes_late = attendance.late_minutes
      lateness_record.lives_used = lives_used
      lateness_record.discount_amount = discount_amount
      lateness_record.save()
    except Lateness.DoesNotExist:
      if attendance.late_minutes > 0:
        self._create_lateness_record(attendance)
  
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