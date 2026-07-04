from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
import time

from .models import ApiKey, IntegrationLog
from .serializers import ApiKeySerializer, IntegrationLogSerializer, InventoryUpdateSerializer
from .auth import ApiKeyAuthentication
from apps.inventory.models import Part
from apps.inventory.serializers import PartSerializer


class ApiKeyViewSet(viewsets.ModelViewSet):
    """
    Módulo para criar chaves de API para integrações externas
    """    
    queryset = ApiKey.objects.all()
    serializer_class = ApiKeySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "last_used_at"]
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "head", "options", "trace"]
    
    @extend_schema(
        summary="Desabilita uma API Key",
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminUser])
    def deactivate(self, request, pk=None):
        api_key = self.get_object()
        api_key.is_active = False
        api_key.save()
        serializer = self.get_serializer(api_key)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Habilita uma API Key",
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminUser])
    def activate(self, request, pk=None):
        api_key = self.get_object()
        api_key.is_active = True
        api_key.save()
        serializer = self.get_serializer(api_key)
        return Response(serializer.data)


class IntegrationLogViewSet(viewsets.ReadOnlyModelViewSet):   
    """
    Módulo para restrear as ações de um client conectado via API Key
    """
    queryset = IntegrationLog.objects.all()
    serializer_class = IntegrationLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["api_key", "status", "action"]
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]

class ExternalInventoryUpdateView(APIView):
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [AllowAny]

    @extend_schema(
        request=InventoryUpdateSerializer(many=True),
        summary="Atualização em lote de estoque (quantidade absoluta)",
        tags=["external"]
    )
    def post(self, request):
        start_time = time.time()
        api_key = request.auth

        payload = request.data

        if not isinstance(payload, list):
            return Response(
                {"error": "Payload deve ser uma lista de objetos"},
                status=status.HTTP_400_BAD_REQUEST
            )

        part_ids = [item.get("part_id") for item in payload if item.get("part_id")]

        parts = Part.objects.filter(id__in=part_ids)
        parts_map = {p.id: p for p in parts}

        updates = []
        logs = []
        not_found = []

        for item in payload:
            part_id = item.get("part_id")
            quantity = item.get("quantity")

            if not part_id:
                logs.append(
                    IntegrationLog(
                        api_key=api_key,
                        action="update_inventory",
                        status="error",
                        payload=item,
                        error_message="part_id é obrigatório",
                        processing_time=time.time() - start_time,
                    )
                )
                continue

            part = parts_map.get(part_id)

            if not part:
                not_found.append({
                    "part_id": part_id,
                    "error": "Part not found"
                })

                logs.append(
                    IntegrationLog(
                        api_key=api_key,
                        action="update_inventory",
                        status="error",
                        payload=item,
                        error_message=f"Part {part_id} não encontrada",
                        processing_time=time.time() - start_time,
                    )
                )
                continue

            if quantity is None:
                logs.append(
                    IntegrationLog(
                        api_key=api_key,
                        action="update_inventory",
                        status="error",
                        payload=item,
                        error_message="quantity é obrigatório",
                        processing_time=time.time() - start_time,
                    )
                )
                continue

            new_quantity = int(quantity)

            if new_quantity < 0:
                logs.append(
                    IntegrationLog(
                        api_key=api_key,
                        action="update_inventory",
                        status="error",
                        payload=item,
                        error_message="Quantidade não pode ser negativa",
                        processing_time=time.time() - start_time,
                    )
                )
                continue

            old_quantity = part.quantity
            part.quantity = new_quantity
            updates.append(part)

            logs.append(
                IntegrationLog(
                    api_key=api_key,
                    action="update_inventory",
                    status="success",
                    payload=item,
                    response={
                        "part_id": part.id,
                        "old_quantity": old_quantity,
                        "new_quantity": new_quantity,
                    },
                    processing_time=time.time() - start_time,
                )
            )

        if updates:
            Part.objects.bulk_update(updates, ["quantity"])

        IntegrationLog.objects.bulk_create(logs)

        return Response(
            {
                "updated": len(updates),
                "errors": len(logs) - len(updates),
                "not_found": not_found
            },
            status=status.HTTP_207_MULTI_STATUS
        )
