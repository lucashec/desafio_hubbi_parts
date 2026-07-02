from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PartViewSet, CSVUploadViewSet

router = DefaultRouter()
router.register(r"parts", PartViewSet, basename="part")
router.register(r"csv-uploads", CSVUploadViewSet, basename="csv-upload")

urlpatterns = [
    path("", include(router.urls)),
]
