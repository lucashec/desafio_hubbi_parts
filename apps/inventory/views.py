from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
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
    Admins podem upload arquivos CSV para importar peças em massa.
    """
    
    queryset = CSVUpload.objects.all()
    serializer_class = CSVUploadSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status"]
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(uploaded_by=self.request.user)
        return queryset
    
    def perform_create(self, serializer):
        csv_upload = serializer.save(uploaded_by=self.request.user)
        process_csv_upload.delay(csv_upload.id)
    
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def status(self, request, pk=None):
        """
        Retorna o status de processamento de um upload CSV.
        GET /api/csv-uploads/{id}/status/
        """
        csv_upload = self.get_object()
        serializer = CSVUploadStatusSerializer(csv_upload)
        return Response(serializer.data)
