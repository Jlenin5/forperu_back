from rest_framework import serializers
from apps.subscriptions.models import Subscription
from apps.plans.serializers import PlanSerializer
from apps.companies.serializers import CompanySerializer

class SubscriptionSerializer(serializers.ModelSerializer):
  company = serializers.SerializerMethodField()
  company_id = serializers.IntegerField(required=True)
  plan = serializers.SerializerMethodField()
  plan_id = serializers.IntegerField(required=True)

  class Meta:
    model = Subscription
    fields = [
      'id',
      'company',
      'company_id',
      'plan',
      'plan_id',
      'start_date',
      'end_date',
      'status',
      'created_at',
      'updated_at',
      'deleted_at'
    ]
    read_only_fields = ['created_at', 'updated_at', 'deleted_at']

  def get_company(self, obj):
    if obj.company:
      CompanySerializer.Meta.model = obj.company.__class__
      return CompanySerializer(obj.company).data
    return None

  def get_plan(self, obj):
    if obj.plan:
      PlanSerializer.Meta.model = obj.plan.__class__
      return PlanSerializer(obj.plan).data
    return None