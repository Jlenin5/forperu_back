from django.db import models
from django.db.models import Max
from apps.branch_offices.models import BranchOffice
from apps.companies.models import Company
from apps.currencies.models import Currency
from apps.customers.models import Customer
from apps.products.models import Product
from apps.warehouses.models import Warehouse
from apps.sale_orders.models import SaleOrder
from apps.payment_methods.models import PaymentMethod
from apps.users.models import UserAccount

class Sale(models.Model):
  DOCUMENT_TYPE_CHOICES = [
    ('ticket', 'Ticket'),
    ('invoice', 'Invoice'),
  ]
  
  SALE_STATUS_CHOICES = [
    ('issued', 'Issued'),
    ('paid', 'Paid'),
    ('unpaid', 'Unpaid'),
    ('pending', 'Pending'),
    ('canceled', 'Canceled'),
  ]
  
  company = models.ForeignKey(
    Company,
    on_delete=models.CASCADE,
    db_column='company_id',
    related_name='sales'
  )
  branch_office = models.ForeignKey(
    BranchOffice,
    on_delete=models.SET_NULL,
    db_column='branch_office_id',
    null=True,
    blank=True,
    related_name='sales'
  )
  warehouse = models.ForeignKey(
    Warehouse,
    on_delete=models.CASCADE,
    db_column='warehouse_id',
    null=True,
    blank=True,
    related_name='sales'
  )
  document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPE_CHOICES)
  series = models.CharField(max_length=4, null=True, blank=True)
  number = models.IntegerField(null=True, blank=True)
  bill = models.CharField(max_length=12, null=True, blank=True)
  issue_date = models.DateField(auto_now_add=True)
  customer = models.ForeignKey(
    Customer,
    on_delete=models.CASCADE,
    db_column='customer_id',
    related_name='sales'
  )
  currency = models.ForeignKey(
    Currency,
    on_delete=models.SET_NULL,
    db_column='currency_id',
    null=True,
    blank=True,
    related_name='sales'
  )
  user = models.ForeignKey(
    UserAccount,
    on_delete=models.SET_NULL,
    db_column='user_id',
    null=True,
    blank=True,
    related_name='sales_created'
  )
  exchange_rate = models.DecimalField(max_digits=14, decimal_places=2, default=1.0)
  discount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
  subtotal = models.DecimalField(max_digits=14, decimal_places=2)
  total = models.DecimalField(max_digits=14, decimal_places=2)
  total_paid = models.DecimalField(max_digits=14, decimal_places=2)
  change_amount = models.DecimalField(max_digits=14, decimal_places=2)
  sale_status = models.CharField(
    max_length=10, 
    choices=SALE_STATUS_CHOICES, 
    default='issued'
  )
  payment_method = models.ForeignKey(
    PaymentMethod,
    on_delete=models.CASCADE,
    db_column='payment_method_id',
    related_name='sales'
  )
  sale_order = models.ForeignKey(
    SaleOrder,
    on_delete=models.SET_NULL,
    db_column='sale_order_id',
    null=True,
    blank=True,
    related_name='sales'
  )
  tax_identification = models.CharField(max_length=20, null=True, blank=True)
  retention = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
  perception = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(null=True, blank=True)
  deleted_at = models.DateTimeField(null=True, blank=True)

  class Meta:
    managed = True
    db_table = 'sales'

  def __str__(self):
    document_ref = f"{self.series}-{str(self.number).zfill(6)}" if self.series and self.number else self.bill or "Sin referencia"
    return f"{document_ref} - {self.customer} - {self.total}"

  def set_series_and_number(self):
    if self.document_type == 'invoice':
      self.series = "FFF1"
    elif self.document_type == 'ticket':
      self.series = "BBB1"

    # Obtener el último número usado para esa serie
    last_number = Sale.objects.filter(
      series=self.series,
      document_type=self.document_type,
      deleted_at__isnull=True
    ).aggregate(max_number=Max("number"))["max_number"]

    self.number = (last_number or 0) + 1

    # Formatear bill con número en 6 dígitos
    self.bill = f"{self.series}-{str(self.number).zfill(6)}"

  def save(self, *args, **kwargs):
    # Solo asignar si aún no tiene número/serie/bill
    if not self.series or not self.number or not self.bill:
      self.set_series_and_number()
    super().save(*args, **kwargs)

class SaleDetail(models.Model):
  product_name = models.CharField(max_length=150, null=True, blank=True)
  
  sale = models.ForeignKey(
    Sale,
    on_delete=models.CASCADE,
    db_column='sale_id',
    related_name='sale_details'
  )
  
  product = models.ForeignKey(
    Product,
    on_delete=models.CASCADE,
    db_column='product_id',
    related_name='sale_details'
  )
  
  quantity = models.DecimalField(max_digits=14, decimal_places=2)
  discount_method = models.BooleanField(default=True)  # True = porcentaje, False = monto
  discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
  price = models.DecimalField(max_digits=14, decimal_places=2)
  subtotal = models.DecimalField(max_digits=14, decimal_places=2)
  total = models.DecimalField(max_digits=14, decimal_places=2)

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(null=True, blank=True)
  deleted_at = models.DateTimeField(null=True, blank=True)

  class Meta:
    managed = True
    db_table = 'sale_details'

  def __str__(self):
    return f"{self.product_name or self.product.name} - {self.quantity} - {self.total}"