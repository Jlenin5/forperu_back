import traceback
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from django.utils import timezone
from apps.purchase_requests.models import PurchaseRequest, PurchaseRequestDetail
from apps.purchase_requests.serializers import PurchaseRequestSerializer, PurchaseRequestDetailSerializer

class PurchaseRequestAPIView(APIView):
  permission_classes = [IsAuthenticated]
  parser_classes = [JSONParser, FormParser, MultiPartParser]

  def get(self, request, pk=None, format=None):
    if pk:
      purchase_request = get_object_or_404(PurchaseRequest, pk=pk, deleted_at__isnull=True)
      serializer = PurchaseRequestSerializer(purchase_request)
      return Response(serializer.data, status=status.HTTP_200_OK)

    purchase_requests = PurchaseRequest.objects.filter(deleted_at__isnull=True)
    serializer = PurchaseRequestSerializer(purchase_requests, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

  def post(self, request, format=None):
    serializer = PurchaseRequestSerializer(data=request.data)
    if serializer.is_valid():
      serializer.save(user=request.user)
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def put(self, request, pk, format=None):
    purchase_request = get_object_or_404(PurchaseRequest, pk=pk, deleted_at__isnull=True)
    serializer = PurchaseRequestSerializer(purchase_request, data=request.data)
    if serializer.is_valid():
        serializer.save(updated_at=timezone.now())
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def patch(self, request, pk, format=None):
    purchase_request = get_object_or_404(PurchaseRequest, pk=pk, deleted_at__isnull=True)
    serializer = PurchaseRequestSerializer(purchase_request, data=request.data, partial=True)
    if serializer.is_valid():
      serializer.save(updated_at=timezone.now())
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def delete(self, request, pk=None, format=None):
    if pk:
      purchase_request = get_object_or_404(PurchaseRequest, pk=pk, deleted_at__isnull=True)
      purchase_request.deleted_at = timezone.now()
      purchase_request.save()
      return Response({'message': 'Purchase request deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    return self._delete_multiple(request)

  def _delete_multiple(self, request):
    try:
      purchase_request_ids = request.data if isinstance(request.data, list) else request.data.get('ids', [])

      if not purchase_request_ids:
        return Response({'error': 'No se proporcionaron IDs de solicitudes de compra'}, status=status.HTTP_400_BAD_REQUEST)

      try:
        purchase_request_ids = [int(id) for id in purchase_request_ids]
      except (ValueError, TypeError):
        return Response({'error': 'IDs de solicitudes de compra no válidos'}, status=status.HTTP_400_BAD_REQUEST)

      existing_purchase_requests = PurchaseRequest.objects.filter(id__in=purchase_request_ids, deleted_at__isnull=True)

      if existing_purchase_requests.count() != len(purchase_request_ids):
        return Response({'error': 'Algunos IDs no existen o ya fueron eliminados'}, status=status.HTTP_400_BAD_REQUEST)

      updated = existing_purchase_requests.update(deleted_at=timezone.now())

      return Response({
        'message': f'{updated} solicitudes de compra eliminadas exitosamente',
        'deleted_count': updated
      }, status=status.HTTP_200_OK)

    except Exception as e:
      traceback.print_exc()
      return Response({'error': f'Error al eliminar solicitudes de compra: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PurchaseRequestDetailAPIView(APIView):
  permission_classes = [IsAuthenticated]
  parser_classes = [JSONParser, FormParser, MultiPartParser]

  def get(self, request, pk=None, format=None):
    if pk:
      detail = get_object_or_404(PurchaseRequestDetail, pk=pk, deleted_at__isnull=True)
      serializer = PurchaseRequestDetailSerializer(detail)
      return Response(serializer.data, status=status.HTTP_200_OK)

    details = PurchaseRequestDetail.objects.filter(deleted_at__isnull=True)
    serializer = PurchaseRequestDetailSerializer(details, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

  def post(self, request, format=None):
    serializer = PurchaseRequestDetailSerializer(data=request.data)
    if serializer.is_valid():
      serializer.save()
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def put(self, request, pk, format=None):
    detail = get_object_or_404(PurchaseRequestDetail, pk=pk, deleted_at__isnull=True)
    serializer = PurchaseRequestDetailSerializer(detail, data=request.data)
    if serializer.is_valid():
      serializer.save(updated_at=timezone.now())
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def patch(self, request, pk, format=None):
    detail = get_object_or_404(PurchaseRequestDetail, pk=pk, deleted_at__isnull=True)
    serializer = PurchaseRequestDetailSerializer(detail, data=request.data, partial=True)
    if serializer.is_valid():
      serializer.save(updated_at=timezone.now())
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def delete(self, request, pk=None, format=None):
    if pk:
      detail = get_object_or_404(PurchaseRequestDetail, pk=pk, deleted_at__isnull=True)
      detail.deleted_at = timezone.now()
      detail.save()
      return Response({'message': 'Purchase request detail deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    return self._delete_multiple(request)

  def _delete_multiple(self, request):
    try:
      detail_ids = request.data if isinstance(request.data, list) else request.data.get('ids', [])

      if not detail_ids:
        return Response({'error': 'No se proporcionaron IDs de detalles de solicitud de compra'}, status=status.HTTP_400_BAD_REQUEST)

      try:
        detail_ids = [int(id) for id in detail_ids]
      except (ValueError, TypeError):
        return Response({'error': 'IDs de detalles no válidos'}, status=status.HTTP_400_BAD_REQUEST)

      existing_details = PurchaseRequestDetail.objects.filter(id__in=detail_ids, deleted_at__isnull=True)

      if existing_details.count() != len(detail_ids):
        return Response({'error': 'Algunos IDs no existen o ya fueron eliminados'}, status=status.HTTP_400_BAD_REQUEST)

      updated = existing_details.update(deleted_at=timezone.now())

      return Response({
        'message': f'{updated} detalles de solicitud de compra eliminados exitosamente',
        'deleted_count': updated
      }, status=status.HTTP_200_OK)

    except Exception as e:
      traceback.print_exc()
      return Response({'error': f'Error al eliminar detalles: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PurchaseRequestStatusAPIView(APIView):
  permission_classes = [IsAuthenticated]
  parser_classes = [JSONParser, FormParser, MultiPartParser]

  def patch(self, request, pk, format=None):
    purchase_request = get_object_or_404(PurchaseRequest, pk=pk, deleted_at__isnull=True)
    
    new_status = request.data.get('status')
    if not new_status:
      return Response({'error': 'El campo status es requerido'}, status=status.HTTP_400_BAD_REQUEST)
    
    if new_status not in dict(PurchaseRequest.STATUS_CHOICES):
      return Response({'error': 'Estado de solicitud de compra no válido'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Lógica para cambios de estado
    if new_status == 'approved':
      purchase_request.status = 'approved'
      purchase_request.approved_by = request.user
      purchase_request.approval_date = timezone.now()
    elif new_status == 'rejected':
      purchase_request.status = 'rejected'
      purchase_request.approved_by = request.user
      purchase_request.approval_date = timezone.now()
    else:
      purchase_request.status = new_status
    
    purchase_request.updated_at = timezone.now()
    purchase_request.save()
    
    serializer = PurchaseRequestSerializer(purchase_request)
    return Response(serializer.data, status=status.HTTP_200_OK)

class PurchaseRequestDetailStatusAPIView(APIView):
  permission_classes = [IsAuthenticated]
  parser_classes = [JSONParser, FormParser, MultiPartParser]

  def patch(self, request, pk, format=None):
    detail = get_object_or_404(PurchaseRequestDetail, pk=pk, deleted_at__isnull=True)
    
    new_status = request.data.get('status')
    received_quantity = request.data.get('received_quantity')
    
    if not new_status:
      return Response({'error': 'El campo status es requerido'}, status=status.HTTP_400_BAD_REQUEST)
    
    if new_status not in dict(PurchaseRequestDetail.STATUS_CHOICES):
      return Response({'error': 'Estado de detalle no válido'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Actualizar estado
    detail.status = new_status
    
    # Actualizar cantidad recibida si se proporciona
    if received_quantity is not None:
      detail.received_quantity = received_quantity
    
    detail.updated_at = timezone.now()
    detail.save()
    
    serializer = PurchaseRequestDetailSerializer(detail)
    return Response(serializer.data, status=status.HTTP_200_OK)

class PurchaseRequestByReferenceAPIView(APIView):
  permission_classes = [IsAuthenticated]
  parser_classes = [JSONParser, FormParser, MultiPartParser]

  def get(self, request, format=None):
    reference = request.query_params.get('reference')
    
    if not reference:
      return Response({'error': 'El parámetro reference es requerido'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
      purchase_request = get_object_or_404(
        PurchaseRequest, 
        reference=reference, 
        deleted_at__isnull=True
      )
      
      serializer = PurchaseRequestSerializer(purchase_request)
      return Response(serializer.data, status=status.HTTP_200_OK)
        
    except PurchaseRequest.DoesNotExist:
      return Response({'error': 'Solicitud de compra no encontrada'}, status=status.HTTP_404_NOT_FOUND)