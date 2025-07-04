from rest_framework import viewsets
from .models import ElementType, ValoreElementType
from .serializers import ElementTypeSerializer, ValoreElementTypeSerializer

class ElementTypeViewSet(viewsets.ModelViewSet):
    queryset = ElementType.objects.all()
    serializer_class = ElementTypeSerializer
    filterset_fields = ['campagna', 'is_base', 'is_enabled']

class ValoreElementTypeViewSet(viewsets.ModelViewSet):
    queryset = ValoreElementType.objects.all()
    serializer_class = ValoreElementTypeSerializer
    filterset_fields = ['elementtype', 'minaccia', 'controllo']