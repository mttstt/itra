from rest_framework import viewsets
from .models import Controllo
from .serializers import ControlloSerializer

class ControlloViewSet(viewsets.ModelViewSet):
    queryset = Controllo.objects.all()
    serializer_class = ControlloSerializer
    filterset_fields = ['campagna', 'tipologia_controllo', 'categoria_controllo', 'elementtype']
