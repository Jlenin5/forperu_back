import traceback
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, FormParser
from django.utils import timezone
from apps.subscriptions.models import Subscription
from apps.subscriptions.serializers import SubscriptionSerializer

class SubscriptionAPIView(APIView):
  permission_classes = [IsAuthenticated]
  parser_classes = [JSONParser, FormParser]

  def get(self, request, pk=None, format=None):
    if pk:
      subscription = get_object_or_404(Subscription, pk=pk, deleted_at__isnull=True)
      serializer = SubscriptionSerializer(subscription)
      return Response(serializer.data, status=status.HTTP_200_OK)

    subscriptions = Subscription.objects.filter(deleted_at__isnull=True)
    serializer = SubscriptionSerializer(subscriptions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

  def post(self, request, format=None):
    serializer = SubscriptionSerializer(data=request.data)
    if serializer.is_valid():
      serializer.save(created_by=request.user)
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def patch(self, request, pk, format=None):
    subscription = get_object_or_404(Subscription, pk=pk, deleted_at__isnull=True)
    serializer = SubscriptionSerializer(subscription, data=request.data, partial=True)
    if serializer.is_valid():
      serializer.save(updated_by=request.user, updated_at=timezone.now())
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def delete(self, request, pk=None, format=None):
    if pk:
      subscription = get_object_or_404(Subscription, pk=pk, deleted_at__isnull=True)
      subscription.deleted_at = timezone.now()
      subscription.updated_by = request.user
      subscription.save()
      return Response({'message': 'Subscription deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    return Response({'error': 'No se proporcionó un ID'}, status=status.HTTP_400_BAD_REQUEST)