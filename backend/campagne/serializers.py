from rest_framework import serializers
from .models import Campagna

class CampagnaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campagna
        fields = '__all__'