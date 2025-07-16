from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from campagne.models import Campagna

class Controllo(models.Model):
    TIPOLOGIA_CHOICES = [
        ('Documentale', 'Documentale'),
        ('Tecnologico', 'Tecnologico'),
        ('Processo', 'Processo'),
        ('Misurazione base', 'Misurazione base'),
        ('Misurazione intermedia', 'Misurazione intermedia'),
        ('Misurazione avanzata', 'Misurazione avanzata'),
    ]
    PESO_MAPPING = {
        'Documentale': 0.4,
        'Tecnologico': 0.5,
        'Processo': 0.6,
        'Misurazione base': 0.8,
        'Misurazione intermedia': 0.9,
        'Misurazione avanzata': 1.0,
    }
    CATEGORIA_CHOICES = [
        ('preventive', 'Preventive'),
        ('detective', 'Detective'),
    ]

    nome = models.CharField("Nome", max_length=255)
    descrizione = models.TextField("Descrizione")
    tipologia_controllo = models.CharField("Tipologia", max_length=50, choices=TIPOLOGIA_CHOICES)
    peso_controllo = models.FloatField("Peso", editable=False)
    categoria_controllo = models.CharField("Categoria", max_length=20, choices=CATEGORIA_CHOICES)
    macroambito = models.CharField("Macroambito di controllo", max_length=255, blank=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Owner del controllo"
    )
    riferimento_best_practies = models.CharField("Riferimento Best Practices", max_length=255, blank=True)
    riferimento_normativo = models.CharField("Riferimento Normativo", max_length=255, blank=True)
    riferimento_processo_ITIL = models.CharField("Riferimento Processo ITIL", max_length=255, blank=True)
    elementtype = models.ForeignKey(
        'elementtypes.ElementType',
        on_delete=models.SET_NULL,
        null=True, blank=True, # Permette controlli non ancora assegnati
        related_name='controls_assigned_to_elementtype', # Changed to resolve clash with ElementType.controlli
        verbose_name="Element Type"
    )
    campagna = models.ForeignKey(
        Campagna,
        on_delete=models.CASCADE, # Modifica per coerenza
        related_name='controlli',
        null=True,
        blank=True
    )
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        self.peso_controllo = self.PESO_MAPPING.get(self.tipologia_controllo, 0.0)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Controllo"
        verbose_name_plural = "Controlli"
        unique_together = ('nome', 'campagna')
