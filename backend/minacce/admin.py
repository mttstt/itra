from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from core.admin_mixins import MasterAdminMixin, CustomDeleteActionMixin
from core.admin_filters import MasterCampaignFilter
from .models import Minaccia

@admin.register(Minaccia)
class MinacciaAdmin(CustomDeleteActionMixin, MasterAdminMixin, ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('descrizione', 'scenario', 'delete_button')
    list_filter = (MasterCampaignFilter, 'campagna', 'scenario')
    search_fields = ('descrizione',)
    readonly_fields = ('campagna',)