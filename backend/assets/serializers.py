from rest_framework import serializers
from .models import Asset, NodoStruttura, StrutturaTemplate, NodoTemplate

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = '__all__'

class NodoStrutturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodoStruttura
        fields = '__all__'

class StrutturaTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrutturaTemplate
        fields = '__all__'