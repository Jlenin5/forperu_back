from rest_framework import serializers
from apps.currencies.serializers import CurrencySerializer
from apps.sales.models import Sale, SaleDetail
from apps.companies.serializers import CompanySerializer
from apps.branch_offices.serializers import BranchOfficeSerializer
from apps.warehouses.serializers import WarehouseSerializer
from apps.customers.serializers import CustomerSerializer
from apps.users.serializers import UserSerializer
from apps.products.serializers import ProductSerializer
from apps.payment_methods.serializers import PaymentMethodSerializer
from apps.sale_orders.serializers import SaleOrderSerializer

class SaleDetailSerializer(serializers.ModelSerializer):
  product = serializers.SerializerMethodField()
  product_id = serializers.IntegerField(required=True)

  class Meta:
    model = SaleDetail
    fields = [
      'id',
      'sale_id',
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

class SaleSerializer(serializers.ModelSerializer):
  company = serializers.SerializerMethodField()
  company_id = serializers.IntegerField(required=False, allow_null=True)
  branch_office = serializers.SerializerMethodField()
  branch_office_id = serializers.IntegerField(required=False, allow_null=True)
  warehouse = serializers.SerializerMethodField()
  warehouse_id = serializers.IntegerField(required=True)
  customer = serializers.SerializerMethodField()
  customer_id = serializers.IntegerField(required=True)
  currency = serializers.SerializerMethodField()
  currency_id = serializers.IntegerField(required=False, allow_null=True)
  user = serializers.SerializerMethodField()
  user_id = serializers.IntegerField(required=False, allow_null=True)
  payment_method = serializers.SerializerMethodField()
  payment_method_id = serializers.IntegerField(required=True)
  sale_order = serializers.SerializerMethodField()
  sale_order_id = serializers.IntegerField(required=False, allow_null=True)

  sale_details = SaleDetailSerializer(many=True)

  class Meta:
    model = Sale
    fields = [
      'id',
      'document_type',
      'series',
      'number',
      'bill',
      'issue_date',
      'company',
      'company_id',
      'branch_office',
      'branch_office_id',
      'warehouse',
      'warehouse_id',
      'customer',
      'customer_id',
      'currency',
      'currency_id',
      'user',
      'user_id',
      'exchange_rate',
      'discount',
      'subtotal',
      'total',
      'total_paid',
      'change_amount',
      'sale_status',
      'payment_method',
      'payment_method_id',
      'sale_order',
      'sale_order_id',
      'tax_identification',
      'retention',
      'perception',
      'sale_details'
    ]

    read_only_fields = ('number', 'updated_at', 'created_at', 'deleted_at')

  def get_company(self, obj):
    if obj.company:
      CompanySerializer.Meta.model = obj.company.__class__
      return CompanySerializer(obj.company).data
    return None

  def get_branch_office(self, obj):
    if obj.branch_office:
      BranchOfficeSerializer.Meta.model = obj.branch_office.__class__
      return BranchOfficeSerializer(obj.branch_office).data
    return None
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
  
  def get_payment_method(self, obj):
    if obj.payment_method:
      PaymentMethodSerializer.Meta.model = obj.payment_method.__class__
      return PaymentMethodSerializer(obj.payment_method).data
    return None
  
  def get_sale_order(self, obj):
    if obj.sale_order:
      SaleOrderSerializer.Meta.model = obj.sale_order.__class__
      return SaleOrderSerializer(obj.sale_order).data
    return None
  
  def create(self, validated_data):
    details_data = validated_data.pop("sale_details", [])
    sale = Sale.objects.create(**validated_data)
    for detail_data in details_data:
      SaleDetail.objects.create(sale=sale, **detail_data)
    return sale

  def update(self, instance, validated_data):
    details_data = validated_data.pop("sale_details", [])
    for attr, value in validated_data.items():
      setattr(instance, attr, value)
    instance.save()

    # actualizar detalles (simplificado: borra y vuelve a crear)
    instance.sale_details.all().delete()
    for detail_data in details_data:
      SaleDetail.objects.create(sale=instance, **detail_data)
    return instance