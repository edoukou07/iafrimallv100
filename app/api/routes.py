"""
API routes for image and text search using CLIP embeddings + Qdrant.
Everything in one container - no external services.

Async Processing:
- Images are enqueued to Redis for background processing
- Worker processes images → CLIP embedding → Qdrant indexing
- API returns immediately (fast response)
"""
import logging
import uuid
import json
import tempfile
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from typing import Optional, List
from pydantic import BaseModel
from app.services.embedding_service import EmbeddingService
from app.services.image_embedding import get_image_embedding_service
from app.services.integrated_qdrant import get_qdrant_service
from app.services.qdrant_monitoring import QdrantMonitor
from app.services.redis_queue import (
    get_redis_queue_service,
    IndexJob
)
from app.services.voice_service import get_voice_service
from app.services.search_service import SearchService
from app.services.text_preprocessing import TextPreprocessor
from app.services.bm25_search import BM25SearchService
from app.services.hybrid_search import HybridSearchService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["search"])

# Initialize monitoring (lazy - will be set up on first use)
_monitor = None


# Request/Response models
class SearchRequest(BaseModel):
    query: str
    limit: int = 10


class SearchResponse(BaseModel):
    query: str
    results: List[dict]
    count: int


class EmbedRequest(BaseModel):
    text: str


class EmbedResponse(BaseModel):
    text: str
    embedding: List[float]
    dimension: int


# Services
embedding_service = EmbeddingService()
image_embedding_service = get_image_embedding_service()
qdrant_service = get_qdrant_service()
bm25_service = BM25SearchService()
hybrid_search_service = HybridSearchService(bm25_service)


