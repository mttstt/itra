from django import template

register = template.Library()

# Elenco dei modelli (in minuscolo) che hanno il campo 'campagna' e per cui
# ha senso mantenere il filtro nella navigazione.
CAMPAIGN_AWARE_MODELS = [
    'asset',
    'controllo',
    'elementtype',
    'minaccia',
    'scenario',
    'strutturatemplate',
    'nodotemplate',
    'nodostruttura',
]

@register.simple_tag
def campaign_aware_url(model_admin_url, model_object_name, campaign):
    """
    Aggiunge il parametro di filtro della campagna all'URL se il modello
    è compatibile e se una campagna è attiva nel contesto.
    """
    if campaign and model_object_name.lower() in CAMPAIGN_AWARE_MODELS:
        separator = '&' if '?' in model_admin_url else '?'
        return f"{model_admin_url}{separator}campagna__id__exact={campaign.id}"
    return model_admin_url