from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from core.admin_mixins import MasterAdminMixin, CustomDeleteActionMixin
from core.admin_filters import MasterCampaignFilter
from .models import Controllo
from elementtypes.models import ElementType

@admin.register(Controllo)
class ControlloAdmin(CustomDeleteActionMixin, MasterAdminMixin, ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('nome', 'tipologia_controllo', 'peso_controllo', 'elementtype', 'delete_button')
    list_filter = (MasterCampaignFilter, 'tipologia_controllo', 'categoria_controllo', 'campagna', 'elementtype')
    search_fields = ('nome', 'descrizione')
    readonly_fields = ('campagna',)