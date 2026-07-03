import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from django.test import TestCase
from apps.inventory.models import Part
from services.vector_search_service import VectorSearchService, get_vector_search_service
from services.embedding_service import EmbeddingService, get_embedding_service
from services.consultor_ia import ConsultorIA, processar_query_consultor


class TestEmbeddingServiceUnit:
    
    def test_embedding_service_initialization(self):
        service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")
        assert service is not None
        assert service.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert service.available is True
    
    @patch('services.embedding_service.SentenceTransformer')
    def test_ensure_model_loaded(self, mock_transformer):
        mock_model = Mock()
        mock_transformer.return_value = mock_model
        
        service = EmbeddingService()
        service._ensure_model_loaded()
        
        mock_transformer.assert_called()
        assert service.model == mock_model
    
    @patch('services.embedding_service.SentenceTransformer')
    def test_generate_embedding_success(self, mock_transformer):
        mock_model = Mock()
        mock_embedding = np.array([0.1, 0.2, 0.3, 0.4])
        mock_model.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_model
        
        service = EmbeddingService()
        service._ensure_model_loaded()
        result = service.generate_embedding("test text")
        
        assert result is not None
        assert isinstance(result, list)
        mock_model.encode.assert_called_once()
    
    @patch('services.embedding_service.SentenceTransformer')
    def test_generate_embedding_array(self, mock_transformer):
        mock_model = Mock()
        mock_embedding = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        mock_model.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_model
        
        service = EmbeddingService()
        service._ensure_model_loaded()
        result = service.generate_embedding_array("test text")
        
        assert result is not None
        assert isinstance(result, np.ndarray)
    
    def test_generate_embedding_when_unavailable(self):
        service = EmbeddingService()
        service.available = False
        result = service.generate_embedding("test text")
        
        assert result is None
    
    def test_compute_similarity_valid_vectors(self):
        service = EmbeddingService()
        vec1 = np.array([1, 0, 0], dtype=np.float32)
        vec2 = np.array([1, 0, 0], dtype=np.float32)
        
        similarity = service.compute_similarity(vec1, vec2)
        
        assert abs(similarity - 1.0) < 0.01
    
    def test_compute_similarity_orthogonal_vectors(self):
        service = EmbeddingService()
        vec1 = np.array([1, 0, 0], dtype=np.float32)
        vec2 = np.array([0, 1, 0], dtype=np.float32)
        
        similarity = service.compute_similarity(vec1, vec2)
        
        assert abs(similarity - 0.0) < 0.01
    
    def test_compute_similarity_with_none_vectors(self):
        service = EmbeddingService()
        similarity = service.compute_similarity(None, np.array([1, 0, 0]))
        assert similarity == 0.0
        
        similarity = service.compute_similarity(np.array([1, 0, 0]), None)
        assert similarity == 0.0


@pytest.mark.django_db
class TestVectorSearchService(TestCase):
    
    def setUp(self):
        self.mock_model = Mock()
        self.service = VectorSearchService(model=self.mock_model)
        
        self.part1 = Part.objects.create(
            name="Motor V8",
            description="Motor V8 3.0L",
            price=Decimal("5000.00"),
            quantity=5
        )
        self.part2 = Part.objects.create(
            name="Filtro de Óleo",
            description="Filtro de óleo sintético",
            price=Decimal("50.00"),
            quantity=10
        )
        self.part3 = Part.objects.create(
            name="Turbo",
            description="Turbocompressor",
            price=Decimal("2000.00"),
            quantity=0
        )
    
    def test_vector_search_service_initialization(self):
        assert self.service is not None
        assert self.service.embedding_service is not None
    
    def test_search_parts_by_query_keyword_fallback(self):
        self.service.embedding_service.available = False
        
        results = self.service.search_parts_by_query("Motor", top_k=5)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0]["name"] == "Motor V8"
    
    def test_keyword_search_multiple_results(self):
        results = self.service._keyword_search("óleo", top_k=5)
        
        assert isinstance(results, list)
        assert len(results) > 0
    
    def test_keyword_search_no_results(self):
        results = self.service._keyword_search("inexistente", top_k=5)
        
        assert len(results) == 0
    
    def test_keyword_search_excludes_out_of_stock(self):
        results = self.service._keyword_search("turbo", top_k=5)
        
        assert len(results) == 0
    
    @patch.object(VectorSearchService, '_generate_and_save_embedding')
    def test_regenerate_all_embeddings(self, mock_generate):
        mock_generate.side_effect = [True, True, False]
        
        success, failed = self.service.regenerate_all_embeddings()
        
        assert success == 2
        assert failed == 1


@pytest.mark.django_db
class TestConsultorIA(TestCase):
    
    def setUp(self):
        self.consultor = ConsultorIA()
        Part.objects.create(
            name="Motor V8",
            description="Motor V8 3.0L",
            price=Decimal("5000.00"),
            quantity=5
        )
        Part.objects.create(
            name="Filtro de Óleo",
            description="Filtro de óleo sintético",
            price=Decimal("50.00"),
            quantity=10
        )
    
    def test_consultor_ia_initialization(self):
        assert self.consultor is not None
    
    def test_extrair_intencao_fallback(self):
        result = self.consultor._extrair_intencao_fallback("Procuro um motor")
        
        assert result is not None
        assert "intenção" in result
        assert "palavras-chave" in result
        assert "sinônimos" in result
    
    def test_extrair_intencao_motor(self):
        result = self.consultor._extrair_intencao("Preciso de um motor")
        
        assert result is not None
        assert result.get("intenção", "").lower() == "motor"
    
    def test_extrair_intencao_filtro(self):
        result = self.consultor._extrair_intencao("Qual filtro vocês têm?")
        
        assert result is not None
        assert result.get("intenção", "").lower() == "filtro"
    
    def test_buscar_pecas_com_sinonimia_motor(self):
        result = self.consultor._buscar_peças_com_sinonímia(["motor", "v8"])
        
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_buscar_pecas_com_sinonimia_no_results(self):
        result = self.consultor._buscar_peças_com_sinonímia(["inexistente"])
        
        assert len(result) == 0
    
    def test_gerar_resposta_fallback(self):
        parts = [{
            "id": 1,
            "name": "Motor V8",
            "price": "5000.00",
            "quantity": 5,
            "similarity_score": 0.9
        }]
        
        response = self.consultor._gerar_resposta_fallback(parts, "motor")
        
        assert response is not None
        assert "Motor V8" in response
    
    def test_gerar_resposta_fallback_no_parts(self):
        response = self.consultor._gerar_resposta_fallback([], "inexistente")
        
        assert response is not None
        assert "não encontrei" in response.lower()
    
    def test_processar_query_consultor(self):
        result = processar_query_consultor("Procuro um motor")
        
        assert result is not None
        assert "query" in result
        assert "resposta" in result
        assert "peças_recomendadas" in result

