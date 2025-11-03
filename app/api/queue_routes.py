"""
Redis Queue Service - API Interface for Task Enqueueing

Provides endpoints to:
1. Enqueue image indexing tasks
2. Track job status
3. Monitor worker health
4. Retrieve job results
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import aioredis
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Redis connection (singleton)
redis_client: Optional[aioredis.Redis] = None

router = APIRouter(prefix="/queue", tags=["Queue"])


class IndexingTask(BaseModel):
    """Task model for image indexing"""
    image_path: str = Field(..., description="Path to the image file")
    product_id: str = Field(..., description="Product identifier")
    name: Optional[str] = Field(None, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class TaskResponse(BaseModel):
    """Response model for enqueued tasks"""
    task_id: str
    status: str
    message: str
    queue_length: Optional[int] = None


class WorkerStatus(BaseModel):
    """Worker status model"""
    worker_id: str
    status: str
    tasks_processed: int
    tasks_failed: int
    last_seen: str


async def get_redis_client():
    """Get or create Redis client"""
    global redis_client
    if redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            redis_client = await aioredis.from_url(
                redis_url,
                encoding="utf8",
                decode_responses=True
            )
            await redis_client.ping()
            logger.info(f"Redis client initialized: {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    return redis_client


@router.post("/enqueue", response_model=TaskResponse)
async def enqueue_task(task: IndexingTask) -> TaskResponse:
    """
    Enqueue an image indexing task to Redis queue
    
    Args:
        task: Indexing task details
        
    Returns:
        Task ID and queue status
        
    Example:
        POST /queue/enqueue
        {
            "image_path": "/path/to/image.jpg",
            "product_id": "prod-123",
            "name": "Product Name",
            "description": "Product description"
        }
    """
    try:
        redis = await get_redis_client()
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Prepare task data
        task_data = {
            "task_id": task_id,
            "image_path": task.image_path,
            "product_id": task.product_id,
            "name": task.name or f"Product {task.product_id}",
            "description": task.description or "",
            "metadata": task.metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        
        # Push to queue
        await redis.rpush(
            "image_indexing_queue",
            json.dumps(task_data)
        )
        
        # Store task info for tracking
        await redis.setex(
            f"task:{task_id}",
            86400,  # Expire in 24 hours
            json.dumps({
                "product_id": task.product_id,
                "created_at": datetime.utcnow().isoformat(),
                "status": "pending"
            })
        )
        
        # Get queue length
        queue_length = await redis.llen("image_indexing_queue")
        
        logger.info(f"Task {task_id} enqueued for product {task.product_id}")
        
        return TaskResponse(
            task_id=task_id,
            status="enqueued",
            message=f"Task {task_id} enqueued successfully",
            queue_length=queue_length
        )
        
    except Exception as e:
        logger.error(f"Error enqueueing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status of a specific task
    
    Args:
        task_id: Task identifier
        
    Returns:
        Task status and details
    """
    try:
        redis = await get_redis_client()
        
        # Try to get task info
        task_info = await redis.get(f"task:{task_id}")
        
        if not task_info:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        data = json.loads(task_info)
        return {
            "task_id": task_id,
            **data
        }
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers")
async def list_workers() -> Dict[str, list]:
    """
    List all active workers and their status
    
    Returns:
        List of worker statuses
    """
    try:
        redis = await get_redis_client()
        
        # Get all worker status keys
        worker_keys = await redis.keys("worker_status:*")
        
        workers = []
        for key in worker_keys:
            status_data = await redis.get(key)
            if status_data:
                workers.append(json.loads(status_data))
        
        return {
            "worker_count": len(workers),
            "workers": workers
        }
        
    except Exception as e:
        logger.error(f"Error listing workers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_queue_stats() -> Dict[str, Any]:
    """
    Get queue statistics
    
    Returns:
        Queue length and worker info
    """
    try:
        redis = await get_redis_client()
        
        # Queue length
        queue_length = await redis.llen("image_indexing_queue")
        
        # Worker count
        worker_keys = await redis.keys("worker_status:*")
        
        # Get all workers for aggregated stats
        total_processed = 0
        total_failed = 0
        active_workers = 0
        
        for key in worker_keys:
            status_data = await redis.get(key)
            if status_data:
                worker_status = json.loads(status_data)
                if worker_status.get("status") == "running":
                    active_workers += 1
                    total_processed += worker_status.get("tasks_processed", 0)
                    total_failed += worker_status.get("tasks_failed", 0)
        
        return {
            "queue_length": queue_length,
            "active_workers": active_workers,
            "total_workers": len(worker_keys),
            "total_tasks_processed": total_processed,
            "total_tasks_failed": total_failed,
            "success_rate": (
                total_processed / (total_processed + total_failed) * 100
                if (total_processed + total_failed) > 0
                else 0
            )
        }
        
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flush")
async def flush_queue() -> Dict[str, str]:
    """
    Clear the entire queue (development only!)
    
    Returns:
        Confirmation message
    """
    try:
        redis = await get_redis_client()
        
        # Delete queue
        deleted = await redis.delete("image_indexing_queue")
        
        logger.warning(f"Queue flushed, deleted {deleted} items")
        
        return {
            "message": "Queue flushed",
            "items_deleted": str(deleted)
        }
        
    except Exception as e:
        logger.error(f"Error flushing queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.on_event("startup")
async def startup():
    """Initialize Redis on startup"""
    try:
        await get_redis_client()
        logger.info("✓ Queue service initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize queue service: {e}")


@router.on_event("shutdown")
async def shutdown():
    """Close Redis connection on shutdown"""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("✓ Queue service closed")

