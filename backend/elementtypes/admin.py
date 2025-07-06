from django.contrib import admin, messages
from django.db import transaction, models
from django.db.models import Q
from django import forms

from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from core.admin_mixins import MasterAdminMixin, CustomDeleteActionMixin
from core.admin_filters import MasterCampaignFilter
from .models import ElementType, ValoreElementType
from .forms import ElementTypeForm
from controlli.models import Controllo
from minacce.models import Minaccia


@admin.register(ElementType)
class ElementTypeAdmin(CustomDeleteActionMixin, MasterAdminMixin, admin.ModelAdmin):
    form = ElementTypeForm
    change_form_template = "admin/elementtypes/elementtype/change_form.html"
    list_display = ('nome', 'is_base', 'dimensione_matrice', 'is_enabled', 'delete_button')
    list_filter = (MasterCampaignFilter, 'is_enabled', 'campagna')
    search_fields = ('nome', 'descrizione')
    readonly_fields = ('campagna', 'is_base')

    filter_horizontal = ('minacce', 'component_element_types',)

    # Rimuoviamo i fieldsets statici perché ora li gestiamo dinamicamente con get_fieldsets
    # fieldsets = (...)

    def get_fieldsets(self, request, obj=None):
        """
        Mostra dinamicamente i fieldset corretti in base al tipo di ElementType.
        """
        base_info = (None, {'fields': ('nome', 'descrizione', 'campagna', 'is_base', 'is_enabled')})
        
        if obj and obj.is_base:
            # Se è un tipo BASE, mostra la configurazione manuale di minacce e controlli
            return (
                base_info,
                ('Configurazione Minacce (righe)', {'classes': ('collapse',), 'fields': ('minacce',)}),
                ('Configurazione Controlli (colonne)', {'classes': ('collapse',), 'fields': ('assigned_controls',)}),
            )
        elif obj and not obj.is_base:
            # Se è un tipo DERIVATO, mostra solo la configurazione dei componenti
            return (
                base_info,
                ('Configurazione Tipi Derivati', {'classes': ('collapse',), 'fields': ('component_element_types',)}),
            )
        else:
            # In fase di creazione (obj is None), mostra tutto per permettere la scelta
            return (
                base_info,
                ('Configurazione per Tipi Base (lasciare vuota la sezione "derivati")', {
                    'classes': ('collapse',),
                    'fields': ('minacce', 'assigned_controls')
                }),
                ('Configurazione per Tipi Derivati (compilare per creare un tipo derivato)', {
                    'classes': ('collapse',),
                    'fields': ('component_element_types',)
                }),
            )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        formfield = super().formfield_for_manytomany(db_field, request, **kwargs)
        # Per il campo 'minacce', vogliamo nascondere il link "+" per aggiungere nuove minacce
        # direttamente da questa schermata, per mantenere l'interfaccia pulita.
        if db_field.name == "minacce":
            # Il widget è avvolto in un RelatedFieldWidgetWrapper che aggiunge i link "+", "matita", ecc.
            # Disabilitiamo la possibilità di aggiungere nuovi record correlati.
            if isinstance(formfield.widget, admin.widgets.RelatedFieldWidgetWrapper):
                formfield.widget.can_add_related = False
        return formfield

    def save_model(self, request, obj, form, change):
        # Imposta 'is_base' in base alla presenza di componenti, sia in creazione che in modifica.
        obj.is_base = not form.cleaned_data.get('component_element_types')
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related(
            'minacce', 
            'controls_assigned_to_elementtype',
            'component_element_types__minacce',
            'component_element_types__controls_assigned_to_elementtype'
        )
        return qs

    def dimensione_matrice(self, obj):
        # Chiama il metodo del modello che ora contiene la logica corretta (anche ricorsiva)
        return obj.get_dimensione_matrice_display()
    dimensione_matrice.short_description = 'Dim. Matrice'

    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)
        class ElementTypeAdminForm(form_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                instance = self.instance
                queryset_filter = Q()
                if instance and instance.pk:
                    queryset_filter.add(Q(elementtype__isnull=True) | Q(elementtype=instance), Q.AND)
                    queryset_filter.add(Q(campagna=instance.campagna), Q.AND)
                    self.initial['assigned_controls'] = instance.controls_assigned_to_elementtype.all()
                else:
                    queryset_filter.add(Q(elementtype__isnull=True), Q.AND)
                    campagna_id = request.GET.get('campagna__id__exact')
                    if campagna_id:
                        queryset_filter.add(Q(campagna_id=campagna_id), Q.AND)
                    else:
                        queryset_filter.add(Q(campagna__isnull=True), Q.AND)
                self.fields['assigned_controls'].queryset = Controllo.objects.filter(queryset_filter).distinct()
                m2m_fields_to_filter = {
                    'minacce': Minaccia,
                    'component_element_types': ElementType,
                }
                for field_name, model in m2m_fields_to_filter.items():
                    if field_name in self.fields:
                        if instance and instance.pk:
                            if instance.campagna:
                                queryset = model.objects.filter(campagna=instance.campagna)
                            else:
                                queryset = model.objects.filter(campagna__isnull=True)
                            if field_name == 'component_element_types':
                                queryset = queryset.exclude(pk=instance.pk)
                        else:
                            campagna_id = request.GET.get('campagna__id__exact')
                            queryset = model.objects.filter(campagna_id=campagna_id) if campagna_id else model.objects.filter(campagna__isnull=True)
                        self.fields[field_name].queryset = queryset
                        if field_name in ['component_element_types', 'minacce']:
                            self.fields[field_name].label = "" # Rimuove l'etichetta del campo
        return ElementTypeAdminForm

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        selected_pks = {c.pk for c in form.cleaned_data.get('assigned_controls', [])}
        current_pks = {c.pk for c in obj.controls_assigned_to_elementtype.all()}
        Controllo.objects.filter(pk__in=(selected_pks - current_pks)).update(elementtype=obj)
        Controllo.objects.filter(pk__in=(current_pks - selected_pks)).update(elementtype=None)
        
        if not obj.is_base:
            components = obj.component_element_types.all()
            ElementType.objects.aggregazione(obj, components)
            self.message_user(request, f"Matrice per '{obj.nome}' ricalcolata tramite aggregazione.", messages.INFO)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj and obj.is_base:
            minacce = obj.minacce.all().order_by('descrizione')
            controlli = Controllo.objects.filter(elementtype=obj).order_by('nome')
            context['matrix_render_problem'] = False
            context['matrix_render_problem_message'] = ""
            context['matrix_incomplete_warning'] = False
            context['matrix_incomplete_warning_message'] = ""
            if not minacce.exists():
                context['matrix_render_problem'] = True
                context['matrix_render_problem_message'] = "Associare almeno una minaccia nella sezione 'Configurazione Minacce (righe)' e salvare per visualizzare la matrice."
            elif not controlli.exists():
                context['matrix_render_problem'] = True
                context['matrix_render_problem_message'] = "Associare almeno un controllo nella sezione 'Configurazione Controlli (colonne)' e salvare per visualizzare la matrice."
            else:
                valori_dict = {(v.minaccia_id, v.controllo_id): v.valore for v in ValoreElementType.objects.filter(elementtype=obj)}
                matrix_data = []
                all_threats_have_non_zero_value = True
                for minaccia in minacce:
                    row = {'minaccia': minaccia, 'cells': []}
                    has_non_zero_value_in_row = False
                    for controllo in controlli:
                        value = valori_dict.get((minaccia.id, controllo.id))
                        if value is not None and value != 0:
                            has_non_zero_value_in_row = True
                        formatted_value = str(value).replace('.', ',') if value is not None else None
                        row['cells'].append({'controllo': controllo, 'value': formatted_value})
                    matrix_data.append(row)
                    if not has_non_zero_value_in_row:
                        all_threats_have_non_zero_value = False
                context['matrix_data'] = matrix_data
                context['matrix_controlli'] = controlli
                if not all_threats_have_non_zero_value:
                    context['matrix_incomplete_warning'] = True
                    context['matrix_incomplete_warning_message'] = "Attenzione: alcune minacce non hanno valori di controllo (diversi da zero) associati. L'Element Type non potrà essere abilitato finché la matrice non sarà completa."
        if obj and not obj.is_base:
            components = obj.component_element_types.all()
            # Usa i nuovi metodi ricorsivi per ottenere minacce e controlli
            aggregated_minacce = obj.get_all_minacce().order_by('descrizione')
            aggregated_controlli = obj.get_all_controlli().order_by('nome')

            if aggregated_minacce.exists() and aggregated_controlli.exists():
                aggregated_matrix_data = []
                for minaccia in aggregated_minacce:
                    row = {'minaccia': minaccia, 'cells': []}
                    for controllo in aggregated_controlli:
                        # Il valore viene letto direttamente dalla matrice aggregata del padre
                        valore_obj = obj.valori_matrice.filter(minaccia=minaccia, controllo=controllo).first()
                        value = valore_obj.valore if valore_obj else None
                        formatted_value = str(value).replace('.', ',') if value is not None else ''
                        row['cells'].append({'controllo': controllo, 'value': formatted_value})
                    aggregated_matrix_data.append(row)
                context['aggregated_matrix_data'] = aggregated_matrix_data
                context['aggregated_matrix_controlli'] = aggregated_controlli
        return super().render_change_form(request, context, add, change, form_url, obj)

    def response_change(self, request, obj):
        if obj.is_base and request.method == 'POST':
            with transaction.atomic():
                minacce = obj.minacce.all()
                controlli = Controllo.objects.filter(elementtype=obj)
                matrix_changed = False
                # is_enabled_changed_in_post = 'is_enabled' in request.POST and request.POST['is_enabled'] == 'on' # Not used in final logic
                post_keys = {k for k in request.POST if k.startswith('matrix-')}
                for minaccia in minacce:
                    for controllo in controlli:
                        form_field_name = f'matrix-{minaccia.id}-{controllo.id}'
                        if form_field_name in post_keys:
                            valore_str = request.POST.get(form_field_name, '').strip()
                            existing_value = ValoreElementType.objects.filter(elementtype=obj, minaccia=minaccia, controllo=controllo).first()

                            # Normalize string for parsing
                            valore_str_norm = valore_str.replace(',', '.').strip()

                            if not valore_str_norm: # Handles empty string
                                if existing_value:
                                    existing_value.delete()
                                    matrix_changed = True
                                continue # Move to next cell

                            try:
                                valore = float(valore_str_norm)

                                # If the value is 0, treat it as "not saved" (delete if exists)
                                if valore == 0.0:
                                    if existing_value:
                                        existing_value.delete()
                                        matrix_changed = True
                                    continue # Move to next cell, as 0 is not saved

                                # Validation for values between 0.01 and 1.0
                                if not (0.0 < valore <= 1.0): # Value must be strictly greater than 0
                                    messages.error(request, f"Valore '{valore_str}' non valido per la cella ({minaccia.descrizione}, {controllo.nome}). Il valore deve essere compreso tra 0.01 e 1. Modifica non salvata per questa cella.")
                                    continue

                                if '.' in valore_str_norm and len(valore_str_norm.split('.')[-1]) > 2:
                                    messages.error(request, f"Valore '{valore_str}' non valido per la cella ({minaccia.descrizione}, {controllo.nome}). Il valore deve avere al massimo due cifre decimali. Modifica non salvata per questa cella.")
                                    continue

                                if not existing_value or existing_value.valore != valore:
                                    ValoreElementType.objects.update_or_create(
                                        elementtype=obj, minaccia=minaccia, controllo=controllo,
                                        defaults={'valore': valore}
                                    )
                                    matrix_changed = True

                            except (ValueError, TypeError):
                                messages.error(request, f"Valore non numerico '{valore_str}' per la cella ({minaccia.descrizione}, {controllo.nome}). Ignorato.")
                                continue
                
                # Dopo aver processato i valori della matrice, si valida lo stato di 'is_enabled'.
                is_enabled_from_form = obj.is_enabled
                should_be_enabled = is_enabled_from_form
                validation_error_message = None

                if is_enabled_from_form:
                    # Eseguiamo la validazione completa contro lo stato attuale del DB all'interno della transazione.
                    # Questo garantisce che stiamo usando i dati più aggiornati, inclusi i valori della matrice appena salvati.
                    current_minacce = obj.minacce.all()
                    current_controlli = Controllo.objects.filter(elementtype=obj)

                    if not current_minacce.exists():
                        should_be_enabled = False
                        validation_error_message = "L'ElementType non può essere abilitato perché non ha minacce associate (righe della matrice)."
                    elif not current_controlli.exists():
                        should_be_enabled = False
                        validation_error_message = "L'ElementType non può essere abilitato perché non ha controlli assegnati (colonne della matrice)."
                    else:
                        # Vincolo 3: Ogni riga (minaccia) deve avere almeno un valore.
                        # Questa query critica legge i dati aggiornati all'interno della transazione.
                        threat_ids_with_values = set(ValoreElementType.objects.filter(elementtype=obj).values_list('minaccia_id', flat=True))
                        
                        threats_without_values = [
                            f'"{m.descrizione}"' for m in current_minacce if m.id not in threat_ids_with_values
                        ]

                        if threats_without_values:
                            should_be_enabled = False
                            validation_error_message = (
                                "L'ElementType non può essere abilitato perché le seguenti minacce (righe) "
                                "non hanno nessun controllo associato nella matrice: "
                                f"{', '.join(threats_without_values)}."
                            )
                
                # Se la validazione fallisce, aggiorna l'oggetto e informa l'utente.
                if not should_be_enabled and is_enabled_from_form:
                    obj.is_enabled = False
                    obj.save(update_fields=['is_enabled'])
                    messages.error(request, validation_error_message)

            if matrix_changed:
                self.message_user(request, f"Matrice per '{obj.nome}' aggiornata con successo.", messages.SUCCESS)
        return super().response_change(request, obj)
