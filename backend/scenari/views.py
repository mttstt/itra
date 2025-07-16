from rest_framework import viewsets
from .models import Scenario
from .serializers import ScenarioSerializer

class ScenarioViewSet(viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
    filterset_fields = ['campagna']