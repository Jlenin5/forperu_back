from rest_framework import serializers
from apps.currencies.serializers import CurrencySerializer
from apps.sale_orders.models import SaleOrder, SaleOrderDetail
from apps.warehouses.serializers import WarehouseSerializer
from apps.customers.serializers import CustomerSerializer
from apps.users.serializers import UserSerializer
from apps.products.serializers import ProductSerializer
from apps.quotes.serializers import QuoteSerializer

class SaleOrderDetailSerializer(serializers.ModelSerializer):
  product = serializers.SerializerMethodField()
  product_id = serializers.IntegerField(required=False, allow_null=True)

  class Meta:
    model = SaleOrderDetail
    fields = [
      'id',
      'sale_order_id',
      'product',
      'product_id',
      'product_name',
      'quantity',
      'price',
      'discount_method',
      'discount',
      'subtotal',
      'total'
    ]

    read_only_fields = ('updated_at', 'created_at', 'deleted_at')

  def get_product(self, obj):
    if obj.product:
      ProductSerializer.Meta.model = obj.product.__class__
      return ProductSerializer(obj.product).data
    return None

class SaleOrderSerializer(serializers.ModelSerializer):
  warehouse = serializers.SerializerMethodField()
  warehouse_id = serializers.IntegerField(required=True)
  customer = serializers.SerializerMethodField()
  customer_id = serializers.IntegerField(required=True)
  currency = serializers.SerializerMethodField()
  currency_id = serializers.IntegerField(required=True)
  user = serializers.SerializerMethodField()
  user_id = serializers.IntegerField(required=False, allow_null=True)
  quote = serializers.SerializerMethodField()
  quote_id = serializers.IntegerField(required=False, allow_null=True)

  sale_order_details = SaleOrderDetailSerializer(many=True)

  class Meta:
    model = SaleOrder
    fields = [
      'id',
      'reference',
      'warehouse',
      'warehouse_id',
      'customer',
      'customer_id',
      'currency',
      'currency_id',
      'user',
      'user_id',
      'issue_date',
      'exchange_rate',
      'discount',
      'subtotal',
      'total',
      'order_status',
      'date_approved',
      'migrate_sale_order',
      'quote',
      'quote_id',
      'sale_order_details'
    ]

    read_only_fields = ('reference', 'updated_at', 'created_at', 'deleted_at')

  def get_warehouse(self, obj):
    if obj.warehouse:
      WarehouseSerializer.Meta.model = obj.warehouse.__class__
      return WarehouseSerializer(obj.warehouse).data
    return None

  def get_customer(self, obj):
    if obj.customer:
      CustomerSerializer.Meta.model = obj.customer.__class__
      return CustomerSerializer(obj.customer).data
    return None
  
  def get_currency(self, obj):
    if obj.currency:
      CurrencySerializer.Meta.model = obj.currency.__class__
      return CurrencySerializer(obj.currency).data
    return None
  
  def get_user(self, obj):
    if obj.user:
      UserSerializer.Meta.model = obj.user.__class__
      return UserSerializer(obj.user).data
    return None
  
  def get_quote(self, obj):
    if obj.quote:
      QuoteSerializer.Meta.model = obj.quote.__class__
      return QuoteSerializer(obj.quote).data
    return None
  
  def create(self, validated_data):
    details_data = validated_data.pop("sale_order_details", [])
    sale_order = SaleOrder.objects.create(**validated_data)
    for detail_data in details_data:
      SaleOrderDetail.objects.create(sale_order=sale_order, **detail_data)
    return sale_order

  def update(self, instance, validated_data):
    details_data = validated_data.pop("sale_order_details", [])
    for attr, value in validated_data.items():
      setattr(instance, attr, value)
    instance.save()

    # actualizar detalles (simplificado: borra y vuelve a crear)
    instance.sale_order_details.all().delete()
    for detail_data in details_data:
      SaleOrderDetail.objects.create(sale_order=instance, **detail_data)
    return instance