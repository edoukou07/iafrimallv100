"""
Hybrid search combining BM25 (keyword) and CLIP (semantic) search
Uses reciprocal rank fusion to combine rankings
"""
import logging
from typing import List, Dict, Tuple
from app.services.bm25_search import BM25SearchService

logger = logging.getLogger(__name__)


class HybridSearchService:
    """Combine BM25 keyword search with CLIP semantic search"""
    
    def __init__(self, bm25_service: BM25SearchService):
        """
        Initialize hybrid search
        
        Args:
            bm25_service: BM25 search service for keyword matching
        """
        self.bm25_service = bm25_service
    
    @staticmethod
    def reciprocal_rank_fusion(
        semantic_results: List[Dict],
        keyword_results: List[Tuple[str, float]],
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict]:
        """
        Fuse semantic and keyword search results using Reciprocal Rank Fusion
        
        Args:
            semantic_results: List of results from CLIP search with 'id' and 'score'
            keyword_results: List of (product_id, bm25_score) tuples
            semantic_weight: Weight for semantic search score (default 0.7 = 70%)
            keyword_weight: Weight for keyword search score (default 0.3 = 30%)
        
        Returns:
            Fused and ranked results
        """
        
        # Create score dictionaries
        semantic_scores = {}
        for i, result in enumerate(semantic_results):
            product_id = str(result.get("id"))
            score = result.get("score", 0)
            semantic_scores[product_id] = score
        
        keyword_scores = {}
        for product_id, score in keyword_results:
            product_id = str(product_id)
            keyword_scores[product_id] = score
        
        # Normalize scores to 0-1 range
        max_semantic = max(semantic_scores.values()) if semantic_scores else 1
        max_keyword = max(keyword_scores.values()) if keyword_scores else 1
        
        if max_semantic == 0:
            max_semantic = 1
        if max_keyword == 0:
            max_keyword = 1
        
        # Fuse scores
        fused_scores = {}
        all_ids = set(semantic_scores.keys()) | set(keyword_scores.keys())
        
        for product_id in all_ids:
            sem_score = semantic_scores.get(product_id, 0) / max_semantic
            kw_score = keyword_scores.get(product_id, 0) / max_keyword
            
            # Weighted fusion
            fused_score = (sem_score * semantic_weight) + (kw_score * keyword_weight)
            fused_scores[product_id] = fused_score
        
        logger.info(f"Fused {len(all_ids)} results: {len(semantic_scores)} semantic + {len(keyword_scores)} keyword")
        
        return fused_scores
    
    def hybrid_search(
        self,
        query: str,
        semantic_results: List[Dict],
        limit: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        min_keyword_score: float = 0.1
    ) -> List[Dict]:
        """
        Perform hybrid search combining semantic and keyword results
        
        Args:
            query: Search query string
            semantic_results: Results from CLIP semantic search
            limit: Max results to return
            semantic_weight: Weight for semantic search (default 0.7)
            keyword_weight: Weight for keyword search (default 0.3)
            min_keyword_score: Minimum BM25 score threshold
        
        Returns:
            Fused results with combined scores, sorted by fused_score
        """
        
        # Get keyword-based results
        keyword_results = self.bm25_service.search(
            query=query,
            limit=limit * 2,  # Get more for fusion
            min_score=min_keyword_score
        )
        
        # Fuse the scores
        fused_scores = self.reciprocal_rank_fusion(
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight
        )
        
        # Create final results by enriching with original data
        final_results = []
        
        # Add all fused results
        for product_id, fused_score in fused_scores.items():
            # Find original semantic result for this product
            original_result = None
            for result in semantic_results:
                if str(result.get("id")) == str(product_id):
                    original_result = result
                    break
            
            if original_result:
                # Use original result but update score with fused score
                result_copy = original_result.copy()
                result_copy["fused_score"] = fused_score
                result_copy["semantic_score"] = original_result.get("score", 0)
                
                # Add keyword score if available
                for kw_id, kw_score in keyword_results:
                    if str(kw_id) == str(product_id):
                        result_copy["keyword_score"] = kw_score
                        break
                
                final_results.append(result_copy)
        
        # Sort by fused score
        final_results.sort(key=lambda x: x.get("fused_score", 0), reverse=True)
        
        # Return top limit
        return final_results[:limit]
