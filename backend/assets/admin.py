from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from django import forms
from import_export.admin import ImportExportModelAdmin
from .models import Asset, NodoStruttura, StrutturaTemplate, NodoTemplate
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from urllib.parse import urlparse, parse_qs
from core.admin_mixins import CustomDeleteActionMixin, MasterAdminMixin
from core.admin_filters import MasterCampaignFilter
from django.utils.functional import SimpleLazyObject
from simple_history.admin import SimpleHistoryAdmin
from .resources import AssetResource, StrutturaTemplateResource, NodoTemplateResource, NodoStrutturaResource


# @admin.register(StrutturaTemplate)
class StrutturaTemplateAdmin(CustomDeleteActionMixin, MasterAdminMixin, SimpleHistoryAdmin, ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('nome', 'dimensione_matrice', 'campagna', 'delete_button')
    list_filter = (MasterCampaignFilter, 'campagna')
    search_fields = ('nome', 'descrizione')
    readonly_fields = ('campagna', 'gestisci_nodi')
    resource_class = StrutturaTemplateResource

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            'nodi_template__element_type__minacce',
            'nodi_template__element_type__controls_assigned_to_elementtype',
            'nodi_template__element_type__component_element_types__minacce',
            'nodi_template__element_type__component_element_types__controls_assigned_to_elementtype'
        )

    def dimensione_matrice(self, obj):
        return obj.get_dimensione_matrice_display()
    dimensione_matrice.short_description = 'Dim. Matrice'

    def gestisci_nodi(self, obj):
        if not obj.pk:
            return "Salva il template per poter aggiungere i nodi."

        url = reverse('admin:assets_nodotemplate_changelist')
        params = {'template__id__exact': obj.pk}
        if obj.campagna:
            params['campagna__id__exact'] = obj.campagna.pk

        link = f'{url}?{urlencode(params)}'
        count = obj.nodi_template.count()
        return format_html('<a href="{}" class="button">Gestisci {} nodi della struttura</a>', link, count)
    gestisci_nodi.short_description = 'Struttura ad Albero'


# @admin.register(NodoTemplate)
class NodoTemplateAdmin(CustomDeleteActionMixin, MasterAdminMixin, SimpleHistoryAdmin, ImportExportModelAdmin, DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'dimensione_matrice', 'template', 'element_type', 'campagna', 'delete_button')
    list_display_links = ('indented_title',)
    list_filter = (MasterCampaignFilter, 'template')
    readonly_fields = ('campagna',)
    resource_class = NodoTemplateResource

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('element_type').prefetch_related(
            'element_type__minacce',
            'element_type__controls_assigned_to_elementtype',
            'element_type__component_element_types__minacce',
            'element_type__component_element_types__controls_assigned_to_elementtype'
        )

    def dimensione_matrice(self, obj):
        return obj.get_dimensione_matrice_display()
    dimensione_matrice.short_description = 'Dim. Matrice'


@admin.register(Asset) # Aggiunto MasterAdminMixin per coerenza
class AssetAdmin(CustomDeleteActionMixin, MasterAdminMixin, SimpleHistoryAdmin, ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('nome', 'dimensione_matrice', 'status', 'template_da_applicare', 'campagna', 'cmdb', 'delete_button')
    list_filter = (MasterCampaignFilter, 'status', 'campagna', 'legal_entity')  # Add 'legal_entity' to the filter
    search_fields = ('nome', 'descrizione', 'cmdb')  # Include 'cmdb' in search fields
    readonly_fields = ('campagna', 'gestisci_nodi_struttura')  # Maintain readonly fields
    raw_id_fields = ('utente_responsabile', 'responsabile_applicativo')
    resource_class = AssetResource

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Determina l'ID della campagna, se presente (Asset esistente o parametro nell'URL)
        campagna_id = None
        if obj and obj.campagna:
            campagna_id = obj.campagna.id
        else:
            campagna_id = request.GET.get('campagna__id__exact')

        # Filtra i template in base alla campagna (o mostra solo i master se non c'è campagna)
        if campagna_id:
            form.base_fields['template_da_applicare'].queryset = StrutturaTemplate.objects.filter(campagna_id=campagna_id)
        else:
            form.base_fields['template_da_applicare'].queryset = StrutturaTemplate.objects.filter(campagna__isnull=True)
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            'nodi_struttura__element_type__minacce',
            'nodi_struttura__element_type__controls_assigned_to_elementtype',
            'nodi_struttura__element_type__component_element_types__minacce',
            'nodi_struttura__element_type__component_element_types__controls_assigned_to_elementtype'
        )

    def dimensione_matrice(self, obj):
        return obj.get_dimensione_matrice_display()
    dimensione_matrice.short_description = 'Dim. Matrice'

    def response_add(self, request, obj, post_url_continue=None):
        params = {}
        if 'campagna__id__exact' in request.GET:
            params['campagna__id__exact'] = request.GET['campagna__id__exact']
        
        redirect_url = reverse("admin:assets_asset_change", args=[obj.pk])
        if params:
            redirect_url += '?' + urlencode(params)
            
        return HttpResponseRedirect(redirect_url)

    def gestisci_nodi_struttura(self, obj):
        if not obj.pk:
            return "Salva l'asset per poter gestire la struttura."

        url = reverse('admin:assets_nodostruttura_changelist')

        params = {'asset__id__exact': obj.pk}
        if obj.campagna:
            params['campagna__id__exact'] = obj.campagna.pk
        link = f'{url}?{urlencode(params)}'

        # Forza il refresh dell'oggetto per assicurarsi che il conteggio dei nodi sia aggiornato
        # dopo la creazione automatica del nodo radice nel segnale post_save.
        try:
            obj.refresh_from_db()
        except Asset.DoesNotExist:
            # L'oggetto potrebbe non essere ancora nel DB se la transazione non è completa.
            # In questo caso, il conteggio originale è probabilmente corretto (0).
            pass

        count = obj.nodi_struttura.count()
        return format_html('<a href="{}" class="button">Gestisci {} nodi della struttura</a>', link, count)
    gestisci_nodi_struttura.short_description = 'Struttura Asset'


