from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExternalCSVUploadViewSet, PartViewSet, CSVUploadViewSet

router = DefaultRouter()
router.register(r"parts", PartViewSet, basename="part")
router.register(r"csv-uploads", CSVUploadViewSet, basename="csv-upload")
router.register(r"external/csv-uploads", ExternalCSVUploadViewSet, basename="external-csv-upload")

urlpatterns = [
    path("", include(router.urls)),
]
