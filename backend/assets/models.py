from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from mptt.models import MPTTModel, TreeForeignKey
from campagne.models import Campagna
from elementtypes.models import ElementType

class StrutturaTemplate(models.Model):
    nome = models.CharField("Nome Template", max_length=255)
    descrizione = models.TextField("Descrizione", blank=True)
    campagna = models.ForeignKey(Campagna, on_delete=models.CASCADE, related_name='templates_struttura', null=True, blank=True)
    cloned_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='clones')
    history = HistoricalRecords()

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Template di Struttura"
        verbose_name_plural = "Template di Struttura"
        unique_together = ('nome', 'campagna')

class NodoTemplate(MPTTModel):
    template = models.ForeignKey(StrutturaTemplate, on_delete=models.CASCADE, related_name='nodi_template')
    element_type = models.ForeignKey(ElementType, on_delete=models.CASCADE)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    campagna = models.ForeignKey(Campagna, on_delete=models.CASCADE, related_name='+', null=True, blank=True)
    history = HistoricalRecords()

    class MPTTMeta:
        order_insertion_by = ['id']

    def save(self, *args, **kwargs):
        if self.template and self.campagna is None:
            self.campagna = self.template.campagna
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.template.nome} - {self.element_type.nome}"

    class Meta:
        verbose_name = "Nodo di Template"
        verbose_name_plural = "Nodi di Template"
        unique_together = ('template', 'element_type', 'parent')

class Asset(models.Model):
    STATUS_CHOICES = [('in_produzione', 'In Produzione'), ('in_sviluppo', 'In Sviluppo'), ('dismesso', 'Dismesso')]
    nome = models.CharField("Nome Asset", max_length=255)
    descrizione = models.TextField("Descrizione", blank=True)
    cmdb = models.CharField("ID CMDB", max_length=100, blank=True)
    utente_responsabile = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='asset_responsabile')
    responsabile_applicativo = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='asset_applicativo')
    legal_entity = models.CharField("Legal Entity", max_length=100, blank=True)
    status = models.CharField("Stato", max_length=20, choices=STATUS_CHOICES, default='in_sviluppo')
    template_da_applicare = models.ForeignKey(StrutturaTemplate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Template di Struttura")
    campagna = models.ForeignKey(Campagna, on_delete=models.CASCADE, related_name='assets', null=True, blank=True)
    cloned_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='clones')
    history = HistoricalRecords()

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if (is_new or not self.nodi_struttura.exists()) and self.template_da_applicare:
            self._applica_struttura_da_template()

    def _applica_struttura_da_template(self):
        self.nodi_struttura.all().delete()
        node_map = {}
        for nodo_template in self.template_da_applicare.nodi_template.all().order_by('level'):
            parent_nodo_struttura = node_map.get(nodo_template.parent_id) if nodo_template.parent_id else None
            nuovo_nodo = NodoStruttura.objects.create(
                asset=self, element_type=nodo_template.element_type, parent=parent_nodo_struttura
            )
            node_map[nodo_template.id] = nuovo_nodo

    class Meta:
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
        unique_together = ('nome', 'campagna')

class NodoStruttura(MPTTModel):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='nodi_struttura')
    element_type = models.ForeignKey(ElementType, on_delete=models.CASCADE, related_name='nodi_istanziati')
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    nome_specifico = models.CharField("Nome Specifico", max_length=255, blank=True)
    campagna = models.ForeignKey(Campagna, on_delete=models.CASCADE, related_name='+', null=True, blank=True)
    history = HistoricalRecords()

    class MPTTMeta:
        order_insertion_by = ['id']

    def save(self, *args, **kwargs):
        if self.asset and self.campagna is None:
            self.campagna = self.asset.campagna
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome_specifico or self.element_type.nome

    class Meta:
        verbose_name = "Nodo di Struttura"
        verbose_name_plural = "Nodi di Struttura"
        unique_together = ('asset', 'element_type', 'parent')