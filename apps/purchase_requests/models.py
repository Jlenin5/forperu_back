from django.db import models
from django.db.models import Max
from apps.suppliers.models import Supplier
from apps.products.models import Product
from apps.users.models import UserAccount
class PurchaseRequest(models.Model):
  STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
  ]
  
  PRIORITY_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
  ]
  
  reference = models.CharField(max_length=8, unique=True, blank=True)
  
  supplier = models.ForeignKey(
    Supplier,
    on_delete=models.CASCADE,
    db_column='supplier_id',
    related_name='purchase_requests'
  )
  
  user = models.ForeignKey(
    UserAccount,
    on_delete=models.SET_NULL,
    db_column='user_id',
    null=True,
    blank=True,
    related_name='purchase_requests_created'
  )
  
  request_date = models.DateField(auto_now_add=True)
  expected_delivery_date = models.DateField(null=True, blank=True)
  
  status = models.CharField(
    max_length=50, 
    choices=STATUS_CHOICES, 
    default='pending'
  )
  
  priority = models.CharField(
    max_length=20, 
    choices=PRIORITY_CHOICES, 
    default='medium'
  )
  
  total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
  
  approved_by = models.ForeignKey(
    UserAccount,
    on_delete=models.SET_NULL,
    db_column='approved_by',
    null=True,
    blank=True,
    related_name='purchase_requests_approved'
  )
  
  approval_date = models.DateField(null=True, blank=True)
  notes = models.TextField(null=True, blank=True)

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(null=True, blank=True)
  deleted_at = models.DateTimeField(null=True, blank=True)

  class Meta:
    managed = True
    db_table = 'purchase_requests'

  def __str__(self):
    return f"{self.reference} - {self.supplier} - {self.status}"
  
  def generate_reference(self):
    last_ref = PurchaseRequest.objects.aggregate(max_ref=Max("reference"))["max_ref"]

    last_number = 0
    if last_ref:
      try:
        last_number = int(last_ref.split("-")[1])
      except (IndexError, ValueError):
        last_number = 0

    new_number = last_number + 1
    return f"PR-{new_number:05d}"

  def save(self, *args, **kwargs):
    if not self.reference:
      self.reference = self.generate_reference()
    super().save(*args, **kwargs)

class PurchaseRequestDetail(models.Model):
  STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('received', 'Received'),
    ('canceled', 'Canceled'),
  ]

  purchase_request = models.ForeignKey(
    PurchaseRequest,
    on_delete=models.CASCADE,
    db_column='purchase_request_id',
    related_name='purchase_request_details'
  )
  product = models.ForeignKey(
    Product,
    on_delete=models.CASCADE,
    db_column='product_id',
    related_name='purchase_request_details'
  )
  quantity = models.DecimalField(max_digits=14, decimal_places=2)
  unit_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
  estimated_cost = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
  subtotal = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
  received_quantity = models.IntegerField(default=0)
  status = models.CharField(
    max_length=50, 
    choices=STATUS_CHOICES, 
    default='pending'
  )
  comments = models.TextField(null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(null=True, blank=True)
  deleted_at = models.DateTimeField(null=True, blank=True)

  class Meta:
    managed = True
    db_table = 'purchase_request_details'

  def __str__(self):
    return f"{self.product.name} - {self.quantity} - {self.status}"
  
  def save(self, *args, **kwargs):
    # Calcular subtotal si hay unit_price y quantity
    if self.unit_price and self.quantity:
      self.subtotal = self.unit_price * self.quantity
      self.estimated_cost = self.subtotal
    
    super().save(*args, **kwargs)