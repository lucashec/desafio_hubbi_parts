from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiTypes
from .models import Part, CSVUpload
from .serializers import PartSerializer, CSVUploadSerializer, CSVUploadStatusSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .tasks import process_csv_upload


class PartViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar peças.
    Admins podem criar, editar e deletar.
    Usuários autenticados podem listar e visualizar.
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
        responses={
            200: {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'name': {'type': 'string'},
                        'description': {'type': 'string'},
                        'price': {'type': 'string'},
                        'quantity': {'type': 'integer'}
                    }
                }
            }
        }
    )
    def available(self, request):
        """
        Retorna apenas peças disponíveis em estoque.
        GET /api/parts/available/
        """
        parts = self.queryset.filter(quantity__gt=0)
        serializer = self.get_serializer(parts, many=True)
        return Response(serializer.data)


class CSVUploadViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar uploads de CSV assincronos.
    Admins fazem o upload arquivos CSV para importar peças em massa.
    """
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
        request={'multipart/form-data': {'type': 'object', 'properties': {'file': {'type': 'string', 'format': 'binary'}}}},
        summary="Upload CSV file for batch parts import",
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'file': {'type': 'string'},
                    'status': {'type': 'string'},
                    'uploaded_by': {'type': 'integer'},
                    'created_at': {'type': 'string', 'format': 'date-time'}
                }
            }
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        csv_upload = serializer.save(uploaded_by=self.request.user)
        process_csv_upload.delay(csv_upload.id)
    
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    @extend_schema(
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'status': {'type': 'string'},
                    'total_rows': {'type': 'integer'},
                    'processed_rows': {'type': 'integer'},
                    'failed_rows': {'type': 'integer'},
                    'created_at': {'type': 'string', 'format': 'date-time'},
                    'updated_at': {'type': 'string', 'format': 'date-time'}
                }
            }
        }
    )
    def status(self, request, pk=None):
        """
        Retorna o status de processamento de um upload CSV.
        GET /api/csv-uploads/{id}/status/
        """
        csv_upload = self.get_object()
        serializer = CSVUploadStatusSerializer(csv_upload)
        return Response(serializer.data)
