from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils.html import format_html
from django.contrib.admin.views.main import ChangeList
from django import forms # Added import for forms
from django.utils.http import urlencode
from django.urls import reverse # Ensure this is imported
from django.http import HttpResponseRedirect # Ensure this is imported
from urllib.parse import urlparse, parse_qs

from django.utils.safestring import mark_safe
def get_nested_attr(obj, attr_path):
    attrs = attr_path.split('__')
    for attr in attrs:
        try:
            obj = getattr(obj, attr)
        except (AttributeError, TypeError):
            return None
    return obj

class MasterAdminMixin:
     
    def _get_campaign_lookup_path(self):
        return getattr(self, 'campaign_lookup', 'campagna')

    def _get_campaign_param_name(self):
        lookup_path = self._get_campaign_lookup_path()
        return f"{lookup_path}__id__exact"

    def _get_campaign_from_obj(self, obj):
        if not obj:
            return None
        lookup_path = self._get_campaign_lookup_path()
        
        # Helper to traverse nested attributes
        current_obj = obj
        for attr in lookup_path.split('__'):
            try:
                current_obj = getattr(current_obj, attr)
            except (AttributeError, TypeError):
                return None
        return current_obj

    def highlighted_status(self, obj):
        if self._get_campaign_from_obj(obj) is None:
            return format_html('<span class="master-list-badge">MASTER</span>')
        return "Campagna"
    highlighted_status.short_description = 'Tipo Record'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        obj_campaign = self._get_campaign_from_obj(obj)
        campagna_id_from_url = request.GET.get(self._get_campaign_param_name())

        if obj_campaign is None and campagna_id_from_url:
            raise PermissionDenied("Non è possibile modificare un record MASTER dall'area di una campagna.")
        # elif obj_campaign is not None:
        #     messages.info(request, f"Stai operando su un record appartenente alla campagna: '{obj_campaign}'.")
 
        return super().change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        """
        Sovrascrive la add_view per mantenere il contesto della campagna.
        Se si accede alla pagina di aggiunta senza un parametro di campagna,
        ma la pagina precedente (referer) lo aveva, reindirizza alla stessa
        pagina di aggiunta includendo quel parametro.
        """
        param_name = self._get_campaign_param_name()
        generic_param = 'campagna__id__exact'

        # Se il parametro di campagna non è già nell'URL...
        if param_name not in request.GET and generic_param not in request.GET:
            referer = request.META.get('HTTP_REFERER')
            if referer:
                try:
                    parsed_url = urlparse(referer)
                    query_params = parse_qs(parsed_url.query)
                    print("query_params:", query_params)
                    print("param_name:", param_name)
                    print("generic_param:", generic_param)
    
                    # ...controlla se era nella pagina precedente.
                    campagna_id = query_params.get(param_name, query_params.get(generic_param))
                    if campagna_id:
                        # Esegui il redirect aggiungendo il parametro.
                        new_query_params = request.GET.copy()
                        if param_name not in new_query_params:
                            new_query_params[param_name] = campagna_id[0]
                        return HttpResponseRedirect(f"{request.path}?{new_query_params.urlencode()}")
                except Exception:
                    pass # Ignora errori di parsing e procedi

        return super().add_view(request, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        lookup_path = self._get_campaign_lookup_path()
        specific_param = self._get_campaign_param_name()
        generic_param = 'campagna__id__exact'

        if generic_param in request.GET and specific_param not in request.GET and lookup_path != 'campagna':
            request.GET = request.GET.copy()
            request.GET[specific_param] = request.GET[generic_param]

        return super().changelist_view(request, extra_context)

    def get_changeform_initial_data(self, request):

        initial = super().get_changeform_initial_data(request)
        campagna_id = request.GET.get(self._get_campaign_param_name())
        if campagna_id:
           
                    
            initial['campagna'] = campagna_id
        return initial

    def get_form(self, request, obj=None, **kwargs):
        """
        Sovrascrive il form di default per assicurare che i campi correlati
        siano filtrati in base alla campagna dell'oggetto in modifica.
        Questo ha la precedenza sui parametri URL per gli oggetti esistenti
        e risolve il problema di validazione durante il salvataggio (POST).
        """
        form = super().get_form(request, obj, **kwargs)

        # Determina l'ID della campagna da usare per i filtri.
        # Priorità 1: la campagna dell'oggetto che si sta modificando.
        # Priorità 2: l'ID campagna dall'URL (per nuovi oggetti).
        effective_campagna_id = None
        if obj and hasattr(obj, 'campagna') and obj.campagna:
            effective_campagna_id = obj.campagna.id
        else:
            effective_campagna_id = request.GET.get('campagna__id__exact')

        # Elenco dei campi che la classe Admin specifica gestirà manualmente
        custom_filter_fields = getattr(self, 'custom_filter_fields', [])

        # Applica il filtro a tutti i campi di tipo ModelChoiceField e ModelMultipleChoiceField
        for field_name, form_field in form.base_fields.items():
            # Salta i campi che sono gestiti in modo personalizzato dalla classe Admin figlia
            if field_name in custom_filter_fields:
                continue

            if isinstance(form_field, (forms.ModelChoiceField, forms.ModelMultipleChoiceField)):
                related_model = form_field.queryset.model
                if hasattr(related_model, 'campagna'):
                    if effective_campagna_id:
                        form_field.queryset = related_model.objects.filter(campagna_id=effective_campagna_id)
                    else:
                        form_field.queryset = related_model.objects.filter(campagna__isnull=True)
        return form

    def save_model(self, request, obj, form, change):
        """
        Sovrascrive save_model per assicurare che il campo 'campagna' sia impostato
        per i nuovi oggetti creati in un contesto di campagna, anche se è un readonly_field.
        Questo è cruciale perché i campi readonly non vengono processati dal form.
        """
        # Applica solo alla creazione di un nuovo oggetto (`change` è False)
        # e solo se il modello ha un campo 'campagna'.
        if not change and hasattr(obj, 'campagna'):
            campagna_id = request.GET.get('campagna__id__exact')
            if campagna_id:
                from campagne.models import Campagna # Importazione locale per evitare dipendenze circolari
                obj.campagna = Campagna.objects.get(pk=campagna_id)
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        La logica di filtraggio è ora gestita in get_form per coerenza
        e per funzionare correttamente anche nelle richieste POST.
        """
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def response_add(self, request, obj, post_url_continue=None):
        """
        Gestisce il reindirizzamento dopo l'aggiunta di un oggetto,
        mantenendo il contesto della campagna per tutti i pulsanti di salvataggio.
        """
        opts = self.model._meta
        campaign_params = {}
        if hasattr(obj, 'campagna') and obj.campagna:
            campaign_params = {'campagna__id__exact': obj.campagna.id}

        changelist_url = reverse(f'admin:{opts.app_label}_{opts.model_name}_changelist')
        add_url = reverse(f'admin:{opts.app_label}_{opts.model_name}_add')
        change_url = reverse(f'admin:{opts.app_label}_{opts.model_name}_change', args=[obj.pk])

        if "_addanother" in request.POST:
            redirect_url = f"{add_url}?{urlencode(campaign_params)}" if campaign_params else add_url
            if 'campagna__id__exact' not in redirect_url:
                return HttpResponseRedirect(redirect_url)
        if "_continue" in request.POST:
            redirect_url = f"{change_url}?{urlencode(campaign_params)}" if campaign_params else change_url
            return HttpResponseRedirect(redirect_url)

        redirect_url = f"{changelist_url}?{urlencode(campaign_params)}" if campaign_params else changelist_url
        return HttpResponseRedirect(redirect_url)

    def response_change(self, request, obj):
        """
        Gestisce il reindirizzamento dopo la modifica di un oggetto,
        mantenendo il contesto della campagna per tutti i pulsanti di salvataggio.
        """
        opts = self.model._meta
        campaign_params = {}
        if hasattr(obj, 'campagna') and obj.campagna:
            campaign_params = {'campagna__id__exact': obj.campagna.id}

        changelist_url = reverse(f'admin:{opts.app_label}_{opts.model_name}_changelist')
        add_url = reverse(f'admin:{opts.app_label}_{opts.model_name}_add')
        change_url = reverse(f'admin:{opts.app_label}_{opts.model_name}_change', args=[obj.pk])

        redirect_url = ""
        if "_addanother" in request.POST:
            redirect_url = f"{add_url}?{urlencode(campaign_params)}" if campaign_params else add_url
        if 'campagna__id__exact' not in redirect_url:
            return HttpResponseRedirect(redirect_url)
        if "_continue" in request.POST:
            redirect_url = f"{change_url}?{urlencode(campaign_params)}" if campaign_params else change_url
            return HttpResponseRedirect(redirect_url)

        redirect_url = f"{changelist_url}?{urlencode(campaign_params)}" if campaign_params else changelist_url
        return HttpResponseRedirect(redirect_url)

    def delete_view(self, request, object_id, extra_context=None):
        """
        Sovrascrive la delete_view per gestire correttamente il contesto della campagna.
        1. Aggiunge la campagna al contesto per la pagina di conferma (GET).
        2. Salva l'ID della campagna sulla request per usarlo in response_delete (POST).
        """
        obj = self.get_object(request, object_id)
        if obj and hasattr(obj, 'campagna') and obj.campagna:
            # Salva l'ID della campagna per il reindirizzamento post-cancellazione
            request._campagna_id_for_delete_redirect = obj.campagna.id

            # Aggiunge la campagna al contesto per il template di conferma
            if extra_context is None:
                extra_context = {}
            # Questo permette al context_processor 'current_campagna' e ai template
            # di sapere in che contesto ci si trova, correggendo i breadcrumb.
            extra_context['current_campagna'] = obj.campagna

        return super().delete_view(request, object_id, extra_context)

    def response_delete(self, request, obj_display, obj_id):
        """
        Sovrascrive la response_delete per reindirizzare alla changelist filtrata
        per campagna, se l'oggetto eliminato apparteneva a una campagna.
        """
        response = super().response_delete(request, obj_display, obj_id)
        campagna_id = getattr(request, '_campagna_id_for_delete_redirect', None)

        if isinstance(response, HttpResponseRedirect) and campagna_id:
            opts = self.model._meta
            changelist_url = reverse(f'admin:{opts.app_label}_{opts.model_name}_changelist')
            params = {'campagna__id__exact': campagna_id}
            return HttpResponseRedirect(f"{changelist_url}?{urlencode(params)}")
        return response

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # La logica di filtraggio per la changelist è ora interamente gestita
        # dalla classe MasterCampaignFilter per maggiore chiarezza e robustezza.
        # Questo metodo ora si limita a chiamare il queryset del genitore.
        return qs

    def get_changelist(self, request, **kwargs):
        """
        Sovrascrive la ChangeList di default per iniettare una generazione URL personalizzata
        che mantiene il contesto della campagna.
        """

        class CampaignAwareChangeList(ChangeList):
            def url_for_result(self, obj):
                # Ottiene l'URL base per il modulo di modifica
                base_url = reverse(
                    f'admin:{self.model_admin.opts.app_label}_{self.model_admin.opts.model_name}_change',
                    args=[obj.pk]
                )

                # Controlla se il modello corrente è "campaign-aware" (ha un campo 'campagna')
                # e se un contesto di campagna è attivo nell'URL.
                is_campaign_aware = hasattr(self.model_admin.model, 'campagna')
                campagna_id = request.GET.get('campagna__id__exact')

                if campagna_id and is_campaign_aware:
                    params = {'campagna__id__exact': campagna_id}
                    return f"{base_url}?{urlencode(params)}"

                return base_url

        # Restituisce la classe, non un'istanza. Django la istanzierà.
        return CampaignAwareChangeList

class CustomDeleteActionMixin:
    """
    Mixin per rimuovere l'azione di cancellazione di massa e aggiungere
    un pulsante di cancellazione per ogni riga nella vista elenco dell'admin.
    """
    def get_actions(self, request):
        """
        Rimuove l'azione di default "delete selected".
        """
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def delete_button(self, obj):
        """
        Genera un link con un'icona SVG del cestino per la cancellazione.
        """
        opts = self.model._meta
        url = reverse(f'admin:{opts.app_label}_{opts.model_name}_delete', args=[obj.pk])
        icon_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#ba2121" viewBox="0 0 16 16" style="vertical-align: text-bottom;"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>"""
        return format_html('<a href="{}" title="Elimina {}">{}</a>', url, opts.verbose_name.capitalize(), mark_safe(icon_svg))
    delete_button.short_description = ''
