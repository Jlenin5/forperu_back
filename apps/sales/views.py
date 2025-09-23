import json
import traceback
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from django.utils import timezone
from apps.electronic_invoices.models import ElectronicInvoice
from apps.sales.models import Sale, SaleDetail
from apps.sales.serializers import SaleSerializer, SaleDetailSerializer
# libs for pdf
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.http import FileResponse, Http404
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import qrcode
from io import BytesIO
import io

from services.nubefact.nubefact_service import NubefactService

def generate_qr(data: str):
  qr = qrcode.QRCode(
    version=1,
    box_size=5,
    border=2
  )
  qr.add_data(data)
  qr.make(fit=True)
  img = qr.make_image(fill_color="black", back_color="white")

  buffer = BytesIO()
  img.save(buffer, format="PNG")
  buffer.seek(0)
  return buffer

class SaleAPIView(APIView):
  permission_classes = [IsAuthenticated]
  parser_classes = [JSONParser, FormParser, MultiPartParser]

  def get(self, request, pk=None, format=None):
    if pk:
      sale = get_object_or_404(Sale, pk=pk, deleted_at__isnull=True)
      serializer = SaleSerializer(sale)
      return Response(serializer.data, status=status.HTTP_200_OK)

    sales = Sale.objects.filter(deleted_at__isnull=True).order_by("-id")
    serializer = SaleSerializer(sales, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

  def post(self, request, format=None):
    serializer = SaleSerializer(data=request.data)
    if serializer.is_valid():
      sale = serializer.save(user=request.user)

      # Emitir a Nubefact si está configurado
      self._emit_to_nubefact(sale, request.user)
      
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def put(self, request, pk, format=None):
    sale = get_object_or_404(Sale, pk=pk, deleted_at__isnull=True)
    serializer = SaleSerializer(sale, data=request.data)
    if serializer.is_valid():
      serializer.save(updated_at=timezone.now())
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def patch(self, request, pk, format=None):
    sale = get_object_or_404(Sale, pk=pk, deleted_at__isnull=True)
    serializer = SaleSerializer(sale, data=request.data, partial=True)
    if serializer.is_valid():
      serializer.save(updated_at=timezone.now())
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def delete(self, request, pk=None, format=None):
    if pk:
      sale = get_object_or_404(Sale, pk=pk, deleted_at__isnull=True)
      sale.deleted_at = timezone.now()
      sale.save()
      return Response({'message': 'Sale deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    return self._delete_multiple(request)

  def _delete_multiple(self, request):
    try:
      sale_ids = request.data if isinstance(request.data, list) else request.data.get('ids', [])

      if not sale_ids:
        return Response({'error': 'No se proporcionaron IDs de ventas'}, status=status.HTTP_400_BAD_REQUEST)

      try:
          sale_ids = [int(id) for id in sale_ids]
      except (ValueError, TypeError):
        return Response({'error': 'IDs de ventas no válidos'}, status=status.HTTP_400_BAD_REQUEST)

      existing_sales = Sale.objects.filter(id__in=sale_ids, deleted_at__isnull=True)

      if existing_sales.count() != len(sale_ids):
        return Response({'error': 'Algunos IDs no existen o ya fueron eliminados'}, status=status.HTTP_400_BAD_REQUEST)

      updated = existing_sales.update(deleted_at=timezone.now())

      return Response({
        'message': f'{updated} ventas eliminadas exitosamente',
        'deleted_count': updated
      }, status=status.HTTP_200_OK)

    except Exception as e:
      traceback.print_exc()
      return Response({'error': f'Error al eliminar ventas: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
  
  def _emit_to_nubefact(self, sale, user):
    try:
      # Obtener la compañía y verificar si tiene proveedor de facturación
      company = sale.company
      if not company.electronic_invoicing_provider:
        return None

      # Verificar si es Nubefact
      provider = company.electronic_invoicing_provider
      if 'nubefact' not in provider.name.lower():
        return None

      # Crear servicio Nubefact
      nubefact_service = NubefactService(
        api_token=provider.api_token,
        api_url=provider.api_url
      )

      # Emitir comprobante
      result = nubefact_service.create_invoice(sale, company)

      # Guardar respuesta en ElectronicInvoice
      electronic_invoice = ElectronicInvoice(
        sale=sale,
        provider=provider,
        document_type=sale.document_type,
        series=sale.series,
        number=sale.number,
        status='pending'
      )

      if result['success']:
        response_data = result['data']
        electronic_invoice.external_id = response_data.get('id')
        electronic_invoice.status = 'sent'
        electronic_invoice.response_message = json.dumps(response_data)
        electronic_invoice.sent_at = timezone.now()
        
        # Guardar URLs si están disponibles
        if 'enlace_del_pdf' in response_data:
          electronic_invoice.pdf_url = response_data.get('enlace_del_pdf')
        if 'enlace_del_cdr' in response_data:
          electronic_invoice.cdr_url = response_data.get('enlace_del_cdr')
        if 'enlace_del_xml' in response_data:
          electronic_invoice.xml_url = response_data.get('enlace_del_xml')
      else:
        electronic_invoice.status = 'rejected'
        electronic_invoice.response_message = json.dumps(result['errors'])

      electronic_invoice.save()
      return electronic_invoice

    except Exception as e:
      # Crear registro de error
      ElectronicInvoice.objects.create(
        sale=sale,
        provider=provider if 'provider' in locals() else None,
        document_type=sale.document_type,
        series=sale.series,
        number=sale.number,
        status='rejected',
        response_message=f"Error al emitir: {str(e)}"
      )
      return None

class SaleDetailAPIView(APIView):
  permission_classes = [IsAuthenticated]
  parser_classes = [JSONParser, FormParser, MultiPartParser]

  def get(self, request, pk=None, format=None):
    if pk:
      detail = get_object_or_404(SaleDetail, pk=pk, deleted_at__isnull=True)
      serializer = SaleDetailSerializer(detail)
      return Response(serializer.data, status=status.HTTP_200_OK)

    details = SaleDetail.objects.filter(deleted_at__isnull=True)
    serializer = SaleDetailSerializer(details, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

  def post(self, request, format=None):
    serializer = SaleDetailSerializer(data=request.data)
    if serializer.is_valid():
      serializer.save()
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def put(self, request, pk, format=None):
    detail = get_object_or_404(SaleDetail, pk=pk, deleted_at__isnull=True)
    serializer = SaleDetailSerializer(detail, data=request.data)
    if serializer.is_valid():
      serializer.save(updated_at=timezone.now())
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def patch(self, request, pk, format=None):
    detail = get_object_or_404(SaleDetail, pk=pk, deleted_at__isnull=True)
    serializer = SaleDetailSerializer(detail, data=request.data, partial=True)
    if serializer.is_valid():
      serializer.save(updated_at=timezone.now())
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def delete(self, request, pk=None, format=None):
    if pk:
      detail = get_object_or_404(SaleDetail, pk=pk, deleted_at__isnull=True)
      detail.deleted_at = timezone.now()
      detail.save()
      return Response({'message': 'Sale detail deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    return self._delete_multiple(request)

  def _delete_multiple(self, request):
    try:
      detail_ids = request.data if isinstance(request.data, list) else request.data.get('ids', [])

      if not detail_ids:
        return Response({'error': 'No se proporcionaron IDs de detalles de venta'}, status=status.HTTP_400_BAD_REQUEST)

      try:
          detail_ids = [int(id) for id in detail_ids]
      except (ValueError, TypeError):
        return Response({'error': 'IDs de detalles no válidos'}, status=status.HTTP_400_BAD_REQUEST)

      existing_details = SaleDetail.objects.filter(id__in=detail_ids, deleted_at__isnull=True)

      if existing_details.count() != len(detail_ids):
        return Response({'error': 'Algunos IDs no existen o ya fueron eliminados'}, status=status.HTTP_400_BAD_REQUEST)

      updated = existing_details.update(deleted_at=timezone.now())

      return Response({
        'message': f'{updated} detalles de venta eliminados exitosamente',
        'deleted_count': updated
      }, status=status.HTTP_200_OK)

    except Exception as e:
      traceback.print_exc()
      return Response({'error': f'Error al eliminar detalles: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SaleStatusAPIView(APIView):
  permission_classes = [IsAuthenticated]
  parser_classes = [JSONParser, FormParser, MultiPartParser]

  def patch(self, request, pk, format=None):
    sale = get_object_or_404(Sale, pk=pk, deleted_at__isnull=True)
    
    new_status = request.data.get('sale_status')
    if not new_status:
      return Response({'error': 'El campo sale_status es requerido'}, status=status.HTTP_400_BAD_REQUEST)
    
    if new_status not in dict(Sale.SALE_STATUS_CHOICES):
      return Response({'error': 'Estado de venta no válido'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Lógica adicional según el estado (puedes personalizar esto)
    if new_status == 'paid':
      sale.sale_status = 'paid'
      # Aquí podrías agregar lógica para registrar el pago
    elif new_status == 'canceled':
      sale.sale_status = 'canceled'
      # Aquí podrías agregar lógica para reversar inventario, etc.
    else:
      sale.sale_status = new_status
    
    sale.updated_at = timezone.now()
    sale.save()
    
    serializer = SaleSerializer(sale)
    return Response(serializer.data, status=status.HTTP_200_OK)

class SaleByReferenceAPIView(APIView):
  permission_classes = [IsAuthenticated]
  parser_classes = [JSONParser, FormParser, MultiPartParser]

  def get(self, request, format=None):
    reference = request.query_params.get('reference')
    document_type = request.query_params.get('document_type')
    
    if not reference:
      return Response({'error': 'El parámetro reference es requerido'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
      if document_type == 'invoice':
        # Para facturas: buscar por serie y número
        if '-' in reference:
          series, number = reference.split('-', 1)
          sale = get_object_or_404(
            Sale, 
            series=series, 
            number=number, 
            document_type='invoice',
            deleted_at__isnull=True
          )
        else:
          return Response({'error': 'Formato de referencia de factura inválido'}, status=status.HTTP_400_BAD_REQUEST)
      else:
        # Para tickets: buscar por bill
        sale = get_object_or_404(
          Sale, 
          bill=reference, 
          document_type='ticket',
          deleted_at__isnull=True
        )
      
      serializer = SaleSerializer(sale)
      return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Sale.DoesNotExist:
      return Response({'error': 'Venta no encontrada'}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
      return Response({'error': 'Formato de referencia inválido'}, status=status.HTTP_400_BAD_REQUEST)

# PDF TICKET (80mm x largo)
class SalePDFTicketView(APIView):
  permission_classes = [IsAuthenticated]

  def get(self, request, bill, format=None):
    # Tamaño rollo ticket (80mm ancho, altura flexible)
    pagesize = (80 * mm, 250 * mm)

    # Obtener la venta
    sale = get_object_or_404(Sale, bill=bill)

    # Crear buffer y PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
      buffer,
      pagesize=pagesize,
      rightMargin=5,
      leftMargin=5,
      topMargin=10,
      bottomMargin=10
    )

    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Center", alignment=TA_CENTER, fontSize=8))
    styles.add(ParagraphStyle(name="Right", alignment=TA_RIGHT, fontSize=8))
    styles.add(ParagraphStyle(name="Small", alignment=TA_LEFT, fontSize=7))

    # ---------------------------
    # ENCABEZADO EMPRESA
    # ---------------------------
    company = (
      sale.warehouse.branch_office.company
      if sale.warehouse and sale.warehouse.branch_office
      else None
    )

    company_name = company.name if company else "EMPRESA NO REGISTRADA"
    company_address = company.address if company else "--"
    company_phone = company.phone if company else "--"
    company_email = company.email if company else "--"

    header = [
      Paragraph(f"<b>{company_name}</b>", styles["Center"]),
      Paragraph(f"{company_address}", styles["Center"]),
      Paragraph(f"Tel: {company_phone}", styles["Center"]),
      Paragraph(f"{company_email}", styles["Center"]),
      Spacer(1, 5),
    ]
    elements.extend(header)

    # Documento
    document_type = "Boleta" if sale.document_type == "ticket" else "Factura"
    elements.append(
      Paragraph(f"<b>{document_type} #{sale.bill}</b>", styles["Center"])
    )
    elements.append(
      Paragraph(
        sale.issue_date.strftime("%d/%m/%Y %I:%M %p"), styles["Center"]
      )
    )
    elements.append(Spacer(1, 8))

    # ---------------------------
    # CLIENTE
    # ---------------------------
    client_data = [
      ["Cliente:", f"{sale.customer.names} {sale.customer.surname}"],
      ["Doc:", f"{sale.customer.document_number or '--'}"],
      ["Tel:", f"{sale.customer.phone or '--'}"],
    ]
    table_client = Table(client_data, colWidths=[30, 120])
    table_client.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 7)]))
    elements.append(table_client)
    elements.append(Spacer(1, 8))

    # ---------------------------
    # DETALLES PRODUCTOS (LISTADO)
    # ---------------------------
    product_style = ParagraphStyle(
      name="ProductStyle",
      fontSize=8,
      leading=10,
      alignment=TA_CENTER,
      wordWrap='CJK'   # permite saltos de línea en textos largos
    )

    detail_style = ParagraphStyle(
      name="DetailStyle",
      fontSize=7,
      leading=9,
      alignment=TA_CENTER
    )

    elements.append(Paragraph("<b>DETALLE DE PRODUCTOS</b>", styles["Center"]))
    elements.append(Spacer(1, 5))

    for detail in sale.sale_details.all():
      # Nombre del producto (cabecera)
      product_name = detail.product_name or detail.product.name
      elements.append(Paragraph(f"<b>{product_name}</b>", product_style))

      # Línea con cantidad, precio y total
      qty = f"Cantidad: {detail.quantity}"
      price = f"Precio: {sale.currency.symbol}{detail.price:.2f}"
      total = f"Total: {sale.currency.symbol}{detail.total:.2f}"

      elements.append(Paragraph(f"{qty}   |   {price}   |   {total}", detail_style))
      elements.append(Spacer(1, 5))
      elements.append(Spacer(1, 8))

    # ---------------------------
    # RESUMEN
    # ---------------------------
    resumen_data = [
      ["SUBTOTAL:", f"{sale.currency.symbol}{sale.subtotal:.2f}"],
      ["IGV (18%):", f"{sale.currency.symbol}{(sale.total - sale.subtotal):.2f}"],
      ["TOTAL:", f"{sale.currency.symbol}{sale.total:.2f}"],
      ["PAGADO:", f"{sale.currency.symbol}{sale.total_paid:.2f}"],
      ["CAMBIO:", f"{sale.currency.symbol}{sale.change_amount:.2f}"],
    ]
    resumen_table = Table(resumen_data, colWidths=[70, 60], hAlign="RIGHT")
    resumen_table.setStyle(TableStyle([
      ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
      ("FONTSIZE", (0, 0), (-1, -1), 7),
    ]))
    elements.append(resumen_table)
    elements.append(Spacer(1, 12))

    # Código QR SUNAT
    qr_data = f"{sale.warehouse.company.ruc}|{sale.bill}|{sale.issue_date}|{sale.total}"
    qr_buffer = generate_qr(qr_data)
    qr_img = Image(qr_buffer, width=80, height=80)
    elements.append(qr_img)
    elements.append(Spacer(1, 12))

    # Observaciones / Nubefact style
    elements.append(Paragraph("<b>Observaciones:</b>", styles['Heading3']))
    elements.append(Paragraph("Representación impresa de la factura electrónica.", styles['Normal']))
    elements.append(Paragraph("Gracias por su compra.", styles['Normal']))

    # ---------------------------
    # FOOTER
    # ---------------------------
    footer = Paragraph(
      "Gracias por su compra<br/><b>Este documento no tiene valor legal</b>",
      styles["Center"]
    )
    elements.append(footer)

    # Construir PDF
    doc.build(elements)
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=False, filename=f"ticket-{sale.bill}.pdf")

class SalePDFA4View(APIView):
  permission_classes = [IsAuthenticated]

  def get(self, request, bill, format=None):
    sale = get_object_or_404(Sale, bill=bill)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=30)

    elements = []
    styles = getSampleStyleSheet()

    # ---------------------------
    # ENCABEZADO EMPRESA
    # ---------------------------
    company = (sale.warehouse.branch_office.company
                if sale.warehouse and sale.warehouse.branch_office else
                sale.warehouse.company if sale.warehouse and sale.warehouse.company else None)

    company_name = company.name if company else "EMPRESA NO REGISTRADA"
    company_address = company.address if company else "--"
    company_phone = company.phone if company else "--"
    company_email = company.email if company else "--"

    header_data = [
      [
          Paragraph(f"<b>{company_name}</b>", styles["Title"]),
          Paragraph(f"<b>{'Factura' if sale.document_type == 'invoice' else 'Boleta'} #{sale.bill}</b>",
                    ParagraphStyle(name="RightHeader", alignment=TA_RIGHT, fontSize=12)),
      ],
      [
          Paragraph(f"{company_address}<br/>Tel: {company_phone}<br/>{company_email}",
                    styles["Normal"]),
          Paragraph(f"Fecha: {sale.issue_date.strftime('%d/%m/%Y')}<br/>"
                    f"Usuario: {sale.user.employee.names if sale.user and sale.user.employee else ''}",
                    ParagraphStyle(name="RightNormal", alignment=TA_RIGHT, fontSize=10))
      ]
    ]

    table_header = Table(header_data, colWidths=[300, 200])
    table_header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(table_header)
    elements.append(Spacer(1, 12))

    # ---------------------------
    # DATOS CLIENTE
    # ---------------------------

    customer_name = ''
    if sale.customer.names:
      customer_name = f"{sale.customer.names} {sale.customer.surname} {sale.customer.second_surname}"
    else:
      customer_name = f"{sale.customer.company_name}"
    
    client_data = [
      [Paragraph("<b>Cliente:</b>", styles["Normal"]),
        Paragraph(customer_name, styles["Normal"])],
      [Paragraph("<b>Dirección:</b>", styles["Normal"]),
        Paragraph(f"{sale.customer.address or '--'}", styles["Normal"])],
      [Paragraph("<b>Tel:</b>", styles["Normal"]),
        Paragraph(f"{sale.customer.phone or '--'}", styles["Normal"])]
    ]
    table_client = Table(client_data, colWidths=[80, 420])
    table_client.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.grey)]))
    elements.append(table_client)
    elements.append(Spacer(1, 15))

    # Definir un estilo pequeño con salto de línea habilitado
    product_style = ParagraphStyle(
      name="ProductStyle",
      fontSize=8,
      leading=10,        # espacio entre líneas
      wordWrap='CJK',    # permite cortar palabras largas y hacer saltos
    )

    # ---------------------------
    # TABLA DETALLES
    # ---------------------------
    data = [["SKU", "Producto", "V/U", "P/U", "Cant.", "Dsc.", "Total"]]

    for detail in sale.sale_details.all():
      discount_value = f"{detail.discount}%" if detail.discount_method else f"{sale.currency.symbol}{detail.discount}"
      
      # Usar Paragraph para el producto (permite salto de línea)
      product_paragraph = Paragraph(detail.product_name or detail.product.name, product_style)

      data.append([
        detail.product.sku,
        product_paragraph,
        Paragraph(f"{sale.currency.symbol}{detail.price:.2f}", product_style),
        Paragraph(f"{sale.currency.symbol}{detail.total / detail.quantity:.2f}", product_style),
        Paragraph(str(detail.quantity), product_style),
        Paragraph(discount_value, product_style),
        Paragraph(f"{sale.currency.symbol}{detail.total:.2f}", product_style),
      ])

    table = Table(data, colWidths=[50, 220, 47, 47, 40, 45, 50])
    table.setStyle(TableStyle([
      ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
      ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
      ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
      ("ALIGN", (1, 1), (-1, -1), "CENTER"),
      ("ALIGN", (0, 1), (0, -1), "LEFT"),  # Producto alineado a la izquierda
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # ---------------------------
    # RESUMEN
    # ---------------------------
    resumen_data = [
      ["DESCUENTO:", f"{sale.currency.symbol}{sale.discount or 0:.2f}"],
      ["SUBTOTAL:", f"{sale.currency.symbol}{sale.subtotal:.2f}"],
      ["IGV (18%):", f"{sale.currency.symbol}{(sale.total - sale.subtotal):.2f}"],
      ["TOTAL:", f"{sale.currency.symbol}{sale.total:.2f}"],
      ["PAGADO:", f"{sale.currency.symbol}{sale.total_paid:.2f}"],
      ["CAMBIO:", f"{sale.currency.symbol}{sale.change_amount:.2f}"],
    ]

    resumen_table = Table(resumen_data, colWidths=[100, 100], hAlign="RIGHT")
    resumen_table.setStyle(TableStyle([
      ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
      ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
      ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    elements.append(resumen_table)

    # ---------------------------
    # FOOTER
    # ---------------------------
    elements.append(Spacer(1, 30))
    footer = Paragraph("Gracias por su compra. <br/>Este documento no tiene valor legal.",
                        ParagraphStyle(name="Footer", alignment=TA_CENTER, fontSize=8, textColor=colors.grey))
    elements.append(footer)

    # Código QR
    qr_data = f"{sale.warehouse.company.ruc}|{sale.bill}|{sale.issue_date}|{sale.total}"
    qr_buffer = generate_qr(qr_data)
    qr_img = Image(qr_buffer, width=120, height=120)
    elements.append(qr_img)
    elements.append(Spacer(1, 6))

    # Observaciones
    elements.append(Paragraph("Representación impresa de la boleta electrónica.", styles['Normal']))
    elements.append(Paragraph("Gracias por su compra.", styles['Normal']))

    # Construir PDF
    doc.build(elements)
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=False, filename=f"a4-{sale.bill}.pdf")