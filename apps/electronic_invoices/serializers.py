from rest_framework import serializers
from apps.electronic_invoices.models import ElectronicInvoice
from apps.sales.serializers import SaleSerializer
from apps.electronic_invoicing_providers.serializers import ElectronicInvoicingProviderSerializer

class ElectronicInvoiceSerializer(serializers.ModelSerializer):
  sale = serializers.SerializerMethodField()
  sale_id = serializers.IntegerField(required=True)
  provider = serializers.SerializerMethodField()
  provider_id = serializers.IntegerField(required=True)

  class Meta:
    model = ElectronicInvoice
    fields = [
      'id',
      'sale',
      'sale_id',
      'provider',
      'provider_id',
      'document_type',
      'series',
      'number',
      'external_id',
      'status',
      'response_message',
      'pdf_url',
      'cdr_url',
      'xml_url',
      'sent_at',
      'created_at',
      'updated_at'
    ]
    read_only_fields = ['created_at', 'updated_at']

  def get_sale(self, obj):
    if obj.sale:
      SaleSerializer.Meta.model = obj.sale.__class__
      return SaleSerializer(obj.sale).data
    return None

  def get_provider(self, obj):
    if obj.provider:
      ElectronicInvoicingProviderSerializer.Meta.model = obj.provider.__class__
      return ElectronicInvoicingProviderSerializer(obj.provider).data
    return None