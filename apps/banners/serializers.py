from rest_framework import serializers
from apps.banners.models import Banner

class BannerSerializer(serializers.ModelSerializer):
  status = serializers.IntegerField()
  
  class Meta:
    model = Banner
    fields = '__all__'
    read_only_fields = ('updated_at', 'created_at', 'deleted_at')