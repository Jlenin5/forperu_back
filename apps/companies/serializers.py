from rest_framework import serializers
from apps.companies.models import Company
from apps.electronic_invoicing_providers.serializers import ElectronicInvoicingProviderSerializer

class CompanySerializer(serializers.ModelSerializer):
  status = serializers.IntegerField()
  electronic_invoicing_provider = serializers.SerializerMethodField()
  electronic_invoicing_provider_id = serializers.IntegerField(required=False, allow_null=True)
  
  class Meta:
    model = Company
    fields = [
      'id',
      'name',
      'logo',
      'ruc',
      'email',
      'phone',
      'web_site',
      'address',
      'status',
      'electronic_invoicing_provider',
      'electronic_invoicing_provider_id',
      'created_by',
      'updated_by'
    ]

    read_only_fields = ('updated_at', 'created_at', 'deleted_at')

  def get_electronic_invoicing_provider(self, obj):
    if obj.electronic_invoicing_provider:
      ElectronicInvoicingProviderSerializer.Meta.model = obj.electronic_invoicing_provider.__class__
      return ElectronicInvoicingProviderSerializer(obj.electronic_invoicing_provider).data
    return None