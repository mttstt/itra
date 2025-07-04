from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import Asset, NodoStruttura, StrutturaTemplate, NodoTemplate
from core.admin_mixins import MasterAdminMixin, CustomDeleteActionMixin
from core.admin_filters import MasterCampaignFilter

@admin.register(StrutturaTemplate)
class StrutturaTemplateAdmin(CustomDeleteActionMixin, MasterAdminMixin, admin.ModelAdmin):
    list_display = ('nome', 'campagna', 'delete_button')
    list_filter = (MasterCampaignFilter, 'campagna')
    search_fields = ('nome', 'descrizione')
    readonly_fields = ('campagna',)

@admin.register(NodoTemplate)
class NodoTemplateAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'template', 'element_type', 'campagna')
    list_display_links = ('indented_title',)
    list_filter = ('template', 'campagna')
    readonly_fields = ('campagna',)

@admin.register(Asset)
class AssetAdmin(CustomDeleteActionMixin, MasterAdminMixin, admin.ModelAdmin):
    list_display = ('nome', 'status', 'template_da_applicare', 'campagna', 'delete_button')
    list_filter = (MasterCampaignFilter, 'status', 'campagna')
    search_fields = ('nome', 'descrizione')
    readonly_fields = ('campagna',)

@admin.register(NodoStruttura)
class NodoStrutturaAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'asset', 'element_type', 'campagna')
    list_display_links = ('indented_title',)
    list_filter = ('asset', 'campagna')
    raw_id_fields = ('asset', 'element_type', 'parent')
    readonly_fields = ('campagna',)