from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ElementTypeViewSet, ValoreElementTypeViewSet

router = DefaultRouter()
router.register(r'', ElementTypeViewSet, basename='elementtype')
router.register(r'valori', ValoreElementTypeViewSet, basename='valoreelementtype')

urlpatterns = [
    path('', include(router.urls)),
]