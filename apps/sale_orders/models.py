from django.db import models
from django.db.models import Max
from apps.currencies.models import Currency
from apps.customers.models import Customer
from apps.products.models import Product
from apps.warehouses.models import Warehouse
from apps.quotes.models import Quote
from apps.users.models import UserAccount

class SaleOrder(models.Model):
  reference = models.CharField(max_length=8, unique=True, blank=True)
  warehouse = models.ForeignKey(
    Warehouse,
    on_delete=models.CASCADE,
    db_column='warehouse_id',
    related_name='sale_orders'
  )
  customer = models.ForeignKey(
    Customer,
    on_delete=models.CASCADE,
    db_column='customer_id',
    related_name='sale_orders'
  )
  currency = models.ForeignKey(
    Currency,
    on_delete=models.CASCADE,
    db_column='currency_id',
    related_name='sale_orders'
  )
  user = models.ForeignKey(
    UserAccount,
    on_delete=models.SET_NULL,
    db_column='user_id',
    null=True,
    blank=True,
    related_name='sale_orders_created'
  )
  issue_date = models.DateField(auto_now_add=True)
  exchange_rate = models.DecimalField(max_digits=14, decimal_places=2, default=1.0)
  discount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
  subtotal = models.DecimalField(max_digits=14, decimal_places=2)
  total = models.DecimalField(max_digits=14, decimal_places=2)
  
  ORDER_STATUS_CHOICES = [
    ('issued', 'Issued'),
    ('approved', 'Approved'),
    ('canceled', 'Canceled'),
  ]
  order_status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default='issued')
  
  date_approved = models.DateField(null=True, blank=True)
  migrate_sale_order = models.BooleanField(default=False)
  
  quote = models.ForeignKey(
    Quote,
    on_delete=models.SET_NULL,
    db_column='quote_id',
    null=True,
    blank=True,
    related_name='sale_orders'
  )

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(null=True, blank=True)
  deleted_at = models.DateTimeField(null=True, blank=True)

  class Meta:
    managed = True
    db_table = 'sale_orders'

  def __str__(self):
    return f"{self.reference} - {self.customer}"
  
  def generate_reference(self):
    last_ref = SaleOrder.objects.aggregate(max_ref=Max("reference"))["max_ref"]

    last_number = 0
    if last_ref:
      try:
        last_number = int(last_ref.split("-")[1])
      except (IndexError, ValueError):
        last_number = 0

    new_number = last_number + 1
    return f"SO-{new_number:05d}"

  def save(self, *args, **kwargs):
    if not self.reference:
      self.reference = self.generate_reference()
    super().save(*args, **kwargs)

class SaleOrderDetail(models.Model):
  product_name = models.CharField(max_length=150, null=True, blank=True)
  sale_order = models.ForeignKey(
    SaleOrder,
    on_delete=models.CASCADE,
    db_column='sale_order_id',
    related_name='sale_order_details'
  )
  product = models.ForeignKey(
    Product,
    on_delete=models.CASCADE,
    db_column='product_id',
    related_name='sale_order_details'
  )
  quantity = models.DecimalField(max_digits=14, decimal_places=2)
  discount_method = models.BooleanField(default=True)  # True = porcentaje, False = monto
  discount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
  price = models.DecimalField(max_digits=14, decimal_places=2)
  subtotal = models.DecimalField(max_digits=14, decimal_places=2)
  total = models.DecimalField(max_digits=14, decimal_places=2)

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(null=True, blank=True)
  deleted_at = models.DateTimeField(null=True, blank=True)

  class Meta:
    managed = True
    db_table = 'sale_order_details'

  def __str__(self):
    return f"{self.product_name or self.product.name} - {self.quantity}"