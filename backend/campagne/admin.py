from django.contrib import admin, messages
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from .models import Campagna
from datetime import date
from django.utils.html import format_html
from django.urls import reverse
from django.urls import path # Import path for custom admin URLs
from core.admin_mixins import CustomDeleteActionMixin
from .views import campagna_dashboard_view # Import the custom view

@admin.register(Campagna) # Removed MasterAdminMixin
class CampagnaAdmin(CustomDeleteActionMixin, ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('anno', 'descrizione', 'status', 'data_inizio', 'data_fine', 'dashboard_link', 'delete_button')
    list_filter = ('anno', 'status') # Removed MasterCampaignFilter
    search_fields = ('anno', 'descrizione')
    


    def dashboard_link(self, obj):
        url = reverse('admin:campagne_campagna_dashboard', args=[obj.pk]) # Questo nome è corretto per il reverse
        return format_html('<a href="{}">Accedi al Dashboard</a>', url)
    dashboard_link.short_description = 'Dashboard'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # Registra la vista dashboard sotto l'URL dell'admin per questa campagna
            path('<int:campagna_id>/dashboard/', self.admin_site.admin_view(campagna_dashboard_view), name='campagne_campagna_dashboard'),
        ]

        # Filter out any unnamed generic object_id patterns that might conflict.
        # The standard 'change' pattern is <path:object_id>/change/ and should be named.
        # The problematic one from debug output was <path:object_id>/ with Name: None.
        filtered_urls = [
            url_pattern for url_pattern in urls
            if not (isinstance(url_pattern.pattern, str) and url_pattern.pattern == '<path:object_id>/' and not hasattr(url_pattern, 'name'))
        ]

        # Place custom_urls first to ensure specificity, then add the filtered default URLs.
        combined_urls = custom_urls + filtered_urls
        return combined_urls

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == 'close':
            # Rende tutti i campi readonly tranne lo status per poterla riaprire se necessario
            return [field.name for field in self.model._meta.fields if field.name != 'status']
        return super().get_readonly_fields(request, obj)

    def save_model(self, request, obj, form, change):
        """
        Sovrascrive save_model per mostrare un messaggio di successo
        dopo la creazione e il popolamento automatico di una nuova campagna.
        """
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new:
            messages.success(request, "Campagna creata e popolata con successo dai dati master.")
