from django.db import models
from simple_history.models import HistoricalRecords
from django.db import transaction


class Campagna(models.Model):
    """
    Modello per le Campagne di valutazione.
    La creazione di una campagna comporterà la copia di tutti i dati di base.
    """
    STATUS_CHOICES = [
        ('open', 'Aperta'),
        ('close', 'Chiusa'),
    ]

    anno = models.PositiveIntegerField("Anno")
    descrizione = models.CharField("Descrizione", max_length=255)
    data_inizio = models.DateField("Data inizio campagna")
    data_fine = models.DateField("Data fine campagna")

    status = models.CharField("Stato", max_length=10, choices=STATUS_CHOICES, default='open')
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.descrizione} ({self.anno})"

    def save(self, *args, **kwargs):
        """
        Sovrascrive il metodo save per avviare il popolamento automatico
        alla creazione di una nuova campagna.
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            try:
                # Tenta di recuperare la campagna appena salvata per assicurare che esista
                # prima di chiamare popola_from_master.
                self.__class__.objects.get(pk=self.pk)
                self.popola_from_master()
            except self.__class__.DoesNotExist:
                pass  # Gestisci il caso in cui, per qualche motivo, non viene trovata (molto improbabile)

    @transaction.atomic
    def popola_from_master(self):
        """
        Popola questa campagna (che si presume vuota) clonando tutti i dati
        di anagrafica "master" (quelli con campagna=NULL).
        """
 
        from controlli.models import Controllo
        from elementtypes.models import ElementType, ValoreElementType, Minaccia
        from minacce.models import Minaccia
        from assets.models import Asset, NodoStruttura, StrutturaTemplate, NodoTemplate
        from scenari.models import Scenario

        new_campaign = self

        # Dizionari per mappare i vecchi ID ai nuovi oggetti clonati
        scenario_map, minaccia_map, elementtype_map, controllo_map, template_map = {}, {}, {}, {}, {}
        # 1. Clona Scenari (nessuna dipendenza da altri modelli clonati)
        for obj in Scenario.objects.filter(campagna__isnull=True):
            old_id = obj.id
            obj.id = None
            obj._state.adding = True
            obj.campagna = new_campaign
            obj.save()
            scenario_map[old_id] = obj

        # 2. Clona Minacce (dipendono da Scenari)
        for obj in Minaccia.objects.filter(campagna__isnull=True):
            old_id = obj.id
            obj.id = None
            obj._state.adding = True
            obj.campagna = new_campaign
            if obj.scenario_id:
                obj.scenario = scenario_map.get(obj.scenario_id)
            obj.save()
            minaccia_map[old_id] = obj

        # 3. Clona ElementTypes (solo gli oggetti, le relazioni verranno popolate dopo)
        original_elementtype_minacce = {}
        for obj in ElementType.objects.filter(campagna__isnull=True).prefetch_related('minacce'):
            old_id = obj.id
            original_elementtype_minacce[old_id] = list(obj.minacce.all())
            obj.cloned_from_id = old_id
            obj.id = None
            obj._state.adding = True
            obj.campagna = new_campaign
            obj.save()
            elementtype_map[old_id] = obj

        # Assicura che esista un ElementType 'root' per la campagna
        ElementType.objects.get_or_create(
            nome='root',
            campagna=new_campaign,
            defaults={'descrizione': 'Elemento di tipo root per la campagna'}
        )

        # 4. Clona Controlli (dipendono da ElementTypes)
        for obj in Controllo.objects.filter(campagna__isnull=True):
            old_id = obj.id
            obj.id = None
            obj._state.adding = True
            obj.campagna = new_campaign
            if obj.elementtype_id:
                obj.elementtype = elementtype_map.get(obj.elementtype_id)
            obj.save()
            controllo_map[old_id] = obj

        # 5. Clona StrutturaTemplate e i loro nodi
        for master_template in StrutturaTemplate.objects.filter(campagna__isnull=True).prefetch_related('nodi_template'):
            old_id = master_template.id
            original_nodes = list(master_template.nodi_template.all())
            
            # Clona l'oggetto StrutturaTemplate
            master_template.id = None
            master_template._state.adding = True
            master_template.campagna = new_campaign
            master_template.cloned_from_id = old_id
            master_template.save()
            new_template = master_template
            template_map[old_id] = new_template

            # Clona i nodi del template in modo sicuro, senza modificare gli originali
            node_map = {}
            for node in sorted(original_nodes, key=lambda n: n.level):
                old_node_id = node.id
                cloned_parent = node_map.get(node.parent_id) if node.parent_id else None
                cloned_element_type = elementtype_map.get(node.element_type_id)

                if cloned_element_type:
                    new_node = NodoTemplate.objects.create(
                        template=new_template, element_type=cloned_element_type, parent=cloned_parent, campagna=new_campaign
                    )
                    node_map[old_node_id] = new_node

        # 6. Clona Asset
        for obj in Asset.objects.filter(campagna__isnull=True):
            old_id = obj.id
            obj.id = None
            obj._state.adding = True
            obj.campagna = new_campaign
            obj.cloned_from_id = old_id
            if obj.template_da_applicare_id in template_map:
                obj.template_da_applicare = template_map[obj.template_da_applicare_id]
            obj.save()

        # 7. Popola relazioni di ElementType (M2M con Minacce e Valori Matrice)
        valori_da_creare = []
        for old_et_id, new_et in elementtype_map.items():
            new_minacce = [minaccia_map[m.id] for m in original_elementtype_minacce[old_et_id] if m.id in minaccia_map]
            if new_minacce:
                new_et.minacce.set(new_minacce)

            for valore in ValoreElementType.objects.filter(elementtype_id=old_et_id):
                new_minaccia = minaccia_map.get(valore.minaccia_id)
                new_controllo = controllo_map.get(valore.controllo_id)
                if new_minaccia and new_controllo:
                    valori_da_creare.append(
                        ValoreElementType(elementtype=new_et, minaccia=new_minaccia, controllo=new_controllo, valore=valore.valore)
                    )

        # 8. Crea tutti i valori delle matrici in una sola query per efficienza
        ValoreElementType.objects.bulk_create(valori_da_creare)