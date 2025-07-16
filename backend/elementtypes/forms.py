from django import forms
from django.contrib import admin
from .models import ElementType
from controlli.models import Controllo

class ElementTypeForm(forms.ModelForm):
    # Definisce il campo personalizzato che non esiste sul modello.
    # Questo lo rende noto al ModelAdmin, risolvendo il FieldError.
    assigned_controls = forms.ModelMultipleChoiceField(
        queryset=Controllo.objects.none(), # Il queryset verrà popolato dinamicamente nell'admin.
        required=False,
        label="",
        widget=admin.widgets.FilteredSelectMultiple("Controlli", is_stacked=False)
    )

    class Meta:
        model = ElementType
        fields = '__all__'