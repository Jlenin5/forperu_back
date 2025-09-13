from rest_framework import serializers
from apps.electronic_invoicing_providers.models import ElectronicInvoicingProvider
from apps.systems.serializers import SystemSerializer

class ElectronicInvoicingProviderSerializer(serializers.ModelSerializer):
  system = serializers.SerializerMethodField()
  system_id = serializers.IntegerField(required=True)

  class Meta:
    model = ElectronicInvoicingProvider
    fields = [
      'id',
      'system',
      'system_id',
      'name',
      'description',
      'api_url',
      'api_token',
      'status'
    ]
    
    read_only_fields = ('updated_at', 'created_at', 'deleted_at')

  def get_system(self, obj):
    if obj.system:
      SystemSerializer.Meta.model = obj.system.__class__
      return SystemSerializer(obj.system).data
    return None
