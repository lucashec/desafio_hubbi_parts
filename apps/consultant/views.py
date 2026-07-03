from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiTypes
from services.consultor_ia import processar_query_consultor
from .models import ConsultantQuery, ConsultantResponse
from .serializers import ConsultantQuerySerializer, ConsultantResponseSerializer
import time


class ConsultorView(APIView):
    """
    Endpoint do Consultor de IA.
    POST /api/consultor/ - Submeter uma pergunta
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={
            'type': 'object',
            'properties': {
                'query': {'type': 'string', 'description': 'Pergunta para o consultor de IA'}
            },
            'required': ['query']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'query_id': {'type': 'integer'},
                    'query': {'type': 'string'},
                    'intenção': {'type': 'string'},
                    'resposta': {'type': 'string'},
                    'peças_recomendadas': {'type': 'array', 'items': {'type': 'object'}},
                    'tempo_processamento': {'type': 'number'},
                    'status': {'type': 'string'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'erro': {'type': 'string'}
                }
            },
            500: {
                'type': 'object',
                'properties': {
                    'erro': {'type': 'string'},
                    'status': {'type': 'string'}
                }
            }
        }
    )
    def post(self, request):
        """Processa uma query do consultor."""
        user_query = request.data.get("query", "").strip()

        if not user_query:
            return Response(
                {"erro": "Campo 'query' é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Registra a query
        query_obj = ConsultantQuery.objects.create(
            user=request.user,
            query_text=user_query,
            status="processing"
        )

        try:
            # Processa com IA
            start_time = time.time()
            resultado = processar_query_consultor(user_query)
            processing_time = time.time() - start_time

            # Registra a resposta
            response_obj = ConsultantResponse.objects.create(
                query=query_obj,
                response_text=resultado.get("resposta", ""),
                tokens_used=resultado.get("tokens_usados", 0),
                processing_time=processing_time
            )

            # Atualiza status da query
            query_obj.status = "completed"
            query_obj.save()

            return Response(
                {
                    "query_id": query_obj.id,
                    "query": user_query,
                    "intenção": resultado.get("intenção", ""),
                    "resposta": resultado.get("resposta", ""),
                    "peças_recomendadas": resultado.get("peças_recomendadas", []),
                    "tempo_processamento": processing_time,
                    "status": "success"
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            # Atualiza status com erro
            query_obj.status = "error"
            query_obj.save()

            return Response(
                {
                    "erro": str(e),
                    "status": "erro"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConsultorHistoricoView(APIView):
    """
    Endpoint para obter histórico de queries do usuário.
    GET /api/consultor/historico/
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'query': {'type': 'string'},
                        'status': {'type': 'string'},
                        'criado_em': {'type': 'string', 'format': 'date-time'},
                        'resposta': {'type': 'string'},
                        'tempo_processamento': {'type': 'number'}
                    }
                }
            }
        }
    )
    def get(self, request):
        """Retorna histórico de queries do usuário autenticado."""
        queries = ConsultantQuery.objects.filter(
            user=request.user
        ).select_related("response").order_by("-created_at")

        resultado = []
        for query in queries:
            item = {
                "id": query.id,
                "query": query.query_text,
                "status": query.status,
                "criado_em": query.created_at,
            }
            if hasattr(query, "response") and query.response:
                item["resposta"] = query.response.response_text
                item["tempo_processamento"] = query.response.processing_time
            resultado.append(item)

        return Response(resultado, status=status.HTTP_200_OK)

