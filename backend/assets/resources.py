from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Asset, StrutturaTemplate, NodoTemplate, NodoStruttura
from django.contrib.auth.models import User


class AssetResource(resources.ModelResource):
    """
    Risorsa per l'import/export degli Asset.
    Configura i campi ForeignKey per utilizzare campi leggibili (es. username)
    invece degli ID numerici, facilitando la creazione e la modifica dei file di import.
    """
    utente_responsabile = fields.Field(
        column_name='utente_responsabile',
        attribute='utente_responsabile',
        widget=ForeignKeyWidget(User, 'username'))

    responsabile_applicativo = fields.Field(
        column_name='responsabile_applicativo',
        attribute='responsabile_applicativo',
        widget=ForeignKeyWidget(User, 'username'))

    class Meta:
        model = Asset
        # Definisce i campi da includere nel file di import/export
        fields = ('id', 'nome', 'descrizione', 'cmdb', 'status', 'legal_entity', 'campagna', 'template_da_applicare', 'utente_responsabile', 'responsabile_applicativo', 'cloned_from')
        export_order = fields
        # Durante l'import, se una riga con lo stesso ID esiste, verrà aggiornata.
        import_id_fields = ['id']
        skip_unchanged = True
        report_skipped = True

class NodoStrutturaResource(resources.ModelResource):
    class Meta:
        model = NodoStruttura
        fields = ('id', 'asset', 'element_type', 'parent', 'nome_specifico', 'campagna')
        export_order = fields
        import_id_fields = ['id']
        skip_unchanged = True
        report_skipped = True


class StrutturaTemplateResource(resources.ModelResource):
    class Meta:
        model = StrutturaTemplate
        fields = ('id', 'nome', 'descrizione', 'campagna', 'cloned_from')
        export_order = fields
        import_id_fields = ['id']
        skip_unchanged = True
        report_skipped = True

class NodoTemplateResource(resources.ModelResource):
    class Meta:
        model = NodoTemplate
        fields = ('id', 'template', 'element_type', 'parent', 'campagna')
        export_order = fields
        import_id_fields = ['id']
        skip_unchanged = True
        report_skipped = True