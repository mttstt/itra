from django.db import models
from simple_history.models import HistoricalRecords
from campagne.models import Campagna
from scenari.models import Scenario

class Minaccia(models.Model):
    descrizione = models.CharField("Descrizione", max_length=255)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, verbose_name="Scenario di riferimento")
    campagna = models.ForeignKey(
        Campagna,
        on_delete=models.CASCADE, # Assicura che la cancellazione della campagna si propaghi
        related_name='minacce',
        null=True,
        blank=True
    )
    history = HistoricalRecords()

    def __str__(self):
        return self.descrizione

    class Meta:
        verbose_name = "Minaccia"
        verbose_name_plural = "Minacce"
        unique_together = ('descrizione', 'campagna')