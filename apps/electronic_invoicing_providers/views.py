import traceback
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from django.utils import timezone

from apps.electronic_invoicing_providers.models import ElectronicInvoicingProvider
from apps.electronic_invoicing_providers.serializers import ElectronicInvoicingProviderSerializer

class ElectronicInvoicingProviderAPIView(APIView):
  permission_classes = [IsAuthenticated]
  parser_classes = [JSONParser, FormParser, MultiPartParser]

  def get(self, request, pk=None, format=None):
    if pk:
      provider = get_object_or_404(ElectronicInvoicingProvider, pk=pk, deleted_at__isnull=True)
      serializer = ElectronicInvoicingProviderSerializer(provider)
      return Response(serializer.data, status=status.HTTP_200_OK)

    providers = ElectronicInvoicingProvider.objects.filter(deleted_at__isnull=True)
    serializer = ElectronicInvoicingProviderSerializer(providers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

  def post(self, request, format=None):
    serializer = ElectronicInvoicingProviderSerializer(data=request.data)
    if serializer.is_valid():
      serializer.save(created_by=request.user)
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def put(self, request, pk, format=None):
    provider = get_object_or_404(ElectronicInvoicingProvider, pk=pk, deleted_at__isnull=True)
    serializer = ElectronicInvoicingProviderSerializer(provider, data=request.data)
    if serializer.is_valid():
      serializer.save(updated_by=request.user, updated_at=timezone.now())
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def patch(self, request, pk, format=None):
    provider = get_object_or_404(ElectronicInvoicingProvider, pk=pk, deleted_at__isnull=True)
    serializer = ElectronicInvoicingProviderSerializer(provider, data=request.data, partial=True)
    if serializer.is_valid():
      serializer.save(updated_by=request.user, updated_at=timezone.now())
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def delete(self, request, pk=None, format=None):
    if pk:
      provider = get_object_or_404(ElectronicInvoicingProvider, pk=pk, deleted_at__isnull=True)
      provider.deleted_at = timezone.now()
      provider.updated_by = request.user
      provider.save()
      return Response({'message': 'Electronic invoicing provider deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    return self._delete_multiple(request)

  def _delete_multiple(self, request):
    try:
      provider_ids = request.data if isinstance(request.data, list) else request.data.get('ids', [])
      if not provider_ids:
        return Response({'error': 'No se proporcionaron IDs de proveedores'}, status=status.HTTP_400_BAD_REQUEST)

      provider_ids = [int(i) for i in provider_ids]
      existing_providers = ElectronicInvoicingProvider.objects.filter(id__in=provider_ids, deleted_at__isnull=True)
      if existing_providers.count() != len(provider_ids):
        return Response({'error': 'Algunos IDs no existen o ya fueron eliminados'}, status=status.HTTP_400_BAD_REQUEST)

      updated = existing_providers.update(deleted_at=timezone.now(), updated_by=request.user)
      return Response({'message': f'{updated} proveedores eliminados exitosamente', 'deleted_count': updated}, status=status.HTTP_200_OK)
    except Exception as e:
      traceback.print_exc()
      return Response({'error': f'Error al eliminar proveedores: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)