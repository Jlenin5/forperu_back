import traceback
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from django.utils import timezone
from apps.sale_orders.models import SaleOrder, SaleOrderDetail
from apps.sale_orders.serializers import SaleOrderSerializer, SaleOrderDetailSerializer

class SaleOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get(self, request, pk=None, format=None):
        if pk:
            sale_order = get_object_or_404(SaleOrder, pk=pk, deleted_at__isnull=True)
            serializer = SaleOrderSerializer(sale_order)
            return Response(serializer.data, status=status.HTTP_200_OK)

        sale_orders = SaleOrder.objects.filter(deleted_at__isnull=True).order_by("-id")
        serializer = SaleOrderSerializer(sale_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = SaleOrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        sale_order = get_object_or_404(SaleOrder, pk=pk, deleted_at__isnull=True)
        serializer = SaleOrderSerializer(sale_order, data=request.data)
        if serializer.is_valid():
            serializer.save(updated_at=timezone.now())
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        sale_order = get_object_or_404(SaleOrder, pk=pk, deleted_at__isnull=True)
        serializer = SaleOrderSerializer(sale_order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(updated_at=timezone.now())
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, format=None):
        if pk:
            sale_order = get_object_or_404(SaleOrder, pk=pk, deleted_at__isnull=True)
            sale_order.deleted_at = timezone.now()
            sale_order.save()
            return Response({'message': 'Sale order deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

        return self._delete_multiple(request)

    def _delete_multiple(self, request):
        try:
            sale_order_ids = request.data if isinstance(request.data, list) else request.data.get('ids', [])

            if not sale_order_ids:
                return Response({'error': 'No se proporcionaron IDs de órdenes de venta'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                sale_order_ids = [int(id) for id in sale_order_ids]
            except (ValueError, TypeError):
                return Response({'error': 'IDs de órdenes de venta no válidos'}, status=status.HTTP_400_BAD_REQUEST)

            existing_sale_orders = SaleOrder.objects.filter(id__in=sale_order_ids, deleted_at__isnull=True)

            if existing_sale_orders.count() != len(sale_order_ids):
                return Response({'error': 'Algunos IDs no existen o ya fueron eliminados'}, status=status.HTTP_400_BAD_REQUEST)

            updated = existing_sale_orders.update(deleted_at=timezone.now())

            return Response({
                'message': f'{updated} órdenes de venta eliminadas exitosamente',
                'deleted_count': updated
            }, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response({'error': f'Error al eliminar órdenes de venta: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SaleOrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get(self, request, pk=None, format=None):
        if pk:
            detail = get_object_or_404(SaleOrderDetail, pk=pk, deleted_at__isnull=True)
            serializer = SaleOrderDetailSerializer(detail)
            return Response(serializer.data, status=status.HTTP_200_OK)

        details = SaleOrderDetail.objects.filter(deleted_at__isnull=True)
        serializer = SaleOrderDetailSerializer(details, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = SaleOrderDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        detail = get_object_or_404(SaleOrderDetail, pk=pk, deleted_at__isnull=True)
        serializer = SaleOrderDetailSerializer(detail, data=request.data)
        if serializer.is_valid():
            serializer.save(updated_at=timezone.now())
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        detail = get_object_or_404(SaleOrderDetail, pk=pk, deleted_at__isnull=True)
        serializer = SaleOrderDetailSerializer(detail, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(updated_at=timezone.now())
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, format=None):
        if pk:
            detail = get_object_or_404(SaleOrderDetail, pk=pk, deleted_at__isnull=True)
            detail.deleted_at = timezone.now()
            detail.save()
            return Response({'message': 'Sale order detail deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

        return self._delete_multiple(request)

    def _delete_multiple(self, request):
        try:
            detail_ids = request.data if isinstance(request.data, list) else request.data.get('ids', [])

            if not detail_ids:
                return Response({'error': 'No se proporcionaron IDs de detalles de orden de venta'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                detail_ids = [int(id) for id in detail_ids]
            except (ValueError, TypeError):
                return Response({'error': 'IDs de detalles no válidos'}, status=status.HTTP_400_BAD_REQUEST)

            existing_details = SaleOrderDetail.objects.filter(id__in=detail_ids, deleted_at__isnull=True)

            if existing_details.count() != len(detail_ids):
                return Response({'error': 'Algunos IDs no existen o ya fueron eliminados'}, status=status.HTTP_400_BAD_REQUEST)

            updated = existing_details.update(deleted_at=timezone.now())

            return Response({
                'message': f'{updated} detalles de orden de venta eliminados exitosamente',
                'deleted_count': updated
            }, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response({'error': f'Error al eliminar detalles: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)