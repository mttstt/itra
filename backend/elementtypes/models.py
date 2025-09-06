from django.db import models
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords
from campagne.models import Campagna
from minacce.models import Minaccia
from controlli.models import Controllo
from .managers import ElementTypeManager # Importa il manager personalizzato
import logging

class ElementType(models.Model):
    nome = models.CharField("Nome", max_length=255)
    descrizione = models.TextField("Descrizione", blank=True)
    is_base = models.BooleanField("Di Base", default=True, editable=False, help_text="Indica se l'elemento è di base o derivato da altri.")
    is_enabled = models.BooleanField("Abilitato", default=False, help_text="Indica se l'elemento è utilizzabile nelle catene tecnologiche.")
    
    minacce = models.ManyToManyField(
        'minacce.Minaccia', 
        blank=True,
        verbose_name="Minacce Applicabili"
    )
    
    component_element_types = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        verbose_name="Elementi componenti (per tipi derivati)",
        help_text="Selezionare uno o più Element Type per creare un tipo derivato. Lasciare vuoto per un tipo base."
    )

    campagna = models.ForeignKey(
        Campagna,
        on_delete=models.CASCADE,
        related_name='elementtypes',
        null=True,
        blank=True
    )
    cloned_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clones',
        verbose_name="Clonato da (Master)",
        help_text="Riferimento all'ElementType master da cui questo è stato clonato."
    )
    history = HistoricalRecords()
    objects = ElementTypeManager()

    def __str__(self):
        return self.nome

    def clean(self):
        """
        Applica logiche di validazione prima di salvare il modello.
        Questa validazione viene eseguita automaticamente nel pannello di amministrazione.
        """
        super().clean()
        # La validazione si applica solo agli ElementType di base che si sta cercando di abilitare.
        if self.is_enabled and self.is_base:
            if not self.pk:
                raise ValidationError({
                    'is_enabled': "Un nuovo ElementType deve essere salvato prima di poter essere abilitato, "
                                  "per poter configurare la matrice di rischio."
                })

            # Vincolo 1: L'ElementType deve avere almeno una minaccia associata.
            if not self.minacce.exists():
                raise ValidationError({
                    'is_enabled': "L'ElementType non può essere abilitato perché non ha minacce associate (righe della matrice)."
                })

            # Vincolo 2 (Nuovo): Ogni minaccia associata deve avere almeno 4 controlli (2 preventive e 2 detective).
            for minaccia in self.minacce.all():
                preventive_controls_count = self.valori_matrice.filter(
                    minaccia=minaccia,
                    controllo__categoria_controllo='preventive'
                ).count()
                detective_controls_count = self.valori_matrice.filter(
                    minaccia=minaccia,
                    controllo__categoria_controllo='detective'
                ).count()

                if preventive_controls_count < 2 or detective_controls_count < 2:
                    self.is_enabled = False
                    break
            
            if not self.is_enabled:
                return

            # Vincolo 3 (Modificato): Tutti i controlli dell'ElementType devono essere associati ad almeno una minaccia.
            # E ogni minaccia deve avere almeno un controllo nella matrice.
            assigned_controls_ids = self.valori_matrice.values_list('controllo_id', flat=True).distinct()
            all_controls_for_elementtype = self.controls_assigned_to_elementtype.all()

            controls_not_in_matrix = [
                f'"{control.nome}"' for control in all_controls_for_elementtype
                if control.id not in assigned_controls_ids
            ]

            if controls_not_in_matrix:
                error_message = (
                    "L'ElementType non può essere abilitato perché i seguenti controlli assegnati "
                    "non sono presenti nella matrice di rischio (non associati a nessuna minaccia): "
                    f"{', '.join(controls_not_in_matrix)}."
                )
                raise ValidationError({'is_enabled': error_message})

    def get_dimensione_matrice_display(self):
        """
        Calcola e restituisce una stringa che rappresenta la dimensione della matrice
        (Minacce x Controlli). Gestisce sia i tipi base che quelli derivati.
        Per una performance ottimale, il chiamante dovrebbe pre-caricare le relazioni
        con prefetch_related.
        """
        if self.nome == "root":
            # For the special 'root' ElementType, calculate dimension from aggregated values
            num_minacce = self.valori_matrice.values('minaccia').distinct().count()
            num_controlli = self.valori_matrice.values('controllo').distinct().count()
            return f"{num_minacce} x {num_controlli}" if num_minacce or num_controlli else "N/D (Root Aggregato)"
        elif self.is_base:
            # Per i tipi base, i conteggi sono diretti.
            num_minacce = self.minacce.count()
            num_controlli = self.controls_assigned_to_elementtype.count()
            return f"{num_minacce} x {num_controlli}" if num_minacce or num_controlli else "N/D"
        else:
            # Per i tipi derivati, usa i metodi ricorsivi per ottenere i conteggi corretti.
            if not self.component_element_types.exists():
                return "N/D (derivato)"
            
            num_minacce = self.get_all_minacce().count()
            num_controlli = self.get_all_controlli().count()
            return f"{num_minacce} x {num_controlli} (A)"

    def get_all_controlli(self):
        """
        Restituisce un queryset di tutti i controlli associati, gestendo la derivazione ricorsiva.
        """
        if self.is_base:
            return self.controls_assigned_to_elementtype.all()
        
        all_control_ids = set()
        for component in self.component_element_types.all():
            all_control_ids.update(component.get_all_controlli().values_list('id', flat=True))
            
        return Controllo.objects.filter(id__in=all_control_ids)

    def get_all_minacce(self):
        """
        Restituisce un queryset di tutte le minacce applicabili, gestendo la derivazione ricorsiva.
        """
        if self.is_base:
            return self.minacce.all()
        
        all_minaccia_ids = set()
        for component in self.component_element_types.all():
            all_minaccia_ids.update(component.get_all_minacce().values_list('id', flat=True))
            
        return Minaccia.objects.filter(id__in=all_minaccia_ids)

    def get_valore_matrice(self, minaccia, controllo):
        """
        Restituisce il valore di una cella della matrice, gestendo la ricorsione per i tipi derivati.
        """
        if self.is_base:
            valore_obj = self.valori_matrice.filter(minaccia=minaccia, controllo=controllo).first()
            return valore_obj.valore if valore_obj else 0.0
        
        # Per i tipi derivati, calcola il MAX dei valori dei componenti.
        max_valore = 0.0
        for component in self.component_element_types.all():
            valore_componente = component.get_valore_matrice(minaccia, controllo)
            if valore_componente > max_valore:
                max_valore = valore_componente
        return max_valore

    @classmethod
    def get_aggregated_matrix_values(cls, element_types):
        """
        Aggregates matrix values from a list of ElementType instances.
        For each (minaccia, controllo) pair, takes the maximum value.
        Returns a dictionary: {(minaccia_id, controllo_id): max_valore}
        """
        logging.info(f"--- Aggregating matrix values for ElementTypes: {[et.nome for et in element_types]} ---")
        aggregated_values = {}
        # Pre-fetch all ValoreElementType for the given element_types to avoid N+1 queries
        valori_to_process = ValoreElementType.objects.filter(elementtype__in=element_types).select_related('minaccia', 'controllo')

        for valore_obj in valori_to_process:
            key = (valore_obj.minaccia_id, valore_obj.controllo_id)
            logging.info(f"  Processing ValoreElementType: ET={valore_obj.elementtype.nome}, Minaccia={valore_obj.minaccia.descrizione}, Controllo={valore_obj.controllo.nome}, Valore={valore_obj.valore}")
            aggregated_values[key] = max(aggregated_values.get(key, 0.0), valore_obj.valore)
            logging.info(f"  Current aggregated value for ({valore_obj.minaccia.descrizione}, {valore_obj.controllo.nome}): {aggregated_values[key]}")
        logging.info(f"Final aggregated values: {aggregated_values}")
        return aggregated_values

    class Meta:
        verbose_name = "Element Type"
        verbose_name_plural = "Element Types"
        unique_together = ('nome', 'campagna')

class ValoreElementType(models.Model):
    elementtype = models.ForeignKey(ElementType, on_delete=models.CASCADE, related_name='valori_matrice')
    minaccia = models.ForeignKey('minacce.Minaccia', on_delete=models.CASCADE)
    controllo = models.ForeignKey('controlli.Controllo', on_delete=models.CASCADE)
    valore = models.FloatField("Valore")

    class Meta:
        unique_together = ('elementtype', 'minaccia', 'controllo')
        verbose_name = 'Valore Matrice Element Type'
        verbose_name_plural = 'Valori Matrice Element Type'