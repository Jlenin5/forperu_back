from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Lateness, EmployeeLatenessSummary
from .serializers import LatenessSerializer, EmployeeLatenessSummarySerializer

# ----- CRUD para registros de tardanza -----
class LatenessListCreateView(generics.ListCreateAPIView):
  queryset = Lateness.objects.all()
  serializer_class = LatenessSerializer
  permission_classes = [IsAuthenticated]

class LatenessDetailView(generics.RetrieveUpdateDestroyAPIView):
  queryset = Lateness.objects.all()
  serializer_class = LatenessSerializer
  permission_classes = [IsAuthenticated]

# ----- Resúmenes por empleado -----
class EmployeeLatenessSummaryListView(generics.ListAPIView):
  queryset = EmployeeLatenessSummary.objects.all()
  serializer_class = EmployeeLatenessSummarySerializer
  permission_classes = [IsAuthenticated]

class EmployeeLatenessSummaryDetailView(generics.RetrieveAPIView):
  queryset = EmployeeLatenessSummary.objects.all()
  serializer_class = EmployeeLatenessSummarySerializer
  permission_classes = [IsAuthenticated]