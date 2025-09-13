from rest_framework import serializers
from apps.purchase_requests.models import PurchaseRequest, PurchaseRequestDetail
from apps.suppliers.serializers import SupplierSerializer
from apps.users.serializers import UserSerializer
from apps.products.serializers import ProductSerializer

class PurchaseRequestDetailSerializer(serializers.ModelSerializer):
  product = serializers.SerializerMethodField()
  product_id = serializers.IntegerField(required=True)

  class Meta:
    model = PurchaseRequestDetail
    fields = [
      'id',
      'purchase_request_id',
      'product',
      'product_id',
      'quantity',
      'unit_price',
      'estimated_cost',
      'subtotal',
      'received_quantity',
      'status',
      'comments'
    ]

    read_only_fields = ('estimated_cost', 'subtotal', 'updated_at', 'created_at', 'deleted_at')

  def get_product(self, obj):
    if obj.product:
      ProductSerializer.Meta.model = obj.product.__class__
      return ProductSerializer(obj.product).data
    return None

class PurchaseRequestSerializer(serializers.ModelSerializer):
  supplier = serializers.SerializerMethodField()
  supplier_id = serializers.IntegerField(required=True)
  user = serializers.SerializerMethodField()
  user_id = serializers.IntegerField(required=False, allow_null=True)
  approved_by_user = serializers.SerializerMethodField()

  purchase_request_details = PurchaseRequestDetailSerializer(many=True)

  class Meta:
    model = PurchaseRequest
    fields = [
      'id',
      'reference',
      'supplier',
      'supplier_id',
      'user',
      'user_id',
      'request_date',
      'expected_delivery_date',
      'status',
      'priority',
      'total_cost',
      'approved_by',
      'approved_by_user',
      'approval_date',
      'notes',
      'purchase_request_details'
    ]

    read_only_fields = ('reference', 'total_cost', 'approval_date', 'updated_at', 'created_at', 'deleted_at')

  def get_supplier(self, obj):
    if obj.supplier:
      SupplierSerializer.Meta.model = obj.supplier.__class__
      return SupplierSerializer(obj.supplier).data
    return None

  def get_user(self, obj):
    if obj.user:
      UserSerializer.Meta.model = obj.user.__class__
      return UserSerializer(obj.user).data
    return None
  
  def get_approved_by_user(self, obj):
    if obj.approved_by:
      UserSerializer.Meta.model = obj.approved_by.__class__
      return UserSerializer(obj.approved_by).data
    return None
  
  def create(self, validated_data):
    details_data = validated_data.pop("purchase_request_details", [])
    purchase_request = PurchaseRequest.objects.create(**validated_data)
    
    total_cost = 0
    for detail_data in details_data:
      detail = PurchaseRequestDetail.objects.create(purchase_request=purchase_request, **detail_data)
      if detail.estimated_cost:
        total_cost += detail.estimated_cost
    
    # Actualizar el costo total
    purchase_request.total_cost = total_cost
    purchase_request.save()
    
    return purchase_request

  def update(self, instance, validated_data):
    details_data = validated_data.pop("purchase_request_details", [])
    
    for attr, value in validated_data.items():
      setattr(instance, attr, value)
    instance.save()

    # actualizar detalles y recalcular total
    instance.purchase_request_details.all().delete()
    total_cost = 0
    
    for detail_data in details_data:
      detail = PurchaseRequestDetail.objects.create(purchase_request=instance, **detail_data)
      if detail.estimated_cost:
        total_cost += detail.estimated_cost
    
    # Actualizar el costo total
    instance.total_cost = total_cost
    instance.save()
    
    return instance