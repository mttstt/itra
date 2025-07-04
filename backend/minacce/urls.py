from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MinacciaViewSet

router = DefaultRouter()
router.register(r'', MinacciaViewSet, basename='minaccia')

urlpatterns = [
    path('', include(router.urls)),
]