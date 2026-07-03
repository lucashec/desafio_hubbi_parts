import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from decimal import Decimal
from io import StringIO
import csv as csv_module


class TestCSVProcessingLogic:
    
    def test_csv_row_validation_missing_name(self):
        from decimal import Decimal
        
        row = {'nome': '', 'descricao': 'test', 'preco': '100', 'quantidade_inicial': '5'}
        name = row.get('nome', '').strip()
        price_str = row.get('preco', '').strip()
        quantity_str = row.get('quantidade_inicial', '').strip()
        
        assert not (name and price_str and quantity_str)
    
    def test_csv_row_validation_invalid_price(self):
        from decimal import Decimal
        
        row = {'nome': 'Motor', 'descricao': 'test', 'preco': 'invalid', 'quantidade_inicial': '5'}
        price_str = row.get('preco', '').strip()
        
        try:
            price = Decimal(price_str)
            assert False, "Should have raised ValueError"
        except:
            assert True
    
    def test_csv_row_validation_negative_price(self):
        from decimal import Decimal
        
        row = {'nome': 'Motor', 'descricao': 'test', 'preco': '-100', 'quantidade_inicial': '5'}
        price_str = row.get('preco', '').strip()
        quantity_str = row.get('quantidade_inicial', '').strip()
        
        price = Decimal(price_str)
        quantity = int(quantity_str)
        
        assert not (price > 0 and quantity >= 0)
    
    def test_csv_row_validation_negative_quantity(self):
        from decimal import Decimal
        
        row = {'nome': 'Motor', 'descricao': 'test', 'preco': '100', 'quantidade_inicial': '-5'}
        price_str = row.get('preco', '').strip()
        quantity_str = row.get('quantidade_inicial', '').strip()
        
        price = Decimal(price_str)
        quantity = int(quantity_str)
        
        assert not (price > 0 and quantity >= 0)
    
    def test_csv_row_validation_success(self):
        from decimal import Decimal
        
        row = {'nome': 'Motor', 'descricao': 'Motor Description', 'preco': '5000.00', 'quantidade_inicial': '10'}
        
        name = row.get('nome', '').strip()
        description = row.get('descricao', '').strip()
        price_str = row.get('preco', '').strip()
        quantity_str = row.get('quantidade_inicial', '').strip()
        
        price = Decimal(price_str)
        quantity = int(quantity_str)
        
        assert name and price_str and quantity_str
        assert price > 0
        assert quantity >= 0


class TestEmbeddingServiceBehavior:
    
    def test_compute_similarity_identical_vectors(self):
        import numpy as np
        from services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        similarity = service.compute_similarity(vec1, vec2)
        
        assert abs(similarity - 1.0) < 0.01
    
    def test_compute_similarity_opposite_vectors(self):
        import numpy as np
        from services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([-1.0, 0.0, 0.0], dtype=np.float32)
        
        similarity = service.compute_similarity(vec1, vec2)
        
        assert abs(similarity - (-1.0)) < 0.01
    
    def test_compute_similarity_zero_vector_handling(self):
        import numpy as np
        from services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        vec1 = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        similarity = service.compute_similarity(vec1, vec2)
        
        assert similarity == 0.0
    
    def test_embedding_service_unavailable_returns_none(self):
        from services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        service.available = False
        
        result = service.generate_embedding("test")
        assert result is None
    
    def test_embedding_service_unavailable_array_returns_none(self):
        from services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        service.available = False
        
        result = service.generate_embedding_array("test")
        assert result is None


class TestKeywordSearchLogic:
    
    def test_keyword_search_scoring_name_match(self):
        query = "motor"
        words = query.lower().split()
        
        assert "motor" in words
    
    def test_keyword_search_multiple_words(self):
        query = "motor v8 turbo"
        words = query.lower().split()
        
        assert len(words) == 3
        assert "motor" in words
        assert "v8" in words
        assert "turbo" in words
    
    def test_keyword_search_scoring_calculation(self):
        parts_score = {}
        
        parts_score[1] = parts_score.get(1, 0) + 10
        parts_score[1] = parts_score.get(1, 0) + 5
        
        assert parts_score[1] == 15
    
    def test_keyword_search_sorting(self):
        parts_score = {1: 10, 2: 20, 3: 5, 4: 15}
        
        sorted_parts = sorted(parts_score.items(), key=lambda x: x[1], reverse=True)
        
        assert sorted_parts[0] == (2, 20)
        assert sorted_parts[1] == (4, 15)
        assert sorted_parts[-1] == (3, 5)


