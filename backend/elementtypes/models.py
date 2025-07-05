from django.db import models
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords
from campagne.models import Campagna
from minacce.models import Minaccia
from .managers import ElementTypeManager # Importa il manager personalizzato

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

            # Vincolo 1: La matrice deve avere almeno una riga (minaccia associata).
            if not self.minacce.exists():
                raise ValidationError({
                    'is_enabled': "L'ElementType non può essere abilitato perché non ha minacce associate (righe della matrice)."
                })

            # Vincolo 2: La matrice deve avere almeno una colonna (controllo assegnato).
            if not self.controls_assigned_to_elementtype.exists():
                raise ValidationError({
                    'is_enabled': "L'ElementType non può essere abilitato perché non ha controlli assegnati (colonne della matrice)."
                })

            # Vincolo 3: Non ci devono essere righe vuote (ogni minaccia deve avere almeno un controllo nella matrice).
            assigned_threats = self.minacce.all()
            threats_with_values_ids = set(self.valori_matrice.values_list('minaccia_id', flat=True))
            
            threats_without_values = [
                f'"{threat.descrizione}"' for threat in assigned_threats
                if threat.id not in threats_with_values_ids
            ]

            if threats_without_values:
                error_message = (
                    "L'ElementType non può essere abilitato perché le seguenti minacce (righe) "
                    "non hanno nessun controllo associato nella matrice: "
                    f"{', '.join(threats_without_values)}."
                )
                raise ValidationError({'is_enabled': error_message})

    def get_dimensione_matrice_display(self):
        """
        Calcola e restituisce una stringa che rappresenta la dimensione della matrice
        (Minacce x Controlli). Gestisce sia i tipi base che quelli derivati.
        Per una performance ottimale, il chiamante dovrebbe pre-caricare le relazioni
        con prefetch_related.
        """
        if self.is_base:
            num_minacce = self.minacce.count()
            num_controlli = self.controls_assigned_to_elementtype.count()
            return f"{num_minacce} x {num_controlli}" if num_minacce or num_controlli else "N/D"
        else:
            # Per i tipi derivati, aggrega le minacce e i controlli dai componenti.
            # Questo si basa sui dati pre-caricati per l'efficienza.
            components = self.component_element_types.all()
            if not components:
                return "N/D (derivato)"
            
            aggregated_minacce_ids = set().union(*(c.minacce.values_list('id', flat=True) for c in components))
            aggregated_controlli_ids = set().union(*(c.controls_assigned_to_elementtype.values_list('id', flat=True) for c in components))
            return f"{len(aggregated_minacce_ids)} x {len(aggregated_controlli_ids)} (A)"

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