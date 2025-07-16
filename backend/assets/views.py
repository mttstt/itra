from rest_framework import viewsets
from .models import Asset, NodoStruttura, StrutturaTemplate
from .serializers import AssetSerializer, NodoStrutturaSerializer, StrutturaTemplateSerializer

class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

class NodoStrutturaViewSet(viewsets.ModelViewSet):
    queryset = NodoStruttura.objects.all()
    serializer_class = NodoStrutturaSerializer

class StrutturaTemplateViewSet(viewsets.ModelViewSet):
    queryset = StrutturaTemplate.objects.all()
    serializer_class = StrutturaTemplateSerializer