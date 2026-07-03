from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
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


class ExternalPartSearchView(APIView):
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="query",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Search query for parts"
            ),
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Maximum number of results (default: 10)"
            )
        ],
    )
    def get(self, request):
        query = request.query_params.get('query', '').strip()
        limit = int(request.query_params.get('limit', 10))
        
        if not query:
            return Response(
                {'error': 'Parâmetro "query" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start_time = time.time()
        
        parts = Part.objects.filter(
            name__icontains=query
        )[:limit]
        
        processing_time = time.time() - start_time
        
        api_key = request.auth
        IntegrationLog.objects.create(
            api_key=api_key,
            action='search_parts',
            status='success',
            payload={'query': query, 'limit': limit},
            response={'count': parts.count()},
            processing_time=processing_time
        )
        
        serializer = PartSerializer(parts, many=True)
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        })


class ExternalPartDetailView(APIView):    
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="part_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Part ID"
            )
        ],
    )
    def get(self, request, part_id):
        start_time = time.time()
        api_key = request.auth
        
        try:
            part = Part.objects.get(id=part_id)
            processing_time = time.time() - start_time
            
            IntegrationLog.objects.create(
                api_key=api_key,
                action='get_part_detail',
                status='success',
                payload={'part_id': part_id},
                response={'name': part.name, 'price': str(part.price)},
                processing_time=processing_time
            )
            
            serializer = PartSerializer(part)
            return Response(serializer.data)
        
        except Part.DoesNotExist:
            processing_time = time.time() - start_time
            IntegrationLog.objects.create(
                api_key=api_key,
                action='get_part_detail',
                status='error',
                payload={'part_id': part_id},
                error_message=f'Part with id {part_id} not found',
                processing_time=processing_time
            )
            return Response(
                {'error': 'Peça não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )


class ExternalInventoryUpdateView(APIView):
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=InventoryUpdateSerializer,
        summary="Atualizar quantidade de peça no estoque",
        tags=["external", "inventory"]
    )
    def post(self, request):
        start_time = time.time()
        api_key = request.auth
        
        part_id = request.data.get('part_id')
        quantity_delta = request.data.get('quantity_delta')
        
        if not part_id or quantity_delta is None:
            return Response(
                {'error': 'part_id e quantity_delta são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            part = Part.objects.get(id=part_id)
            old_quantity = part.quantity
            part.quantity += int(quantity_delta)
            
            if part.quantity < 0:
                processing_time = time.time() - start_time
                IntegrationLog.objects.create(
                    api_key=api_key,
                    action='update_inventory',
                    status='error',
                    payload={'part_id': part_id, 'quantity_delta': quantity_delta},
                    error_message='Quantidade resultante não pode ser negativa',
                    processing_time=processing_time
                )
                return Response(
                    {'error': 'Quantidade resultante não pode ser negativa'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            part.save()
            processing_time = time.time() - start_time
            
            IntegrationLog.objects.create(
                api_key=api_key,
                action='update_inventory',
                status='success',
                payload={'part_id': part_id, 'quantity_delta': quantity_delta},
                response={
                    'part_id': part.id,
                    'old_quantity': old_quantity,
                    'new_quantity': part.quantity
                },
                processing_time=processing_time
            )
            
            serializer = PartSerializer(part)
            return Response(serializer.data)
        
        except Part.DoesNotExist:
            processing_time = time.time() - start_time
            IntegrationLog.objects.create(
                api_key=api_key,
                action='update_inventory',
                status='error',
                payload={'part_id': part_id, 'quantity_delta': quantity_delta},
                error_message=f'Part with id {part_id} not found',
                processing_time=processing_time
            )
            return Response(
                {'error': 'Peça não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )


class StockUpdateView(APIView):
    @extend_schema(
        summary="Envio em lote de peças via csv",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        parameters=[
            OpenApiParameter(
                name="X_API_Key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="API Key"
            )
        ],
    )
    def put(self, request):
        return Response(
            {"message": "Atualização de estoque será implementada na próxima etapa"},
            status=status.HTTP_200_OK,
        )
