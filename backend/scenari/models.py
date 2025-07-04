from django.db import models
from simple_history.models import HistoricalRecords
from campagne.models import Campagna

class Scenario(models.Model):
    descrizione = models.CharField("Descrizione", max_length=255)
    campagna = models.ForeignKey(
        Campagna,
        on_delete=models.CASCADE, # Modifica per coerenza
        related_name='scenari',
        null=True,
        blank=True
    )
    history = HistoricalRecords()

    def __str__(self):
        return self.descrizione

    class Meta:
        verbose_name = "Scenario"
        verbose_name_plural = "Scenari"
        unique_together = ('descrizione', 'campagna')