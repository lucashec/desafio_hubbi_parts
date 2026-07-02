import numpy as np
import logging
from typing import Optional
from datetime import datetime
from sentence_transformers import SentenceTransformer
from django.conf import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        try:
            self.model = SentenceTransformer(model_name)
            self.available = True
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            self.available = False
            self.model = None
    
    def generate_embedding(self, text: str) -> Optional[bytes]:
        """Generate embedding for a given text."""
        if not self.available or not self.model:
            logger.warning("Embedding service not available")
            return None
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32).tobytes()
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def generate_embedding_array(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding as numpy array."""
        if not self.available or not self.model:
            return None
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def bytes_to_array(self, embedding_bytes: bytes) -> np.ndarray:
        """Convert embedding bytes back to numpy array."""
        if not embedding_bytes:
            return None
        
        try:
            dtype = np.float32
            return np.frombuffer(embedding_bytes, dtype=dtype)
        except Exception as e:
            logger.error(f"Error converting bytes to array: {str(e)}")
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
