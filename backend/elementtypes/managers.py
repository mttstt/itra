from django.db import models, transaction
from minacce.models import Minaccia
import logging
logger = logging.getLogger(__name__)
from controlli.models import Controllo


class ElementTypeManager(models.Manager):
    @transaction.atomic
    def aggregazione(self, parent_element_type, child_element_types):
        """
        Aggrega le matrici degli element type figli e popola la matrice
        dell'element type padre.
        """
        from .models import ValoreElementType
        
        # --- LOGICA MODIFICATA ---
        # La lista delle sorgenti per l'aggregazione ora include sia il padre
        # (con la sua eventuale matrice preesistente) sia tutti i suoi figli.
        all_sources = [parent_element_type] + list(child_element_types)
        
        # Colonne (Controlli) -> Unione
        controlli_qs = Controllo.objects.none()
        for et in all_sources:
            controlli_qs = controlli_qs | et.controls_assigned_to_elementtype.all()

     
        controlli_set = set(controlli_qs)

        # Righe (Minacce) -> Unione
        minacce_qs = Minaccia.objects.none()
        for et in all_sources:
            minacce_qs = minacce_qs | et.minacce.all()
        minacce_set = set(minacce_qs)

        # Pulisce la vecchia matrice e imposta le nuove minacce
        parent_element_type.valori_matrice.all().delete()
        parent_element_type.minacce.set(list(minacce_set))

        
        # Calcolo valori aggregati (MAX)
        valori_da_creare = []
        for minaccia in minacce_set:
            for controllo in controlli_set:
                max_valore = 0.0
                # Itera su tutte le sorgenti (padre + figli) per trovare il valore massimo.
                for et_figlio in all_sources:
                    valore_obj = et_figlio.valori_matrice.filter(minaccia=minaccia, controllo=controllo).first()
                    if valore_obj and valore_obj.valore > max_valore:
                        max_valore = valore_obj.valore
                
                if max_valore > 0:
                    valori_da_creare.append(ValoreElementType(elementtype=parent_element_type, minaccia=minaccia, controllo=controllo, valore=max_valore))
        
        ValoreElementType.objects.bulk_create(valori_da_creare)