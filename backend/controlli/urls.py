from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ControlloViewSet

router = DefaultRouter()
router.register(r'', ControlloViewSet)

urlpatterns = [
    path('', include(router.urls)),
]