def _get_monitor() -> QdrantMonitor:
    """Get or create monitor instance (lazy initialization)."""
    global _monitor
    if _monitor is None:
        _monitor = QdrantMonitor(qdrant_service)
    return _monitor


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        qdrant_ok = qdrant_service.health_check()
        stats = qdrant_service.get_collection_stats()
        
        return {
            "status": "healthy" if qdrant_ok else "degraded",
            "service": "Image Search API (Container Apps)",
            "version": "3.0",
            "qdrant": {
                "connected": qdrant_ok,
                "stats": stats
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Search for products by text query with improved precision.
    
    Features:
    - Enhanced text preprocessing (cleaning, normalization)
    - Intelligent score threshold (0.3 default for better precision)
    - Optional category filtering
    
    Query Parameters:
    - limit: Max results (default 10)
    - score_threshold: Minimum similarity (default 0.3)
    - category: Filter by category (optional)
    """
    try:
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Preprocess query for better matching
        processed_query = TextPreprocessor.preprocess_query(request.query)
        logger.info(f"Searching for: '{request.query}' (processed: '{processed_query}')")
        
        # Generate CLIP text embedding
        embedding = embedding_service.embed_text(processed_query)
        
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
        # Search in Qdrant with improved parameters
        search_results = qdrant_service.search(
            query_vector=embedding,
            limit=request.limit,
            score_threshold=0.3  # Intelligent threshold for better precision
        )
        
        response = SearchResponse(
            query=request.query,
            results=search_results,
            count=len(search_results)
        )
        
        logger.info(f"Search returned {len(search_results)} results (threshold=0.3)")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/search-hybrid")
async def search_hybrid(
    request: SearchRequest,
    semantic_weight: float = Query(0.7, ge=0.0, le=1.0, description="Weight for semantic search (0-1)"),
    keyword_weight: float = Query(0.3, ge=0.0, le=1.0, description="Weight for keyword search (0-1)")
):
    """
    Hybrid search combining semantic (CLIP) and keyword (BM25) search.
    
    This endpoint combines:
    1. **Semantic Search (CLIP)**: Understands meaning and context
    2. **Keyword Search (BM25)**: Matches exact terms and phrases
    
    The results are fused using weighted scores:
    - Default: 70% semantic + 30% keyword
    - Customize weights via query parameters
    
    Example:
    - "red shoes" → finds both semantically similar items AND items with "red" or "shoes"
    - "cheap electronics" → finds affordable items with electronic keywords
    
    Args:
        query: Search query
        limit: Max results (default 10)
        semantic_weight: Weight for semantic search (default 0.7)
        keyword_weight: Weight for keyword search (default 0.3)
    
    Returns:
        List of products with both semantic_score and keyword_score
    """
    try:
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Normalize weights to sum to 1.0
        total_weight = semantic_weight + keyword_weight
        if total_weight > 0:
            semantic_weight = semantic_weight / total_weight
            keyword_weight = keyword_weight / total_weight
        else:
            semantic_weight, keyword_weight = 0.7, 0.3
        
        # Preprocess query
        processed_query = TextPreprocessor.preprocess_query(request.query)
        logger.info(f"Hybrid search for: '{request.query}' (semantic={semantic_weight:.1%}, keyword={keyword_weight:.1%})")
        
        # Get semantic results from CLIP
        embedding = embedding_service.embed_text(processed_query)
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
        semantic_results = qdrant_service.search(
            query_vector=embedding,
            limit=request.limit * 2,  # Get more for fusion
            score_threshold=0.2  # Lower threshold for fusion
        )
        
        # Perform hybrid fusion
        fused_results = hybrid_search_service.hybrid_search(
            query=processed_query,
            semantic_results=semantic_results,
            limit=request.limit,
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight,
            min_keyword_score=0.1
        )
        
        response = {
            "query": request.query,
            "results": fused_results,
            "count": len(fused_results),
            "method": "hybrid (CLIP + BM25)",
            "weights": {
                "semantic": semantic_weight,
                "keyword": keyword_weight
            }
        }
        
        logger.info(f"Hybrid search returned {len(fused_results)} results")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hybrid search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")
async def get_embedding(request: EmbedRequest):
    """Get CLIP text embedding vector."""
    try:
        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        embedding = embedding_service.embed_text(request.text)
        
        return {
            "text": request.text,
            "embedding": embedding,
            "dimension": len(embedding)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/embed-image")
async def embed_image(file: UploadFile = File(...)):
    """
    Extract CLIP embedding from an image.
    
    Returns:
        - embedding: 512-dimensional CLIP vector
        - dimension: 512
    """
    try:
        # Validate file content type (handle None case)
        content_type = file.content_type or ''
        if not content_type.startswith("image/"):
            # Try to validate by filename extension as fallback
            filename = file.filename or ''
            valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
            has_valid_ext = any(filename.lower().endswith(ext) for ext in valid_extensions)
            
            if not has_valid_ext and not content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        logger.info(f"Processing image: {file.filename} ({len(image_data)} bytes)")
        
        # Generate image embedding using CLIP
        embedding = image_embedding_service.embed_image(image_data)
        
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to process image")
        
        return {
            "image": file.filename,
            "embedding": embedding,
            "dimension": len(embedding),
            "model": "CLIP"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image embedding error: {e}")
        raise HTTPException(status_code=500, detail=f"Image embedding failed: {str(e)}")

@router.post("/index-product")
async def index_product(
    product_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    metadata: str = Form(default="{}")
):
    """
    Index a product for searching.
    Generates CLIP text embedding and stores in Qdrant.
    """
    try:
        # Generate embedding for full text
        full_text = f"{name} {description}"
        embedding = embedding_service.embed_text(full_text)
        
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
        # Parse metadata
        try:
            import json
            metadata_dict = json.loads(metadata)
        except:
            metadata_dict = {}
        
        # Index in Qdrant
        success, qdrant_id = qdrant_service.index_product(
            product_id=product_id,
            name=name,
            description=description,
            embedding=embedding,
            metadata=metadata_dict
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to index product")
        
        return {
            "status": "success",
            "message": f"Product {product_id} indexed successfully",
            "product_id": product_id,
            "qdrant_id": qdrant_id,
            "embedding_dimension": len(embedding)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@router.get("/stats")
async def get_stats():
    """Get collection statistics."""
    try:
        stats = qdrant_service.get_collection_stats()
        return {
            "collection": stats,
            "embedding_service": {
                "type": "TF-IDF",
                "model": "scikit-learn",
                "dimension": embedding_service.get_dimension()
            }
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-image")
async def search_by_image(file: UploadFile = File(...), limit: int = Query(10)):
    """
    Search for similar products by uploading an image.
    Uses CLIP model to extract image embeddings.
    
    Args:
        file: Image file (JPEG, PNG, etc.)
        limit: Maximum number of results to return
    
    Returns:
        List of similar products from database
    """
    try:
        # Validate file content type (handle None case)
        content_type = file.content_type or ''
        if not content_type.startswith("image/"):
            # Try to validate by filename extension as fallback
            filename = file.filename or ''
            valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
            file_ext = ''.join([c for c in filename.lower() if c.isalnum() or c == '.'])
            has_valid_ext = any(filename.lower().endswith(ext) for ext in valid_extensions)
            
            if not has_valid_ext and not content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        logger.info(f"Processing image: {file.filename} ({len(image_data)} bytes)")
        
        # Generate image embedding using CLIP
        embedding = image_embedding_service.embed_image(image_data)
        
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to process image")
        
        # Search similar products in Qdrant
        # For image search, use lower threshold (0.2) because image embeddings are different from text
        search_results = qdrant_service.search(
            query_vector=embedding,
            limit=limit,
            score_threshold=0.2  # Lower threshold for image similarity
        )
        
        response = {
            "query_image": file.filename,
            "results": search_results,
            "count": len(search_results),
            "model": "CLIP",
            "embedding_dimension": len(embedding)
        }
        
        logger.info(f"Image search returned {len(search_results)} results")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image search error: {e}")
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")

@router.post("/index-product-with-image")
async def index_product_with_image(
    product_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    image_file: UploadFile = File(...),
    metadata: str = Form(default="{}")
):
    """
    Queue product image for asynchronous indexing.
    
    ⚡ FAST: Returns immediately (~10ms)
    🔄 ASYNC: Worker processes image in background
    
    Workflow:
    1. Client uploads image → API enqueues to Redis → returns job_id (~10ms)
    2. Worker retrieves job from Redis
    3. Worker: loads image → CLIP embedding → Qdrant indexing
    4. Client polls /api/v1/queue/status/{job_id} for completion
    
    Benefits:
    - API stays responsive (no 5-10 second blocking)
    - Multiple workers can process images in parallel
    - Automatic retry on failure
    - Full transparency (track job status)
    """
    try:
        # Validate file content type (handle None case)
        content_type = image_file.content_type or ''
        if not content_type.startswith("image/"):
            # Try to validate by filename extension as fallback
            filename = image_file.filename or ''
            valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
            has_valid_ext = any(filename.lower().endswith(ext) for ext in valid_extensions)
            
            if not has_valid_ext and not content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image bytes
        image_data = await image_file.read()
        logger.info(f"Enqueuing product {product_id} for image indexing ({len(image_data)} bytes)")
        
        # Parse metadata
        try:
            metadata_dict = json.loads(metadata)
        except:
            metadata_dict = {}
        
        # Create job
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        job = IndexJob(
            job_id=job_id,
            product_id=product_id,
            image_bytes=image_data,
            name=name,
            description=description,
            metadata=metadata_dict
        )
        
        # Save image to temporary file
        try:
            image_path = job.save_image_temp()
            logger.debug(f"Image saved to temporary file: {image_path}")
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")
        
        # Enqueue to Redis
        queue_service = get_redis_queue_service()
        success = queue_service.enqueue_job(job)
        
        if not success:
            logger.warning("Redis queue unavailable - falling back to sync processing")
            # Fallback: process synchronously if Redis not available
            image_embedding_service = get_image_embedding_service()
            qdrant_service = get_qdrant_service()
            
            image_embedding = image_embedding_service.embed_image(image_data)
            if not image_embedding:
                raise HTTPException(status_code=500, detail="Failed to process image")
            
            metadata_dict["has_image"] = True
            qdrant_success, qdrant_id = qdrant_service.index_product(
                product_id=product_id,
                name=name,
                description=description,
                embedding=image_embedding,
                metadata=metadata_dict
            )
            
            if not qdrant_success:
                raise HTTPException(status_code=500, detail="Failed to index product")
            
            return {
                "status": "indexed",
                "job_id": job_id,
                "product_id": product_id,
                "qdrant_id": qdrant_id,
                "message": "Product indexed synchronously (Redis unavailable)",
                "processing_mode": "sync"
            }
        
        return {
            "status": "queued",
            "job_id": job_id,
            "product_id": product_id,
            "message": f"Product queued for indexing. Track status at /api/v1/queue/status/{job_id}",
            "processing_mode": "async",
            "status_url": f"/api/v1/queue/status/{job_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enqueuing product: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.get("/queue/status/{job_id}")
async def get_queue_job_status(job_id: str):
    """
    Get status of an indexing job.
    
    Returns:
    - queued: Job waiting in queue
    - processing: Worker currently processing
    - completed: Successfully indexed
    - failed: Error occurred (check error_message)
    """
    try:
        queue_service = get_redis_queue_service()
        job_data = queue_service.get_job_status(job_id)
        
        if not job_data:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return {
            "job_id": job_id,
            "status": job_data.get("status"),
            "product_id": job_data.get("product_id"),
            "created_at": job_data.get("created_at"),
            "updated_at": job_data.get("updated_at"),
            "retry_count": job_data.get("retry_count", 0),
            "error_message": job_data.get("error_message")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/stats")
async def get_queue_stats():
    """
    Get queue statistics.
    
    Shows:
    - Pending jobs in queue
    - Jobs by status (queued, processing, completed, failed)
    - Total jobs in system
    """
    try:
        queue_service = get_redis_queue_service()
        stats = queue_service.get_queue_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/retry/{job_id}")
async def retry_failed_job(job_id: str):
    """
    Retry a failed indexing job.
    
    Only works for failed jobs that haven't exceeded max retries.
    """
    try:
        queue_service = get_redis_queue_service()
        success = queue_service.retry_failed_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Could not retry job {job_id}"
            )
        
        return {
            "status": "retrying",
            "job_id": job_id,
            "message": "Job re-queued for processing"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying job: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/performance/monitor")
async def monitor_performance():
    """
    Get current performance and resource statistics.
    
    Includes:
    - Memory usage (container and Qdrant cache)
    - Disk usage (database and snapshots)
    - Query latency statistics (avg, p95, p99)
    - Cache hit rate
    - Collection statistics
    - Health status and warnings
    """
    try:
        monitor = _get_monitor()
        stats = monitor.get_performance_stats()
        
        return {
            "timestamp": stats.timestamp.isoformat(),
            "status": "healthy" if stats.is_healthy else "degraded",
            "memory": {
                "container_memory_mb": round(stats.container_memory_mb, 2),
                "container_memory_percent": round(stats.container_memory_percent, 2),
                "qdrant_cache_mb": round(stats.qdrant_cache_mb, 2),
                "message": "RAM-optimized with disk storage"
            },
            "disk": {
                "database_size_mb": round(stats.database_size_mb, 2),
                "snapshots_size_mb": round(stats.snapshots_size_mb, 2),
                "total_mb": round(stats.total_disk_mb, 2)
            },
            "collection": {
                "points_indexed": stats.points_count,
                "vectors_count": stats.vectors_count
            },
            "queries": {
                "avg_latency_ms": round(stats.avg_query_latency_ms, 2),
                "p95_latency_ms": round(stats.p95_query_latency_ms, 2),
                "p99_latency_ms": round(stats.p99_query_latency_ms, 2),
                "cache_hit_rate_percent": round(stats.cache_hit_rate, 2)
            },
            "health": {
                "is_healthy": stats.is_healthy,
                "warnings": stats.warnings
            }
        }
    except Exception as e:
        logger.error(f"Performance monitoring error: {e}")
        raise HTTPException(status_code=500, detail=f"Monitoring failed: {str(e)}")


@router.post("/performance/record-query")
async def record_query_performance(
    latency_ms: float = Query(..., description="Query latency in milliseconds"),
    query_size: int = Query(1, description="Number of results returned"),
    cache_hit: bool = Query(False, description="Whether result was from cache")
):
    """
    Record query performance for monitoring.
    
    Called internally after each search to track performance metrics.
    """
    try:
        monitor = _get_monitor()
        monitor.record_query(
            latency_ms=latency_ms,
            query_size=query_size,
            results_count=query_size,
            cache_hit=cache_hit
        )
        return {"status": "recorded"}
    except Exception as e:
        logger.warning(f"Could not record query performance: {e}")


# ============================================================================
# VOICE SEARCH ENDPOINTS
# ============================================================================

@router.post("/voice-search")
async def voice_search(
    audio_file: UploadFile = File(...),
    language: Optional[str] = Query(None, description="Language code (e.g., 'en', 'fr'). Auto-detected if None"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
):
    """
    Search by voice: transcribe audio → search by text → return results.
    
    - Accepts MP3, WAV, M4A, FLAC, OGG, etc.
    - Transcribes using OpenAI Whisper (high accuracy)
    - Searches Qdrant using transcribed text
    - Returns matching products/images
    
    Args:
        audio_file: Audio file to transcribe
        language: Language code (auto-detected if None)
        limit: Max number of results (default 10)
    
    Returns:
        {
            "transcription": "transcribed text",
            "language": "detected language",
            "confidence": 0.95,
            "results": [...],
            "search_type": "voice"
        }
    """
    try:
        # Get voice service
        voice_service = get_voice_service(model_size="base")
        
        # Save audio file temporarily
        logger.info(f"Received voice search request: filename={audio_file.filename}, content_type={audio_file.content_type}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp_file:
            content = await audio_file.read()
            logger.info(f"Audio content size: {len(content)} bytes")
            tmp_file.write(content)
            tmp_audio_path = tmp_file.name
        
        logger.info(f"Saved to temp file: {tmp_audio_path}")
        
        # Transcribe audio
        transcription_result = voice_service.transcribe(
            tmp_audio_path,
            language=language,
        )
        
        transcript_text = transcription_result["text"]
        detected_language = transcription_result["language"]
        confidence = transcription_result.get("confidence", 0.95)
        
        logger.info(f"[OK] Transcription: '{transcript_text}' (lang={detected_language}, conf={confidence})")
        
        # Preprocess transcribed text for better search
        processed_text = TextPreprocessor.preprocess_query(transcript_text)
        
        # Search using transcribed text (use global embedding_service and qdrant_service)
        embedding = embedding_service.embed_text(processed_text)
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding from transcribed text")
        
        search_results = qdrant_service.search(
            query_vector=embedding,
            limit=limit,
            score_threshold=0.3  # Intelligent threshold
        )
        
        # Flatten results for frontend: extract name/description from nested metadata
        flattened_results = []
        for result in search_results:
            flattened_results.append({
                "id": result.get("id"),
                "name": result.get("metadata", {}).get("name", "Unknown Product"),
                "description": result.get("metadata", {}).get("description", ""),
                "image": result.get("metadata", {}).get("image_url"),
                "score": result.get("score", 0),
            })
        
        logger.info(f"Voice search flattened results: {len(flattened_results)} products")
        if flattened_results:
            logger.info(f"First result: {flattened_results[0]}")
        
        # Clean up temp file
        import os
        try:
            os.remove(tmp_audio_path)
        except:
            pass
        
        return {
            "transcription": transcript_text,
            "language": detected_language,
            "confidence": float(confidence),
            "results": flattened_results,
            "count": len(flattened_results),
            "search_type": "voice",
        }
    
    except Exception as e:
        logger.error(f"Voice search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Voice search failed: {str(e)}"
        )


@router.get("/voice/model-info")
async def voice_model_info():
    """
    Get information about the Whisper model.
    
    Returns model size, supported languages, etc.
    """
    try:
        voice_service = get_voice_service()
        model_info = voice_service.get_model_info()
        return {
            "status": "success",
            "model": model_info,
            "supported_formats": ["MP3", "WAV", "M4A", "FLAC", "OGG", "OPUS"],
        }
    except Exception as e:
        logger.error(f"Could not get model info: {str(e)}", exc_info=True)
        return {
            "status": "warning",
            "message": f"Voice service not ready: {str(e)}",
            "supported_formats": ["MP3", "WAV", "M4A", "FLAC", "OGG", "OPUS"],
        }


@router.get("/health/voice")
async def voice_service_health():
    """
    Health check for voice service.
    """
    try:
        voice_service = get_voice_service()
        return {
            "status": "healthy",
            "service": "voice",
            "model_size": voice_service.model_size,
        }
    except Exception as e:
        logger.error(f"Voice service health check failed: {str(e)}", exc_info=True)
        return {
            "status": "unhealthy",
            "service": "voice",
            "error": str(e),
        }

