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
        # Utilizziamo i nuovi metodi ricorsivi per ottenere l'unione corretta.
        
        # Colonne (Controlli) -> Unione ricorsiva
        controlli_set = parent_element_type.get_all_controlli()

        # Righe (Minacce) -> Unione ricorsiva
        minacce_set = parent_element_type.get_all_minacce()

        # Pulisce la vecchia matrice e imposta le nuove minacce
        parent_element_type.valori_matrice.all().delete()
        parent_element_type.minacce.set(minacce_set)

        
        # Calcolo valori aggregati (MAX)
        valori_da_creare = []
        for minaccia in minacce_set:
            for controllo in controlli_set:
                max_valore = 0.0
                # Itera sui componenti figli per trovare il valore massimo in modo ricorsivo.
                for et_figlio in child_element_types:
                    valore_figlio = et_figlio.get_valore_matrice(minaccia, controllo)
                    if valore_figlio > max_valore:
                        max_valore = valore_figlio
                
                if max_valore > 0:
                    valori_da_creare.append(ValoreElementType(elementtype=parent_element_type, minaccia=minaccia, controllo=controllo, valore=max_valore))
        
        ValoreElementType.objects.bulk_create(valori_da_creare)