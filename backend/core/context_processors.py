from django.urls import resolve
from campagne.models import Campagna

def current_campagna(request):
    """
    Aggiunge la campagna corrente al contesto se l'utente si trova
    in una pagina relativa a una campagna specifica. Controlla sia
    i kwargs dell'URL che i parametri GET.
    """
    campagna_id = None
    try:
        # Prova a prenderlo dai parametri della URL (es. per il dashboard)
        match = resolve(request.path_info)
        if 'campagna_id' in match.kwargs:
            campagna_id = match.kwargs['campagna_id']

        # Prova a prenderlo dai parametri GET (es. per le viste elenco filtrate)
        if not campagna_id:
            campagna_id = request.GET.get('campagna__id__exact')

        if campagna_id:
            return {'current_campagna': Campagna.objects.get(pk=campagna_id)}

    except (Campagna.DoesNotExist, ValueError, Exception):
        # Ignora se l'ID non è valido, non trovato o per altri errori di risoluzione URL
        return {}
    return {}