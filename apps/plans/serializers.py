from rest_framework import serializers
from apps.plans.models import Plan

class PlanSerializer(serializers.ModelSerializer):
  class Meta:
    model = Plan
    fields = [
      'id',
      'title',
      'subtitle',
      'price',
      'max_branch_offices',
      'max_warehouses',
      'max_purchases',
      'max_users',
      'max_products',
      'max_services',
      'max_documents',
      'status',
      'created_at',
      'updated_at',
      'deleted_at'
    ]
    read_only_fields = ['created_at', 'updated_at', 'deleted_at']