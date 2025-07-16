import random
from itertools import cycle
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from scenari.models import Scenario
from minacce.models import Minaccia
from assets.models import Asset, NodoStruttura
from controlli.models import Controllo
from elementtypes.models import ElementType
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Popola il database con dati di test per ITRA'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Pulisce il database prima di eseguire il seeding.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        from campagne.models import Campagna  # Import here to be available throughout the handle method

        if options['clean']:
            self.stdout.write(self.style.WARNING("Pulizia del database in corso..."))
            Asset.objects.all().delete()
            NodoStruttura.objects.all().delete()
            Controllo.objects.all().delete()
            ElementType.objects.all().delete()
            Minaccia.objects.all().delete()
            Scenario.objects.all().delete()
            Campagna.objects.all().delete() # Now uses the import from above
            User.objects.filter(is_superuser=False).delete()
            from assets.models import StrutturaTemplate  # Importazione qui per evitare dipendenze circolari
            self.stdout.write(self.style.SUCCESS("Database pulito."))

        self.stdout.write(self.style.SUCCESS("Inizio seeding del database..."))

        # 1. Crea utente admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write("Superuser 'admin' creato con password 'admin'.")
        admin_user = User.objects.get(username='admin')
        
        # 2. Creazione anagrafiche "master" (senza campagna)
        self.stdout.write(self.style.SUCCESS("\nCreazione anagrafiche master..."))
        scenari = self._crea_scenari()
        minacce = self._crea_minacce(scenari)
        element_types_base = self._crea_elementtype_base()
        self._crea_controlli(element_types_base, admin_user) # I controlli vengono associati agli ET
        self._popola_matrici_base(element_types_base, minacce)
        element_types_derivati = self._crea_elementtype_derivati()

        # 3. Creazione template strutture
        self.stdout.write(self.style.SUCCESS("\nCreazione template strutture..."))
        templates = self._crea_templates(15)

        # 4. Creazione Asset master con assegnazione template
        self.stdout.write(self.style.SUCCESS("\nCreazione Asset master con template..."))
        self._crea_assets_master(admin_user, templates, 100)
        # 5. Creazione e popolamento della campagna iniziale
        self.stdout.write(self.style.SUCCESS("\nCreazione e popolamento della campagna iniziale '2024'..."))
        campagna_2024, created = Campagna.objects.get_or_create(
            anno=2024,
            defaults={
                'descrizione': 'Campagna di Assessment 2024',
                'data_inizio': '2024-01-01',
                'data_fine': '2024-12-31'
            }
        )
        # If the campaign was just created, popola_from_master was already called by its save() method.
        # If it was not created (i.e., it already existed) and it's empty, then populate it.
        if not created and not campagna_2024.controlli.exists():
            campagna_2024.popola_from_master()

        self.stdout.write(self.style.SUCCESS("\n--- Statistiche di Seeding ---"))
        self.stdout.write(f"Scenari creati: {Scenario.objects.count()}")
        self.stdout.write(f"Minacce create: {Minaccia.objects.count()}")
        self.stdout.write(f"Element Types creati: {ElementType.objects.count()}")
        self.stdout.write(f"Controlli creati: {Controllo.objects.count()}")
        self.stdout.write(f"Templates creati: {len(templates)}")
        self.stdout.write(f"Asset master creati: {Asset.objects.filter(campagna__isnull=True).count()} (con template assegnato)")
        self.stdout.write(self.style.SUCCESS("--- Seeding completato con successo! ---"))

    def _crea_scenari(self):
        scenari_data = [f"Scenario di rischio {i} (Master)" for i in range(1, 6)]  # Make descriptions unique
        scenari = [Scenario.objects.get_or_create(descrizione=desc, campagna=None)[0] for desc in scenari_data]
        self.stdout.write(f"Creati {len(scenari)} scenari.")
        return scenari

    def _crea_minacce(self, scenari):
        minacce_data = [f"Minaccia generica n.{i}" for i in range(1, 46)]
        scenari_cycle = cycle(scenari)
        [Minaccia.objects.get_or_create(
            descrizione=desc,
            campagna=None,
            scenario=next(scenari_cycle)
        )[0] for desc in minacce_data]
        self.stdout.write(f"Create {len(minacce_data)} minacce.")
        return Minaccia.objects.all()

    def _crea_elementtype_base(self):
        nomi = [
            "application", "database", "schema", "procedure interne", "network", 
            "sala server", "sistemi operativi", "server", "cloud", 
            "terze parti", "terze parti trasversali"
        ]
        for nome in nomi:
            ElementType.objects.get_or_create(nome=nome, campagna=None, defaults={'descrizione': f'Elemento di tipo {nome}', 'is_base': True, 'is_enabled': True})
        self.stdout.write(f"Creati {len(nomi)} ElementType base.")
        return ElementType.objects.filter(nome__in=nomi)

    def _crea_controlli(self, element_types, owner):
        controlli_creati = []
        et_cycle = cycle(element_types)
        for i in range(1, 281):
            tipologia = random.choice(Controllo.TIPOLOGIA_CHOICES)[0]
            categoria = random.choice(Controllo.CATEGORIA_CHOICES)[0]
            controllo, _ = Controllo.objects.get_or_create(
                nome=f"Controllo C.{i:03}",
                campagna=None,
                defaults={
                    'descrizione': f"Descrizione dettagliata per il controllo C.{i:03}",
                    'tipologia_controllo': tipologia,
                    'categoria_controllo': categoria,
                    'macroambito': f"Ambito {random.choice(['Sicurezza', 'Operativo', 'Compliance'])}",
                    'owner': owner,
                    'elementtype': next(et_cycle)
                }
            )
            controlli_creati.append(controllo)
        self.stdout.write(f"Creati {len(controlli_creati)} controlli.")
        return Controllo.objects.all()
    

    def _popola_matrici_base(self, element_types, minacce):
        dimensioni = [
            (10, 40), (4, 10), (3, 10), (4, 20), (4, 50), (2, 10),
            (4, 10), (7, 15), (10, 8), (4, 7), (2, 16)
        ] # 11 dimensioni per 11 ET base

        from elementtypes.models import ValoreElementType

        for et, dim in zip(element_types, dimensioni):
            if et.valori_matrice.exists():
                continue

            num_minacce, num_controlli = dim
            
            # Seleziona minacce e controlli
            minacce_selezionate = random.sample(list(minacce), k=min(num_minacce, minacce.count()))
            controlli_disponibili = Controllo.objects.filter(elementtype=et)
            controlli_selezionati = random.sample(list(controlli_disponibili), k=min(num_controlli, controlli_disponibili.count()))

            et.minacce.set(minacce_selezionate)

            # Popola valori con sparsità
            for minaccia_matrice in minacce_selezionate:
                # Assicura almeno un valore non nullo per riga
                controllo_obbligatorio = random.choice(controlli_selezionati)
                ValoreElementType.objects.create(elementtype=et, minaccia=minaccia_matrice, controllo=controllo_obbligatorio, valore=controllo_obbligatorio.peso_controllo)
                # Popola il resto della riga con sparsità
                for controllo_matrice in controlli_selezionati:
                    if controllo_matrice == controllo_obbligatorio:
                        continue
                    if random.uniform(0, 1) < random.uniform(0.2, 0.6): # Sparsità 20-60%
                        ValoreElementType.objects.create(elementtype=et, minaccia=minaccia_matrice, controllo=controllo_matrice, valore=controllo_matrice.peso_controllo)
        self.stdout.write(f"Popolate le matrici per {len(dimensioni)} ElementType base.")
    def _crea_elementtype_derivati(self):
        """Crea gli element type derivati e li popola aggregando i componenti."""
        # db derivato da database e schema
        et_db, _ = ElementType.objects.get_or_create(
            nome="db", campagna=None, defaults={'descrizione': "DB derivato da database e schema", 'is_base': False, 'is_enabled': True}
        )
        db_components = ElementType.objects.filter(nome__in=['database', 'schema'])
        if db_components:
            et_db.component_element_types.set(db_components)
            ElementType.objects.aggregazione(et_db, db_components)

        # backend derivato da sistemi operativi e server
        et_backend, _ = ElementType.objects.get_or_create(
            nome="backend", campagna=None, defaults={'descrizione': "Backend derivato da SO e server", 'is_base': False, 'is_enabled': True}
        )
        backend_components = ElementType.objects.filter(nome__in=['sistemi operativi', 'server'])
        if backend_components:
            et_backend.component_element_types.set(backend_components)
            ElementType.objects.aggregazione(et_backend, backend_components)

        self.stdout.write("Creati e popolati 2 ElementType derivati.")
        return ElementType.objects.filter(nome__in=["db", "backend"])

    def _crea_templates(self, num_templates):
        from assets.models import StrutturaTemplate, NodoTemplate

        all_element_types = list(ElementType.objects.filter(campagna__isnull=True, is_enabled=True))
        if not all_element_types:
            self.stdout.write(self.style.WARNING("Nessun ElementType master trovato e abilitato. Impossibile creare template."))
            return []

        templates = []
        for i in range(1, num_templates + 1):
            template, _ = StrutturaTemplate.objects.get_or_create(
                nome=f"Template Struttura {i}",
                defaults={'descrizione': f"Template di esempio n. {i}"}
            )
            templates.append(template)

            # Crea una struttura di esempio per il template
            root_et = random.choice(all_element_types)
            root_node = NodoTemplate.objects.create(template=template, element_type=root_et)
            self._popola_albero_template(template, root_node, all_element_types, max_depth=3, max_children=3)
        self.stdout.write(f"Creati {len(templates)} template di struttura.")
        return templates

    def _popola_albero_template(self, template, parent_node, all_ets, max_depth, max_children, current_depth=1):
        from assets.models import NodoTemplate
        if current_depth >= max_depth or not all_ets:
            return
        
        # Determine the number of children, ensuring it's not more than the available unique element types.
        num_children = random.randint(1, min(max_children, len(all_ets)))

        # Sample unique element types for the children of this parent node to avoid UNIQUE constraint violations.
        children_ets = random.sample(all_ets, k=num_children)

        for child_et in children_ets:
            child_node = NodoTemplate.objects.create(template=template, element_type=child_et, parent=parent_node)
            if random.random() < 0.6:  # Probabilità di avere ulteriori livelli
                self._popola_albero_template(template, child_node, all_ets, max_depth, max_children, current_depth + 1)

    def _crea_assets_master(self, admin_user, templates, num_assets):
        """Crea asset master assegnando casualmente un template."""
        if not templates:
            self.stdout.write(self.style.WARNING("Nessun template disponibile. Gli asset verranno creati senza template."))

        assets = []
        for i in range(1, num_assets + 1):
            asset, _ = Asset.objects.get_or_create(
                nome=f"Asset Master {i}",
                campagna=None,
                defaults={
                'descrizione': f"Asset master di esempio n. {i}",
                'cmdb': f"CMDB{1000 + i}",
                'utente_responsabile': admin_user,
                'responsabile_applicativo': admin_user,
                'legal_entity': random.choice(["Banca A", "Assicurazioni B", "Servizi C"]),
                'status': random.choice(['in_produzione', 'in_sviluppo']),
                'template_da_applicare': random.choice(templates) if templates else None,
                }
            )
            if asset.template_da_applicare and not asset.nodi_struttura.exists():
                asset._applica_struttura_da_template()
            assets.append(asset)
        self.stdout.write(f"Creati {len(assets)} asset master con assegnazione casuale di template.")
        return assets
