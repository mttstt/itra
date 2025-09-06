from rest_framework import viewsets
from .models import Campagna
from .serializers import CampagnaSerializer
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models import Q
from assets.models import NodoTemplate, NodoStruttura

class CampagnaViewSet(viewsets.ModelViewSet):
    queryset = Campagna.objects.all()
    serializer_class = CampagnaSerializer

@staff_member_required
def campagna_dashboard_view(request, campagna_id):
    """
    Vista per il dashboard di una specifica campagna, accessibile dall'admin.
    """
    # Recupera la campagna.
    campagna = get_object_or_404(Campagna, pk=campagna_id)

    # Esegue i conteggi con query separate e più semplici per migliorare le prestazioni.
    # Annotare più conteggi in una singola query può essere molto lento a causa dei JOIN complessi.
    # I related_name sono definiti nei rispettivi modelli e .count() è efficiente.
    campagna = Campagna.objects.annotate(
        controlli_count=Count('controlli'),
        minacce_count=Count('minacce'),
        scenari_count=Count('scenari'),
        elementtypes_count=Count('elementtypes'),
        assets_count=Count('assets'),

        nodistruttura_count = Count('nodistruttura', filter=Q(campagna=campagna)),
    ).get(pk=campagna_id)

    # Aggiungi i conteggi per assets e template di struttura
    campagna.strutture_template_count = campagna.templates_struttura.count()
    campagna.noditemplate_count = NodoTemplate.objects.filter(campagna=campagna).count()


    
    context = {
        'title': f'Dashboard: {campagna.descrizione}',
        'campagna': campagna,
        'site_header': 'IT Risk Administrator',
        'site_title': 'IT Risk Administrator',
        'has_permission': True,
    }
    return render(request, 'admin/campagne/dashboard.html', context)
