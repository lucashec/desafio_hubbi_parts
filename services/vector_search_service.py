import logging
import numpy as np
from typing import List, Dict, Tuple
from apps.inventory.models import Part
from .embedding_service import get_embedding_service
from django.db.models import F

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Service for semantic search using embeddings (RAG) with pgvector."""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
    
    def search_parts_by_query(self, query: str, top_k: int = 10, min_score: float = 0.3) -> List[Dict]:
        """
        Search for parts using semantic similarity with RAG (pgvector).
        
        Args:
            query: User query text
            top_k: Number of results to return
            min_score: Minimum similarity score threshold
            
        Returns:
            List of parts with similarity scores
        """
        if not self.embedding_service.available:
            logger.warning("Embedding service not available, falling back to keyword search")
            return self._keyword_search(query, top_k)
        
        query_embedding = self.embedding_service.generate_embedding_array(query)
        if query_embedding is None:
            logger.warning("Failed to generate query embedding")
            return self._keyword_search(query, top_k)
        
        try:
            from pgvector.django import CosineDistance
            
            results = []
            parts = (
                Part.objects
                .filter(quantity__gt=0, embedding__isnull=False)
                .annotate(distance=CosineDistance('embedding', query_embedding.tolist()))
                .order_by('distance')[:top_k]
            )
            
            for part in parts:
                similarity = 1 - part.distance
                if similarity >= min_score:
                    results.append({
                        "id": part.id,
                        "name": part.name,
                        "description": part.description,
                        "price": str(part.price),
                        "quantity": part.quantity,
                        "supplier": part.supplier.name if part.supplier else "Unknown",
                        "similarity_score": float(similarity)
                    })
            
            if results:
                logger.info(f"Found {len(results)} parts using vector search")
                return results
            
            logger.warning("No similar parts found, falling back to keyword search")
            return self._keyword_search(query, top_k)
            
        except Exception as e:
            logger.error(f"Error during vector search: {str(e)}, falling back to keyword search")
            return self._keyword_search(query, top_k)
    
    def _generate_and_save_embedding(self, part: Part) -> bool:
        """Generate and save embedding for a part using pgvector."""
        try:
            text = f"{part.name} {part.description}".strip()
            
            embedding = self.embedding_service.generate_embedding(text)
            if embedding:
                from django.utils import timezone
                part.embedding = embedding
                part.embedding_model = self.embedding_service.model_name
                part.embedding_updated_at = timezone.now()
                part.save(update_fields=['embedding', 'embedding_model', 'embedding_updated_at'])
                logger.info(f"Generated embedding for part {part.id}")
                return True
        except Exception as e:
            logger.error(f"Error generating embedding for part {part.id}: {str(e)}")
        
        return False
    
    def _keyword_search(self, query: str, top_k: int) -> List[Dict]:
        """Fallback keyword search when embeddings unavailable."""
        logger.info("Using keyword search fallback")
        
        words = query.lower().split()
        parts_score = {}
        
        for word in words:
            parts = Part.objects.filter(
                name__icontains=word,
                quantity__gt=0
            )
            for part in parts:
                parts_score[part.id] = parts_score.get(part.id, 0) + 10
        
        for word in words:
            parts = Part.objects.filter(
                description__icontains=word,
                quantity__gt=0
            )
            for part in parts:
                parts_score[part.id] = parts_score.get(part.id, 0) + 5
        
        results = []
        for part_id, score in sorted(parts_score.items(), key=lambda x: x[1], reverse=True)[:top_k]:
            try:
                part = Part.objects.get(id=part_id)
                results.append({
                    "id": part.id,
                    "name": part.name,
                    "description": part.description,
                    "price": str(part.price),
                    "quantity": part.quantity,
                    "supplier": part.supplier.name if part.supplier else "Unknown",
                    "similarity_score": float(score) / 100.0
                })
            except Part.DoesNotExist:
                pass
        
        return results
    
    def regenerate_all_embeddings(self) -> Tuple[int, int]:
        """Regenerate embeddings for all parts."""
        if not self.embedding_service.available:
            logger.error("Embedding service not available")
            return 0, 0
        
        success = 0
        failed = 0
        
        parts = Part.objects.all()
        for part in parts:
            if self._generate_and_save_embedding(part):
                success += 1
            else:
                failed += 1
        
        logger.info(f"Regenerated embeddings: {success} success, {failed} failed")
        return success, failed


def get_vector_search_service() -> VectorSearchService:
    """Get instance of vector search service."""
    return VectorSearchService()
