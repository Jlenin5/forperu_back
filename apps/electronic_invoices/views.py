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
from apps.electronic_invoices.serializers import ElectronicInvoiceSerializer
from services.nubefact.nubefact_service import NubefactService

class ElectronicInvoiceAPIView(APIView):
  permission_classes = [IsAuthenticated]
  parser_classes = [JSONParser, FormParser, MultiPartParser]

  def get(self, request, pk=None, format=None):
    if pk:
      invoice = get_object_or_404(ElectronicInvoice, pk=pk, deleted_at__isnull=True)
      serializer = ElectronicInvoiceSerializer(invoice)
      return Response(serializer.data, status=status.HTTP_200_OK)

    invoices = ElectronicInvoice.objects.filter(deleted_at__isnull=True)
    serializer = ElectronicInvoiceSerializer(invoices, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

  def post(self, request, sale_id):
    try:
      electronic_invoice = ElectronicInvoice.objects.get(sale_id=sale_id)
      provider = electronic_invoice.provider
      
      if 'nubefact' in provider.name.lower():
        nubefact_service = NubefactService(
          api_token=provider.api_token,
          api_url=provider.api_url
        )
        
        if electronic_invoice.external_id:
          # Consultar estado existente
          status_result = nubefact_service.get_invoice_status(
            electronic_invoice.external_id
          )
          electronic_invoice.response_message = json.dumps(status_result)
          electronic_invoice.save()
          
          return Response(status_result)
        else:
          # Re-emitir
          sale = electronic_invoice.sale
          result = nubefact_service.create_invoice(sale, sale.company)
          
          if result['success']:
            electronic_invoice.external_id = result['data'].get('id')
            electronic_invoice.status = 'sent'
            electronic_invoice.response_message = json.dumps(result['data'])
            electronic_invoice.sent_at = timezone.now()
          else:
            electronic_invoice.status = 'rejected'
            electronic_invoice.response_message = json.dumps(result['errors'])
          
          electronic_invoice.save()
          return Response(result)
        
      return Response({'error': 'Proveedor no compatible'})
        
    except ElectronicInvoice.DoesNotExist:
      return Response({'error': 'No se encontró factura electrónica'}, status=status.HTTP_404_NOT_FOUND)

  def put(self, request, pk, format=None):
    invoice = get_object_or_404(ElectronicInvoice, pk=pk, deleted_at__isnull=True)
    serializer = ElectronicInvoiceSerializer(invoice, data=request.data)
    if serializer.is_valid():
      serializer.save(updated_by=request.user, updated_at=timezone.now())
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def patch(self, request, pk, format=None):
    invoice = get_object_or_404(ElectronicInvoice, pk=pk, deleted_at__isnull=True)
    serializer = ElectronicInvoiceSerializer(invoice, data=request.data, partial=True)
    if serializer.is_valid():
      serializer.save(updated_by=request.user, updated_at=timezone.now())
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def delete(self, request, pk=None, format=None):
    if pk:
      invoice = get_object_or_404(ElectronicInvoice, pk=pk, deleted_at__isnull=True)
      invoice.deleted_at = timezone.now()
      invoice.updated_by = request.user
      invoice.save()
      return Response({'message': 'Electronic invoice deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    return self._delete_multiple(request)

  def _delete_multiple(self, request):
    try:
      invoice_ids = request.data if isinstance(request.data, list) else request.data.get('ids', [])
      if not invoice_ids:
        return Response({'error': 'No se proporcionaron IDs de facturas'}, status=status.HTTP_400_BAD_REQUEST)

      invoice_ids = [int(i) for i in invoice_ids]
      existing_invoices = ElectronicInvoice.objects.filter(id__in=invoice_ids, deleted_at__isnull=True)
      if existing_invoices.count() != len(invoice_ids):
        return Response({'error': 'Algunos IDs no existen o ya fueron eliminados'}, status=status.HTTP_400_BAD_REQUEST)

      updated = existing_invoices.update(deleted_at=timezone.now(), updated_by=request.user)
      return Response({'message': f'{updated} facturas eliminadas exitosamente', 'deleted_count': updated}, status=status.HTTP_200_OK)
    except Exception as e:
      traceback.print_exc()
      return Response({'error': f'Error al eliminar facturas: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)