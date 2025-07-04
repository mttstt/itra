from rest_framework import serializers
from .models import ElementType, ValoreElementType

class ValoreElementTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValoreElementType
        fields = '__all__'

class ElementTypeSerializer(serializers.ModelSerializer):
    # Optionally, include matrix values in the serializer
    valori_matrice = ValoreElementTypeSerializer(many=True, read_only=True)
    matrix_dimension = serializers.SerializerMethodField() # Aggiungi questo campo
    
    class Meta:
        model = ElementType
        fields = '__all__'

    def get_matrix_dimension(self, obj):
        """
        Calcola la dimensione della matrice (Minacce x Controlli) per l'ElementType.
        """
        if not obj.pk: # Per oggetti non ancora salvati
            return "N/A"
        num_minacce = obj.minacce.count()
        num_controlli = obj.valori_matrice.values('controllo').distinct().count()
        if num_minacce == 0 and num_controlli == 0:
            return "N/A"
        return f"{num_minacce} x {num_controlli}"