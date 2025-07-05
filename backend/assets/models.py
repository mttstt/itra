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

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        template_to_clone_from = self.cloned_from
        super().save(*args, **kwargs)
        if is_new and template_to_clone_from:
            self._clona_nodi_da_template(template_to_clone_from)

    def _clona_nodi_da_template(self, source_template):
        """Clona l'albero di NodoTemplate da un template sorgente."""
        self.nodi_template.all().delete()
        node_map = {}
        for source_node in source_template.nodi_template.all().order_by('level'):
            parent_nodo_template = node_map.get(source_node.parent_id) if source_node.parent_id else None
            nuovo_nodo = NodoTemplate.objects.create(template=self, element_type=source_node.element_type, parent=parent_nodo_template)
            node_map[source_node.id] = nuovo_nodo

    class Meta:
        verbose_name = "Template di Struttura"
        verbose_name_plural = "Template di Struttura"
        unique_together = ('nome', 'campagna')

    def get_dimensione_matrice_display(self):
        """Restituisce la dimensione della matrice del nodo radice del template."""
        # Itera sulla cache prefetched per efficienza
        root_node = next((node for node in self.nodi_template.all() if node.level == 0), None)
        if root_node:
            return root_node.get_dimensione_matrice_display()
        return "N/D"

class NodoTemplate(MPTTModel):
    template = models.ForeignKey(StrutturaTemplate, on_delete=models.CASCADE, related_name='nodi_template')
    element_type = models.ForeignKey(ElementType, on_delete=models.CASCADE)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    campagna = models.ForeignKey(Campagna, on_delete=models.CASCADE, related_name='+', null=True, blank=True)
    history = HistoricalRecords(excluded_fields=['lft', 'rght', 'tree_id', 'level'])

    class MPTTMeta:
        order_insertion_by = ['id']

    def save(self, *args, **kwargs):
        if self.template and self.campagna is None:
            self.campagna = self.template.campagna
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.template.nome} - {self.element_type.nome}"

    def get_dimensione_matrice_display(self):
        """Restituisce la dimensione della matrice dell'ElementType associato."""
        if self.element_type:
            return self.element_type.get_dimensione_matrice_display()
        return "N/D"

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
        # Cattura lo stato prima del salvataggio, poiché i campi potrebbero cambiare
        template_to_apply = self.template_da_applicare
        asset_to_clone_from = self.cloned_from

        super().save(*args, **kwargs)

        # Applica la struttura solo alla creazione o se la struttura non esiste
        if is_new or not self.nodi_struttura.exists():
            if template_to_apply:
                self._applica_struttura_da_template(template_to_apply)
            elif asset_to_clone_from:
                self._clona_struttura_da_asset(asset_to_clone_from)

    def _applica_struttura_da_template(self, template):
        self.nodi_struttura.all().delete()
        node_map = {}
        for nodo_template in template.nodi_template.all().order_by('level'):
            parent_nodo_struttura = node_map.get(nodo_template.parent_id) if nodo_template.parent_id else None
            nuovo_nodo = NodoStruttura.objects.create(
                asset=self, element_type=nodo_template.element_type, parent=parent_nodo_struttura
            )
            node_map[nodo_template.id] = nuovo_nodo

    def _clona_struttura_da_asset(self, source_asset):
        """Clona l'albero di NodoStruttura da un asset sorgente."""
        self.nodi_struttura.all().delete()
        node_map = {}
        for source_node in source_asset.nodi_struttura.all().order_by('level'):
            parent_nodo_struttura = node_map.get(source_node.parent_id) if source_node.parent_id else None
            nuovo_nodo = NodoStruttura.objects.create(asset=self, element_type=source_node.element_type, parent=parent_nodo_struttura, nome_specifico=source_node.nome_specifico)
            node_map[source_node.id] = nuovo_nodo

    def get_dimensione_matrice_display(self):
        """Restituisce la dimensione della matrice del nodo radice dell'asset."""
        # Itera sulla cache prefetched per efficienza
        root_node = next((node for node in self.nodi_struttura.all() if node.level == 0), None)
        if root_node:
            return root_node.get_dimensione_matrice_display()
        return "N/D"

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
    history = HistoricalRecords(excluded_fields=['lft', 'rght', 'tree_id', 'level'])

    class MPTTMeta:
        order_insertion_by = ['id']

    def save(self, *args, **kwargs):
        if self.asset and self.campagna is None:
            self.campagna = self.asset.campagna
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome_specifico or self.element_type.nome

    def get_dimensione_matrice_display(self):
        """Restituisce la dimensione della matrice dell'ElementType associato."""
        if self.element_type:
            return self.element_type.get_dimensione_matrice_display()
        return "N/D"

    class Meta:
        verbose_name = "Nodo di Struttura"
        verbose_name_plural = "Nodi di Struttura"
        unique_together = ('asset', 'element_type', 'parent')