@admin.register(NodoStruttura)
class NodoStrutturaAdmin(CustomDeleteActionMixin, MasterAdminMixin, SimpleHistoryAdmin, ImportExportModelAdmin, DraggableMPTTAdmin): 
    list_display = ('tree_actions', 'indented_title', 'dimensione_matrice', 'asset', 'element_type', 'campagna', 'delete_button')
    list_display_links = ('indented_title',)
    list_filter = (MasterCampaignFilter, 'asset')
    fieldsets = (
        (None, {
            'fields': ('asset_nome', 'parent', 'element_type', 'nome_specifico')
        }),
    )

    def get_model_perms(self, request):
        """
        Restituisce un dizionario di permessi vuoto per nascondere il modello
        dall'indice principale dell'admin, pur mantenendolo accessibile
        tramite link diretti (es. dalla pagina degli Asset).
        """
        return {}

    readonly_fields = ('campagna',)
    resource_class = NodoStrutturaResource

    def add_view(self, request, form_url='', extra_context=None):
        """
        Sovrascrive la add_view per portare il contesto dell'asset dal referer (es. changelist filtrata).
        Se l'utente arriva alla pagina di aggiunta da una lista di nodi filtrata per asset,
        l'ID dell'asset viene aggiunto all'URL per pre-compilare il form.
        """
        if 'asset__id__exact' not in request.GET:
            referer = request.META.get('HTTP_REFERER')
            if referer:
                try:
                    parsed_url = urlparse(referer)
                    query_params = parse_qs(parsed_url.query)
                    asset_id = query_params.get('asset__id__exact')
                    if asset_id:
                        new_query_params = request.GET.copy()
                        new_query_params['asset__id__exact'] = asset_id[0]
                        return HttpResponseRedirect(f"{request.path}?{new_query_params.urlencode()}")
                except Exception:
                    pass # Ignora errori di parsing e procedi
        return super().add_view(request, form_url, extra_context)



    def get_form(self, request, obj=None, **kwargs):
        """
        Sovrascrive il form per modificare dinamicamente l'URL dei widget
        raw_id per i campi 'parent' e 'element_type', assicurando che i popup
        di selezione mostrino solo i record pertinenti al contesto (asset e campagna). Inoltre,
        assicura che i nuovi nodi possano essere aggiunti solo al di sotto del nodo root.
        """ # Ensures element types displayed are filtered by the campaign of the asset.


        asset_id = None
        campagna_id = None

        if obj and obj.asset:
            asset_id = obj.asset.id
            campagna_id = obj.asset.campagna_id
        elif 'asset__id__exact' in request.GET:
            asset_id = request.GET.get('asset__id__exact')

        if 'fields' in kwargs:
            kwargs['fields'] = [f for f in kwargs['fields'] if f != 'asset_nome']

        form = super().get_form(request, obj, **kwargs)


        class NodoStrutturaForm(form):
            asset_nome = forms.CharField(label="Nome Asset", required=False, disabled=True)

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                from elementtypes.models import ElementType
                
                # Usa l'asset_id calcolato nello scope di get_form per maggiore affidabilità
                current_asset_id = asset_id

                if current_asset_id:
                    try:
                        asset = Asset.objects.get(pk=current_asset_id)
                        self.fields['asset_nome'].initial = asset.nome
                        self.fields['parent'].queryset = NodoStruttura.objects.filter(asset_id=current_asset_id, element_type__is_base=False)

                        # Se esistono nodi per questo asset, imposta il campo parent come richiesto
                        # e preseleziona il nodo radice.
                        if NodoStruttura.objects.filter(asset_id=current_asset_id).exists():
                            self.fields['parent'].required = True
                            self.fields['parent'].empty_label = None
                            
                            root_node = NodoStruttura.objects.filter(asset_id=current_asset_id, level=0).first()
                            if root_node:
                                self.fields['parent'].initial = root_node.pk

                        # Filtra gli element type in base alla campagna dell'asset
                        if asset.campagna:
                            element_type_queryset = ElementType.objects.filter(campagna=asset.campagna).exclude(nome="root")
                        else:
                            element_type_queryset = ElementType.objects.filter(campagna__isnull=True).exclude(nome="root")

                        self.fields['element_type'].queryset = element_type_queryset
                        self.fields['element_type'].label_from_instance = self.element_type_label_from_instance

                    except Asset.DoesNotExist:
                        self.fields['parent'].queryset = NodoStruttura.objects.none()
                        self.fields['element_type'].queryset = ElementType.objects.none()
                        self.fields['asset_nome'].initial = "Asset non trovato"
                        self.fields['parent'].help_text = "Impossibile determinare l'asset. Assicurati di accedere a questa pagina tramite l'elenco dei nodi struttura dell'asset."
                else:
                    self.fields['parent'].queryset = NodoStruttura.objects.none()
                    self.fields['element_type'].queryset = ElementType.objects.none()
                    self.fields['asset_nome'].initial = "Asset non specificato"
                    self.fields['parent'].help_text = "Impossibile determinare l'asset. Assicurati di accedere a questa pagina tramite l'elenco dei nodi struttura dell'asset."

            def element_type_label_from_instance(self, obj):
                """Customizes the display of ElementType instances in the dropdown."""
                if obj.is_base:
                    return f"{obj.nome} (Base)"
                else:
                    return f"{obj.nome} (Derivato)"

            def clean(self):
                cleaned_data = super().clean()
                parent = cleaned_data.get('parent')
                
                # For new nodes, enforce that a parent is selected if a root node already exists.
                if not self.instance.pk and not parent:
                    if asset_id and NodoStruttura.objects.filter(asset_id=asset_id, level=0).exists():
                        raise forms.ValidationError(
                            "Un nodo radice esiste già per questo asset. "
                            "Tutti i nuovi nodi devono avere un nodo padre."
                        )
                return cleaned_data
        return NodoStrutturaForm





    def response_add(self, request, obj, post_url_continue=None):
        """
        Redirects to the asset-specific node structure view after adding a new node.
        """
        asset_id = obj.asset.pk
        params = {'asset__id__exact': asset_id}
        if obj.asset.campagna:
            params['campagna__id__exact'] = obj.asset.campagna.pk
        
        redirect_url = reverse('admin:assets_nodostruttura_changelist')
        return HttpResponseRedirect(f'{redirect_url}?{urlencode(params)}')

    def response_change(self, request, obj):
        """
        Redirects to the asset-specific node structure view after changing a node.
        """
        asset_id = obj.asset.pk
        params = {'asset__id__exact': asset_id}
        if obj.asset.campagna:
            params['campagna__id__exact'] = obj.asset.campagna.pk
            
        redirect_url = reverse('admin:assets_nodostruttura_changelist')
        return HttpResponseRedirect(f'{redirect_url}?{urlencode(params)}')

    def save_model(self, request, obj, form, change):
        """
        Assicura che l'asset venga salvato correttamente, anche se il campo è disabilitato nel form.
        """
        # Se si sta creando un nuovo oggetto e l'asset non è stato impostato
        if not change and not obj.asset_id:
            asset_id = request.GET.get('asset__id__exact')
            if asset_id:
                obj.asset = Asset.objects.get(pk=asset_id)

                # Se è il primo nodo dell'asset, imposta il nome uguale a quello dell'asset
                if not NodoStruttura.objects.filter(asset=obj.asset, level=0).exists():
                    obj.nome_specifico = obj.asset.nome

                    # Aggrega la matrice del nodo radice se ha figli
                    children = NodoStruttura.objects.filter(parent=obj)
                    if children.exists():
                        # Aggrega la matrice del nodo radice basata sui figli
                        from elementtypes.models import ElementType
                        element_types = [child.element_type for child in children]

                        # TODO: Aggregazione

        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """
        Filtra il queryset in base al parametro 'asset_id_for_filter' passato
        dall'URL del popup raw_id. Questo è il secondo pezzo della soluzione
        per filtrare i parent.
        """
        qs = super().get_queryset(request)
        
        # Se il parametro è presente, filtra i nodi per l'asset specificato
        asset_id_for_filter = request.GET.get('asset_id_for_filter')
        if asset_id_for_filter:
            qs = qs.filter(asset_id=asset_id_for_filter)
        
        # Mantiene il prefetching originale per le performance
        return qs.select_related('element_type').prefetch_related(
            'element_type__minacce',
            'element_type__controls_assigned_to_elementtype',
            'element_type__component_element_types__minacce',
            'element_type__component_element_types__controls_assigned_to_elementtype'
        )

    def dimensione_matrice(self, obj):
        return obj.get_dimensione_matrice_display()
    dimensione_matrice.short_description = 'Dim. Matrice'