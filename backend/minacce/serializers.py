from rest_framework import serializers
from .models import Minaccia

class MinacciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Minaccia
        fields = '__all__'