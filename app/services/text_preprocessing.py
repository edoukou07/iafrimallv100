"""
Text preprocessing and query enhancement for better search precision
"""
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Enhanced text preprocessing for search queries and product data"""
    
    # Synonyms mapping for query expansion
    SYNONYMS = {
        'shoe': ['shoes', 'footwear', 'sneaker', 'boot', 'sandal'],
        'shirt': ['tshirt', 't-shirt', 'tee', 'top', 'blouse'],
        'pants': ['trousers', 'jeans', 'denim', 'slacks'],
        'buy': ['purchase', 'order', 'get', 'acquire'],
        'cheap': ['affordable', 'inexpensive', 'budget', 'discount'],
        'expensive': ['costly', 'premium', 'luxury', 'high-end'],
        'fast': ['quick', 'rapid', 'speedy', 'swift'],
        'slow': ['sluggish', 'delayed', 'lagging'],
        'good': ['great', 'excellent', 'awesome', 'nice', 'quality'],
        'bad': ['poor', 'terrible', 'awful', 'low-quality'],
    }
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text:
        - Convert to lowercase
        - Remove special characters (keep alphanumeric, spaces, hyphens)
        - Remove extra whitespace
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove special characters but keep hyphens and apostrophes
        text = re.sub(r'[^a-z0-9\s\-\']', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Split text into tokens (words)"""
        return text.split()
    
    @staticmethod
    def remove_stopwords(tokens: List[str], language: str = 'en') -> List[str]:
        """Remove common stopwords"""
        # Minimal stopword list for e-commerce (keep product-relevant words)
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
            'who', 'when', 'where', 'why', 'how'
        }
        
        return [token for token in tokens if token not in stopwords and len(token) > 1]
    
    @classmethod
    def preprocess_query(cls, query: str) -> str:
        """
        Full preprocessing pipeline for search query:
        1. Clean text
        2. Remove stopwords (optional - for better results, keep them for voice)
        
        Returns cleaned query
        """
        cleaned = cls.clean_text(query)
        # For search queries, keep stopwords as they may be important
        # tokens = cls.tokenize(cleaned)
        # tokens = cls.remove_stopwords(tokens)
        # return ' '.join(tokens)
        return cleaned
    
    @classmethod
    def preprocess_product_data(cls, name: str, description: str, category: str = "", tags: str = "") -> str:
        """
        Preprocess product data for indexing:
        Combine name, description, category and tags with proper weighting
        
        Args:
            name: Product name
            description: Product description
            category: Product category
            tags: Additional tags (comma-separated)
        
        Returns:
            Processed full text for embedding
        """
        # Clean each field
        clean_name = cls.clean_text(name)
        clean_desc = cls.clean_text(description)
        clean_cat = cls.clean_text(category)
        clean_tags = cls.clean_text(tags)
        
        # Combine with importance weighting (name appears multiple times)
        # This gives more weight to product name in similarity search
        full_text = f"{clean_name} {clean_name} {clean_cat} {clean_tags} {clean_desc}"
        
        return full_text.strip()
    
    @classmethod
    def expand_query(cls, query: str) -> List[str]:
        """
        Expand query with synonyms for better recall
        
        Example:
            "cheap shoes" -> ["cheap shoes", "affordable shoes", "budget shoes", ...]
        
        Returns:
            List of expanded queries
        """
        cleaned = cls.preprocess_query(query)
        tokens = cls.tokenize(cleaned)
        expanded_queries = [cleaned]  # Original query
        
        # Check each token for synonyms
        for token in tokens:
            if token in cls.SYNONYMS:
                # Create variations with each synonym
                for synonym in cls.SYNONYMS[token]:
                    # Replace token with synonym
                    expanded = cleaned.replace(token, synonym)
                    if expanded not in expanded_queries:
                        expanded_queries.append(expanded)
        
        logger.info(f"Query expansion: '{cleaned}' -> {len(expanded_queries)} variations")
        return expanded_queries
    
    @staticmethod
    def calculate_relevance_score(query: str, product_name: str, product_desc: str) -> float:
        """
        Calculate additional relevance score based on keyword matching
        Used for re-ranking results
        
        Score calculation:
        - Exact match in name: 0.9
        - Partial match in name: 0.7
        - Match in description: 0.5
        """
        query_lower = query.lower()
        name_lower = product_name.lower()
        desc_lower = product_desc.lower()
        
        # Exact match in name
        if query_lower == name_lower:
            return 0.95
        
        # Query is substring of name
        if query_lower in name_lower:
            return 0.85
        
        # All query words in name
        query_words = query_lower.split()
        if all(word in name_lower for word in query_words):
            return 0.80
        
        # Query in description
        if query_lower in desc_lower:
            return 0.60
        
        # Partial word matches
        matches = sum(1 for word in query_words if word in desc_lower)
        if matches > 0:
            return 0.4 + (matches / len(query_words)) * 0.2
        
        return 0.0
