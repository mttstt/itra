from rest_framework import serializers
from .models import Controllo

class ControlloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Controllo
        fields = '__all__'
        read_only_fields = ('peso_controllo',)