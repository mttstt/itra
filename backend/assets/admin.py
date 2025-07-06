from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from import_export.admin import ImportExportModelAdmin
from .models import Asset, NodoStruttura, StrutturaTemplate, NodoTemplate
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from core.admin_mixins import CustomDeleteActionMixin, MasterAdminMixin
from core.admin_filters import MasterCampaignFilter
from simple_history.admin import SimpleHistoryAdmin
from .resources import AssetResource, StrutturaTemplateResource, NodoTemplateResource, NodoStrutturaResource


@admin.register(StrutturaTemplate)
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


@admin.register(NodoTemplate)
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

    def gestisci_nodi_struttura(self, obj):
        if not obj.pk:
            return "Salva l'asset per poter gestire la struttura."

        url = reverse('admin:assets_nodostruttura_changelist')
        params = {'asset__id__exact': obj.pk}
        if obj.campagna:
            params['campagna__id__exact'] = obj.campagna.pk

        link = f'{url}?{urlencode(params)}'
        count = obj.nodi_struttura.count()
        return format_html('<a href="{}" class="button">Gestisci {} nodi della struttura</a>', link, count)
    gestisci_nodi_struttura.short_description = 'Struttura Asset'


@admin.register(NodoStruttura)
class NodoStrutturaAdmin(CustomDeleteActionMixin, MasterAdminMixin, SimpleHistoryAdmin, ImportExportModelAdmin, DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'dimensione_matrice', 'asset', 'element_type', 'campagna', 'delete_button')
    list_display_links = ('indented_title',)
    list_filter = (MasterCampaignFilter, 'asset')
    raw_id_fields = ('asset', 'element_type', 'parent')
    readonly_fields = ('campagna',)
    resource_class = NodoStrutturaResource

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