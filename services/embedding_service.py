import numpy as np
import logging
from typing import Optional, List
from datetime import datetime
from sentence_transformers import SentenceTransformer
from django.conf import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.available = True
    
    def _ensure_model_loaded(self):
        """Lazy-load model on first use to avoid unnecessary loading."""
        if self.model is None:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.error(f"Failed to load embedding model: {str(e)}")
                self.available = False
                self.model = None
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a given text as list (pgvector compatible)."""
        if not self.available:
            logger.warning("Embedding service not available")
            return None
        
        self._ensure_model_loaded()
        
        if not self.model:
            return None
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32).tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def generate_embedding_array(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding as numpy array."""
        if not self.available:
            return None
        
        self._ensure_model_loaded()
        
        if not self.model:
            return None
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def compute_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        if vec1 is None or vec2 is None:
            return 0.0
        
        try:
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(np.dot(vec1, vec2) / (norm1 * norm2))
        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            return 0.0


_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        model_name = getattr(settings, "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        _embedding_service = EmbeddingService(model_name)
    return _embedding_service
