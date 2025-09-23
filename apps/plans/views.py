import traceback
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, FormParser
from django.utils import timezone
from apps.plans.models import Plan
from apps.plans.serializers import PlanSerializer

class PlanAPIView(APIView):
  permission_classes = [IsAuthenticated]
  parser_classes = [JSONParser, FormParser]

  def get(self, request, pk=None, format=None):
    if pk:
      plan = get_object_or_404(Plan, pk=pk, deleted_at__isnull=True)
      serializer = PlanSerializer(plan)
      return Response(serializer.data, status=status.HTTP_200_OK)

    plans = Plan.objects.filter(deleted_at__isnull=True)
    serializer = PlanSerializer(plans, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

  def post(self, request, format=None):
    serializer = PlanSerializer(data=request.data)
    if serializer.is_valid():
      serializer.save(created_by=request.user)
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def patch(self, request, pk, format=None):
    plan = get_object_or_404(Plan, pk=pk, deleted_at__isnull=True)
    serializer = PlanSerializer(plan, data=request.data, partial=True)
    if serializer.is_valid():
      serializer.save(updated_by=request.user, updated_at=timezone.now())
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def delete(self, request, pk=None, format=None):
    if pk:
      plan = get_object_or_404(Plan, pk=pk, deleted_at__isnull=True)
      plan.deleted_at = timezone.now()
      plan.updated_by = request.user
      plan.save()
      return Response({'message': 'Plan deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    return Response({'error': 'No se proporcionó un ID'}, status=status.HTTP_400_BAD_REQUEST)