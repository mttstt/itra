from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from mptt.models import MPTTModel, TreeForeignKey
from campagne.models import Campagna
from elementtypes.models import ElementType
import logging

from django.core.exceptions import ValidationError
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
        
        template_to_apply = self.template_da_applicare
        asset_to_clone_from = self.cloned_from

        if not is_new:
            old_nome = Asset.objects.get(pk=self.pk).nome
            if old_nome != self.nome:
                logging.info(f"Asset name changed from '{old_nome}' to '{self.nome}'. Updating root node name.")
                if self.nodi_struttura.filter(level=0).exists():
                    self.nodi_struttura.filter(level=0).update(nome_specifico=self.nome)

        super().save(*args, **kwargs)

        if is_new:
            logging.info(f"New asset '{self.nome}': creating structure.")
            
            if template_to_apply:
                self._applica_struttura_da_template(template_to_apply)
            elif asset_to_clone_from:
                self._clona_struttura_da_asset(asset_to_clone_from)
                if self.nodi_struttura.filter(level=0).exists():
                    self.nodi_struttura.filter(level=0).update(nome_specifico=self.nome)
            else:
                self._crea_nodo_radice()

    def _crea_nodo_radice(self):
        """Crea un nodo radice per un nuovo asset."""
        logging.info(f"New asset '{self.nome}' without template or clone: creating root node.")
        try:
            if self.campagna:
                element_type, created = ElementType.objects.update_or_create(
                    nome="root",
                    campagna=self.campagna,
                    defaults={'descrizione': 'Elemento di tipo root per la campagna', 'is_base': False}
                )
            else:
                element_type, created = ElementType.objects.update_or_create(
                    nome="root",
                    campagna=None,
                    defaults={'descrizione': 'Elemento di tipo root master', 'is_base': False}
                )

            NodoStruttura.objects.create(
                asset=self,
                element_type=element_type,
                nome_specifico=self.nome
            )
            logging.info(f"Root node created for asset '{self.nome}'.")
        except Exception as e:
            logging.error(f"Error creating root node for asset '{self.nome}': {e}")

    def _applica_struttura_da_template(self, template):
        self.nodi_struttura.all().delete()
        node_map = {}
        for nodo_template in template.nodi_template.all().order_by('level'):
            parent_nodo_struttura = node_map.get(nodo_template.parent_id) if nodo_template.parent_id else None
            nuovo_nodo = NodoStruttura.objects.create(
                asset=self, element_type=nodo_template.element_type, parent=parent_nodo_struttura
            )
            node_map[nodo_template.id] = nuovo_nodo
        # Dopo aver creato i nodi dal template, impostiamo il nome del primo nodo uguale al nome dell'asset
        if self.nodi_struttura.filter(level=0).exists():
            self.nodi_struttura.filter(level=0).update(nome_specifico=self.nome)





    def _clona_struttura_da_asset(self, source_asset):
        logging.info(f"Clonazione struttura dall'asset {source_asset.nome} all'asset {self.nome}")
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
        if root_node and root_node.element_type: # Ensure element_type exists
            return root_node.element_type.get_dimensione_matrice_display()
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
        # Validazione: non si possono aggiungere figli a un nodo di base
        if self.parent and self.parent.element_type.is_base:
            raise ValidationError(f"Non è possibile aggiungere un nodo figlio a '{self.parent}', perché il suo tipo '{self.parent.element_type.nome}' è di base e non può essere derivato.")

        is_new = self.pk is None
        if self.asset and self.campagna is None:
            self.campagna = self.asset.campagna
        
        super().save(*args, **kwargs)

        # Se è un nuovo nodo non di base, crea automaticamente i suoi componenti
        if is_new and not self.element_type.is_base:
            for component_et in self.element_type.component_element_types.all():
                NodoStruttura.objects.create(
                    asset=self.asset,
                    element_type=component_et,
                    parent=self,
                    nome_specifico=component_et.nome  # Opzionale: imposta un nome di default
                )
        
        # Trigger aggregation of the root node's matrix
        if self.is_root_node():
            self.aggregate_root_node_matrix()
        else:
            root_node = self.get_root()
            if root_node: # Ensure root_node exists
                root_node.aggregate_root_node_matrix()

    def __str__(self):
        return self.nome_specifico or self.element_type.nome

    def get_dimensione_matrice_display(self):
        """Restituisce la dimensione della matrice dell'ElementType associato."""
        if self.element_type:
            return self.element_type.get_dimensione_matrice_display()
        return "N/D"

    def is_root_node(self):
        return self.level == 0

    def aggregate_root_node_matrix(self):
        from elementtypes.models import ElementType, ValoreElementType
        root_element_type = self.element_type

        if not root_element_type:
            logging.warning(f"Root node {self.pk} has no element type. Cannot aggregate matrix.")
            return
        """Aggrega la matrice del nodo radice basata sui figli."""
        logging.info(f"--- Aggregating matrix for root node: {self.nome_specifico or self.element_type.nome} (Asset: {self.asset.nome}) ---")
        children = NodoStruttura.objects.filter(parent=self)
        if children.exists():
            from elementtypes.models import ElementType, ValoreElementType
            
            logging.info(f"Child nodes found: {children.count()}")
            for child in children:
                logging.info(f"  Child: {child.nome_specifico or child.element_type.nome}, ElementType: {child.element_type.nome}, Dimension: {child.element_type.get_dimensione_matrice_display()}")

            # Ensure element_type and its related values are prefetched for children
            children = children.select_related('element_type').prefetch_related('element_type__valori_matrice')
            element_types = [child.element_type for child in children]
            
            aggregated_values = ElementType.get_aggregated_matrix_values(element_types)
            logging.info(f"Aggregated values from children: {aggregated_values}")

            # Clear existing values for the root ElementType and create new ones.
            ValoreElementType.objects.filter(elementtype=root_element_type).delete()
            logging.info(f"Cleared existing matrix values for root ElementType: {root_element_type.nome}")

            new_valori = []
            for (minaccia_id, controllo_id), valore in aggregated_values.items():
                new_valori.append(
                    ValoreElementType(
                        elementtype=root_element_type,
                        minaccia_id=minaccia_id,
                        controllo_id=controllo_id,
                        valore=valore
                    )
                )
            ValoreElementType.objects.bulk_create(new_valori)
            logging.info(f"Bulk created {len(new_valori)} new matrix values for root ElementType.")
            
            # Refresh the root element type to get the updated dimension
            root_element_type.refresh_from_db()
            logging.info(f"New dimension of root ElementType ({root_element_type.nome}): {root_element_type.get_dimensione_matrice_display()}")
        else:
            logging.info(f"No children found for root node: {self.nome_specifico or self.element_type.nome}. Matrix will be N/D.")
            # If no children, clear the matrix for the root ElementType
            ValoreElementType.objects.filter(elementtype=root_element_type).delete()
            root_element_type.refresh_from_db()
            logging.info(f"Root ElementType ({root_element_type.nome}) matrix cleared. Dimension: {root_element_type.get_dimensione_matrice_display()}")
    