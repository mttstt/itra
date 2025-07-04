from django.contrib import admin
from django.utils.translation import gettext_lazy as _

class MasterCampaignFilter(admin.SimpleListFilter):
    """
    Filtro personalizzato per visualizzare solo i record master (campagna=NULL)
    o tutti i record (master e clonati) nelle liste di amministrazione.
    Di default, mostra solo i record master.
    """
    title = _('Tipo di Record')
    parameter_name = 'record_type'

    def lookups(self, request, model_admin):
        # Store the model_admin instance so it's available in the queryset method.
        # This is a robust way to access model_admin in both methods.
        self.model_admin_instance = model_admin
        return [
            (None, _('Per Contesto')),
            ('master', _('Record Master')),
            ('all', _('Tutti i Record')),
        ]

    def choices(self, changelist):
        # Override to make 'Per Contesto' the default selected choice
        yield {
            'selected': self.value() is None,
            'query_string': changelist.get_query_string(remove=[self.parameter_name]),
            'display': _('Per Contesto'),
        }
        for lookup, title in self.lookup_choices:
            if lookup is None:
                continue
            yield {
                'selected': self.value() == str(lookup),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}),
                'display': title,
            }

    def queryset(self, request, queryset):
        # Use the stored model_admin instance from lookups.
        lookup_path = getattr(self.model_admin_instance, 'campaign_lookup', 'campagna')
        isnull_lookup = f"{lookup_path}__isnull"

        specific_param_name = f"{lookup_path}__id__exact"
        generic_campaign_param = 'campagna__id__exact'
        campagna_id_from_url = request.GET.get(specific_param_name) or request.GET.get(generic_campaign_param)

        if self.value() == 'all':
            return queryset

        if self.value() == 'master':
            return queryset.filter(**{isnull_lookup: True})

        # Default behavior for 'Per Contesto' (self.value() is None)
        if self.value() is None:
            if campagna_id_from_url:
                return queryset.filter(**{f"{lookup_path}__id": campagna_id_from_url})
            else:
                return queryset.filter(**{isnull_lookup: True})

        return queryset