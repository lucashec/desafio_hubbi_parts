from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ApiKeyViewSet,
    IntegrationLogViewSet,
    StockUpdateView,
    ExternalPartSearchView,
    ExternalPartDetailView,
    ExternalInventoryUpdateView
)

router = DefaultRouter()
router.register(r'api-keys', ApiKeyViewSet, basename='api-key')
router.register(r'integration-logs', IntegrationLogViewSet, basename='integration-log')

urlpatterns = [
    path('', include(router.urls)),
    path('integrations/stock-update/', StockUpdateView.as_view(), name='stock-update'),
    path('external/parts/search/', ExternalPartSearchView.as_view(), name='external-parts-search'),
    path('external/parts/<int:part_id>/', ExternalPartDetailView.as_view(), name='external-part-detail'),
    path('external/inventory/update/', ExternalInventoryUpdateView.as_view(), name='external-inventory-update'),
]
