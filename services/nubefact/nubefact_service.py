import requests
import json
import base64
from datetime import datetime
from django.conf import settings
from django.utils import timezone

class NubefactService:
  def __init__(self, api_token, api_url):
    self.api_token = api_token
    self.api_url = api_url
    self.headers = {
      'Authorization': f'Token token="{api_token}"',
      'Content-Type': 'application/json'
    }

  def _get_tipo_documento(self, document_type):
    mapping = {
      'invoice': '01',  # Factura
      'ticket': '03',   # Boleta
    }
    return mapping.get(document_type, '01')

  def _get_tipo_moneda(self, currency_code):
    mapping = {
      'PEN': 1,
      'USD': 2,
      'EUR': 3
    }
    return mapping.get(currency_code, 'PEN')

  def _prepare_items(self, sale_details):
    items = []
    for detail in sale_details:
      # Determinar tipo de afectación IGV (10 = Gravado)
      # Puedes ajustar según tus necesidades
      tipo_afectacion_igv = "1"  # Gravado - Operación Onerosa

      valor_unitario = float(detail.subtotal) / float(detail.quantity or 1)
      precio_unitario = float(detail.total) / float(detail.quantity or 1)
      
      items.append({
        "unidad_de_medida": "NIU",  # Unidad
        "codigo": str(detail.product.id),
        "descripcion": detail.product_name or detail.product.name,
        "cantidad": float(detail.quantity),
        "valor_unitario": round(valor_unitario, 6),   # sin IGV
        "precio_unitario": round(precio_unitario, 6), # con IGV
        "descuento": float(detail.discount) if detail.discount_method else 0,
        "subtotal": float(detail.subtotal),
        "tipo_de_igv": tipo_afectacion_igv,
        "igv": float(detail.total - detail.subtotal),
        "total": float(detail.total),
        "anticipo_regularizacion": False
      })
    return items

  def create_invoice(self, sale, company):
    
    # Preparar datos del cliente
    customer = sale.customer
    documentType = 6 if sale.document_type == 'invoice' else 1  # 6=RUC, 1=DNI

    customer_name = customer.company_name  if sale.document_type == 'invoice' else f"{customer.names} {customer.surname} {customer.second_surname}"

    currencyCode =  self._get_tipo_moneda(sale.currency.code)
    
    # Preparar datos generales
    payload = {
      "operacion": "generar_comprobante",
      "tipo_de_comprobante": self._get_tipo_documento(sale.document_type),
      "serie": sale.series,
      "numero": sale.number,
      "sunat_transaction": 1,
      "cliente_tipo_de_documento": documentType,
      "cliente_numero_de_documento": customer.document_number,
      "cliente_denominacion": customer_name,
      "cliente_direccion": customer.address or "-",
      "cliente_email": customer.email,
      "fecha_de_emision": "12-09-2025",
      "fecha_de_vencimiento": "",
      "moneda": currencyCode,
      "tipo_de_cambio": float(sale.exchange_rate or 0),
      "porcentaje_de_igv": 18.00,
      "descuento_global": float(sale.discount or 0),
      "total_descuento": float(sale.discount or 0),
      "total_anticipo": "",
      "total_gravada": float(sale.subtotal or 0),
      "total_inafecta": "",
      "total_exonerada": "",
      "total_igv": float((sale.total or 0) - (sale.subtotal or 0)),
      "total_gratuita": "",
      "total_otros_cargos": "",
      "total": float(sale.total or 0),
      "detraccion": "false",
      "tipo_de_nota_de_credito": 10,
      "percepcion_tipo": "",
      "percepcion_base_imponible": "",
      "total_percepcion": "",
      "total_incluido_percepcion": "",
      "retencion_tipo": "",
      "retencion_base_imponible": "",
      "total_retencion": "",
      "total_impuestos_bolsas": "",
      "observaciones": "",
    }
    
    # Agregar items
    payload["items"] = self._prepare_items(sale.sale_details.all())

    try:
      response = requests.post(
        self.api_url,
        headers=self.headers,
        data=json.dumps(payload)
      )
      response.raise_for_status()
      data = response.json()

      # Si Nubefact responde éxito
      if "errors" not in data:
        return {
          "success": True,
          "data": data
        }
      else:
        return {
          "success": False,
          "errors": data["errors"]
        }
      
    except requests.exceptions.HTTPError as e:
      print("❌ Error HTTP:", e)
      print("📥 Respuesta completa:", response.text)  # 🔍 Aquí verás el detalle del error
      raise

    except requests.exceptions.RequestException as e:
      return {
        'success': False,
        'data': None,
        'errors': f"Error de conexión: {str(e)}"
      }

  def get_invoice_status(self, external_id):
    """Consulta el estado de un comprobante"""
    try:
      response = requests.get(
        f"{self.api_url}/{external_id}",
        headers=self.headers,
        timeout=30
      )
      return response.json()
    except Exception as e:
      return {'error': str(e)}