from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScenarioViewSet

router = DefaultRouter()
router.register(r'', ScenarioViewSet, basename='scenario')

urlpatterns = [
    path('', include(router.urls)),
]