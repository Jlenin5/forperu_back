from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from apps.banners.models import Banner
from apps.banners.serializers import BannerSerializer
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.permissions import AllowAny

class BannerAPIView(APIView):
  permission_classes = [AllowAny]
  parser_classes = [JSONParser, FormParser, MultiPartParser]

  def get(self, request, pk=None, format=None):
    if pk:
      # Detalle de un banner
      banner = get_object_or_404(Banner, pk=pk, deleted_at__isnull=True)
      serializer = BannerSerializer(banner)
      return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Listado de banners
    banners = Banner.objects.filter(deleted_at__isnull=True)
    serializer = BannerSerializer(banners, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)