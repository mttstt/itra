from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetViewSet, NodoStrutturaViewSet, StrutturaTemplateViewSet

router = DefaultRouter()
router.register(r'assets', AssetViewSet)
router.register(r'nodi-struttura', NodoStrutturaViewSet)
router.register(r'strutture-template', StrutturaTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
]