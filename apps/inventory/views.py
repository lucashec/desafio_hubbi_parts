from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.integrations.auth import ApiKeyAuthentication
from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiParameter
from .models import Part, CSVUpload
from .serializers import PartSerializer, CSVUploadSerializer, CSVUploadStatusSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .tasks import process_csv_upload


class PartViewSet(viewsets.ModelViewSet):
    """
    CRUD para peças
    """
    queryset = Part.objects.all()
    serializer_class = PartSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["quantity"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "price", "name"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ["create", "update", "destroy"]:
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    @extend_schema(
        summary="Listar apenas peças disponíveis em estoque",
        tags=["parts"]
    )
    def available(self, request):
        parts = self.queryset.filter(quantity__gt=0)
        serializer = self.get_serializer(parts, many=True)
        return Response(serializer.data)

class CSVUploadViewSet(viewsets.ModelViewSet):
    queryset = CSVUpload.objects.all()
    serializer_class = CSVUploadSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status"]
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "head", "options", "trace"]
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(uploaded_by=self.request.user)
        return queryset
    @extend_schema(
        request={'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {'type': 'string', 'format': 'binary'}
            }
        }},
        summary="Envio em lote de peças via CSV",
        tags=["csv-uploads"]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        csv_upload = serializer.save(uploaded_by=self.request.user)
        process_csv_upload.delay(csv_upload.id)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    @extend_schema(
        summary="Obter status de processamento de upload CSV",
        tags=["csv-uploads"]
    )
    def status(self, request, pk=None):
        csv_upload = self.get_object()
        serializer = CSVUploadStatusSerializer(csv_upload)
        return Response(serializer.data)

class ExternalCSVUploadViewSet(viewsets.ModelViewSet):
    queryset = CSVUpload.objects.all()
    serializer_class = CSVUploadSerializer
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [AllowAny]
    http_method_names = ["post"]

    @extend_schema(
        request={'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {'type': 'string', 'format': 'binary'}
            }
        }},
        summary="Envio em lote de peças via CSV por um cliente externo",
        parameters=[
            OpenApiParameter(
                name="X_API_Key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="API Key"
            )
        ],
        tags=["external"]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        csv_upload = serializer.save(uploaded_by=None)
        process_csv_upload.delay(csv_upload.id)
    
    @action(detail=True, methods=["get"], authentication_classes = [ApiKeyAuthentication])
    @extend_schema(
        summary="Obter status de processamento de upload CSV",
        parameters=[
            OpenApiParameter(
                name="X_API_Key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="API Key"
            )
        ],
        tags=["external"]
    )
    def status(self, request, pk=None):
        csv_upload = self.get_object()
        serializer = CSVUploadStatusSerializer(csv_upload)
        return Response(serializer.data)
