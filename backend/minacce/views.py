from rest_framework import viewsets
from .models import Minaccia
from .serializers import MinacciaSerializer

class MinacciaViewSet(viewsets.ModelViewSet):
    queryset = Minaccia.objects.all()
    serializer_class = MinacciaSerializer
    filterset_fields = ['campagna', 'scenario']