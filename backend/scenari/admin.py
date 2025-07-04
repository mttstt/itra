from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from core.admin_mixins import MasterAdminMixin, CustomDeleteActionMixin
from core.admin_filters import MasterCampaignFilter
from .models import Scenario

@admin.register(Scenario)
class ScenarioAdmin(CustomDeleteActionMixin, MasterAdminMixin, ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('descrizione', 'delete_button')
    list_filter = (MasterCampaignFilter, 'campagna')
    search_fields = ('descrizione',)
    readonly_fields = ('campagna',)