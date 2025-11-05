"""
BM25 keyword search service for hybrid search
BM25 is a probabilistic retrieval model that ranks documents based on query terms
"""
import logging
from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


class BM25SearchService:
    """BM25-based keyword search for hybrid search"""
    
    def __init__(self):
        """Initialize BM25 service"""
        self.bm25 = None
        self.corpus = []  # List of product dicts with name, description
        self.corpus_ids = []  # Corresponding product IDs
        
    def index_products(self, products: List[Dict]) -> None:
        """
        Index products for BM25 search
        
        Args:
            products: List of product dicts with 'id', 'name', 'description'
        """
        self.corpus = []
        self.corpus_ids = []
        
        for product in products:
            product_id = product.get("id")
            name = product.get("name", "").lower()
            description = product.get("description", "").lower()
            category = product.get("category", "").lower()
            
            # Combine all text fields
            full_text = f"{name} {category} {description}"
            
            # Tokenize (split by space)
            tokens = full_text.split()
            
            self.corpus.append(tokens)
            self.corpus_ids.append(product_id)
        
        # Build BM25 index
        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)
            logger.info(f"BM25 indexed {len(self.corpus)} products")
        else:
            logger.warning("No products to index in BM25")
    
    def search(self, query: str, limit: int = 10, min_score: float = 0.1) -> List[Tuple[str, float]]:
        """
        Search for products using BM25
        
        Args:
            query: Search query
            limit: Max results to return
            min_score: Minimum BM25 score threshold
        
        Returns:
            List of (product_id, bm25_score) tuples sorted by score descending
        """
        if not self.bm25:
            logger.warning("BM25 not indexed yet")
            return []
        
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Get BM25 scores for all products
        scores = self.bm25.get_scores(query_tokens)
        
        # Create result list with product IDs and scores
        results = []
        for idx, score in enumerate(scores):
            if score >= min_score:
                product_id = self.corpus_ids[idx]
                results.append((product_id, float(score)))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top limit results
        return results[:limit]
    
    def normalize_scores(self, scores: List[float]) -> List[float]:
        """
        Normalize BM25 scores to 0-1 range
        
        Args:
            scores: List of BM25 scores
        
        Returns:
            Normalized scores (0-1)
        """
        if not scores:
            return []
        
        max_score = max(scores)
        if max_score == 0:
            return [0.0] * len(scores)
        
        return [s / max_score for s in scores]
