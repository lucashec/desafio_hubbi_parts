from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ApiKeyViewSet,
    IntegrationLogViewSet,
    ExternalInventoryUpdateView
)

router = DefaultRouter()
router.register(r'api-keys', ApiKeyViewSet, basename='api-key')
router.register(r'integration-logs', IntegrationLogViewSet, basename='integration-log')

urlpatterns = [
    path('', include(router.urls)),
    path('external/inventory/update/', ExternalInventoryUpdateView.as_view(), name='external-inventory-update'),
]
