"""
Redis Queue Service for asynchronous image indexing.

Flow:
1. API receives image → enqueues it to Redis → returns immediately
2. Worker reads from queue → processes CLIP embedding → indexes in Qdrant
3. Worker can scale independently

This keeps API fast (~100ms response) and processing happens in background.
"""

import os
import json
import logging
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("redis-py not installed. Redis queue disabled.")


logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class IndexJob:
    """Represents a single indexing job."""
    job_id: str
    product_id: str
    image_path: Optional[str] = None
    image_bytes: Optional[bytes] = None
    name: str = ""
    description: str = ""
    metadata: Optional[Dict] = None
    created_at: str = None
    status: str = JobStatus.QUEUED
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        d = asdict(self)
        # Don't serialize bytes (send path only)
        d['image_bytes'] = None
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> 'IndexJob':
        """Create from dictionary."""
        return cls(**data)


class RedisQueueService:
    """
    Redis-based queue service for image indexing.
    
    Keeps API fast by offloading heavy work to background worker.
    """

    def __init__(self, redis_url: Optional[str] = None, 
                 queue_name: str = "image_index_queue",
                 status_prefix: str = "job:"):
        """
        Initialize Redis queue service.
        
        Args:
            redis_url: Redis connection URL (default from env or localhost)
            queue_name: Name of the queue key in Redis
            status_prefix: Prefix for job status keys
        """
        self.queue_name = queue_name
        self.status_prefix = status_prefix
        
        # Connection settings
        if redis_url is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        self.redis_url = redis_url
        self.client = None
        
        if REDIS_AVAILABLE:
            try:
                self._connect()
                logger.info(f"✓ Redis queue initialized: {queue_name}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.client = None
        else:
            logger.warning("Redis queue service unavailable (redis-py not installed)")
    
    def _connect(self):
        """Connect to Redis."""
        from redis import from_url
        self.client = from_url(self.redis_url, decode_responses=True)
        # Test connection
        self.client.ping()
    
    def is_available(self) -> bool:
        """Check if Redis is available."""
        try:
            if self.client is None:
                return False
            self.client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}")
            return False
    
    def enqueue_job(self, job: IndexJob) -> bool:
        """
        Add job to queue.
        
        Args:
            job: IndexJob to enqueue
            
        Returns:
            True if successfully queued
        """
        if not self.is_available():
            logger.error("Redis not available for enqueuing")
            return False
        
        try:
            # Store job metadata
            job_key = f"{self.status_prefix}{job.job_id}"
            job_data = job.to_dict()
            
            # Store as JSON
            self.client.hset(
                job_key,
                mapping=job_data
            )
            
            # Set expiration (24 hours)
            self.client.expire(job_key, 86400)
            
            # Add to queue (list)
            self.client.rpush(self.queue_name, job.job_id)
            
            logger.info(f"✓ Job {job.job_id} enqueued: product {job.product_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error enqueuing job: {e}")
            return False
    
    def dequeue_job(self) -> Optional[IndexJob]:
        """
        Get next job from queue (blocking).
        
        Returns:
            IndexJob or None if queue empty
        """
        if not self.is_available():
            return None
        
        try:
            # Pop from left (FIFO), with 1 second timeout
            result = self.client.blpop(self.queue_name, timeout=1)
            
            if result is None:
                return None
            
            queue_name, job_id = result
            
            # Get job details
            job_key = f"{self.status_prefix}{job_id}"
            job_data = self.client.hgetall(job_key)
            
            if not job_data:
                logger.warning(f"Job {job_id} not found in storage")
                return None
            
            job = IndexJob.from_dict(job_data)
            job.status = JobStatus.PROCESSING
            
            # Update status
            self._update_job_status(job)
            
            logger.debug(f"Dequeued job {job.job_id}: product {job.product_id}")
            return job
            
        except Exception as e:
            logger.error(f"Error dequeuing job: {e}")
            return None
    
    def update_job_status(self, job_id: str, status: JobStatus, 
                         error_message: Optional[str] = None) -> bool:
        """
        Update job status.
        
        Args:
            job_id: Job ID
            status: New status
            error_message: Error message if status is FAILED
            
        Returns:
            True if successful
        """
        if not self.is_available():
            return False
        
        try:
            job_key = f"{self.status_prefix}{job_id}"
            
            update_data = {
                "status": status.value,
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            # Update timestamp
            update_data["updated_at"] = datetime.now().isoformat()
            
            self.client.hset(job_key, mapping=update_data)
            
            logger.debug(f"Job {job_id} status: {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
            return False
    
    def _update_job_status(self, job: IndexJob) -> bool:
        """Internal method to update job from object."""
        return self.update_job_status(
            job.job_id,
            JobStatus(job.status),
            job.error_message
        )
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Get job status and details.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job details dict or None
        """
        if not self.is_available():
            return None
        
        try:
            job_key = f"{self.status_prefix}{job_id}"
            job_data = self.client.hgetall(job_key)
            return job_data if job_data else None
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dict with queue stats
        """
        if not self.is_available():
            return {"available": False}
        
        try:
            # Count jobs in each status
            keys = self.client.keys(f"{self.status_prefix}*")
            
            queued = 0
            processing = 0
            completed = 0
            failed = 0
            
            for key in keys:
                job_data = self.client.hgetall(key)
                status = job_data.get("status", JobStatus.QUEUED)
                
                if status == JobStatus.QUEUED:
                    queued += 1
                elif status == JobStatus.PROCESSING:
                    processing += 1
                elif status == JobStatus.COMPLETED:
                    completed += 1
                elif status == JobStatus.FAILED:
                    failed += 1
            
            queue_length = self.client.llen(self.queue_name)
            
            return {
                "available": True,
                "queue_name": self.queue_name,
                "pending_in_queue": queue_length,
                "jobs": {
                    "queued": queued,
                    "processing": processing,
                    "completed": completed,
                    "failed": failed,
                    "total": len(keys)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {"available": False, "error": str(e)}
    
    def retry_failed_job(self, job_id: str) -> bool:
        """
        Retry a failed job.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if re-queued successfully
        """
        if not self.is_available():
            return False
        
        try:
            job_key = f"{self.status_prefix}{job_id}"
            job_data = self.client.hgetall(job_key)
            
            if not job_data:
                logger.error(f"Job {job_id} not found")
                return False
            
            retry_count = int(job_data.get("retry_count", 0))
            max_retries = int(job_data.get("max_retries", 3))
            
            if retry_count >= max_retries:
                logger.warning(f"Job {job_id} exceeded max retries ({max_retries})")
                return False
            
            # Update retry count and reset status
            self.client.hincrby(job_key, "retry_count", 1)
            self.client.hset(job_key, mapping={
                "status": JobStatus.QUEUED,
                "error_message": None
            })
            
            # Re-add to queue
            self.client.rpush(self.queue_name, job_id)
            
            logger.info(f"Job {job_id} re-queued (attempt {retry_count + 1})")
            return True
            
        except Exception as e:
            logger.error(f"Error retrying job: {e}")
            return False
    
    def cleanup_completed_jobs(self, days_old: int = 7) -> int:
        """
        Clean up completed and failed jobs older than N days.
        
        Args:
            days_old: Delete jobs older than this many days
            
        Returns:
            Number of jobs cleaned up
        """
        if not self.is_available():
            return 0
        
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 86400)
            deleted = 0
            
            keys = self.client.keys(f"{self.status_prefix}*")
            
            for key in keys:
                job_data = self.client.hgetall(key)
                status = job_data.get("status")
                created_at_str = job_data.get("created_at", "")
                
                # Only delete completed and failed jobs
                if status not in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    continue
                
                try:
                    created_at = datetime.fromisoformat(created_at_str).timestamp()
                    if created_at < cutoff_time:
                        self.client.delete(key)
                        deleted += 1
                except:
                    pass
            
            logger.info(f"Cleaned up {deleted} old jobs")
            return deleted
            
        except Exception as e:
            logger.error(f"Error cleaning up jobs: {e}")
            return 0


# Singleton instance
_queue_service: Optional[RedisQueueService] = None


def get_redis_queue_service() -> RedisQueueService:
    """Get or create Redis queue service singleton."""
    global _queue_service
    if _queue_service is None:
        _queue_service = RedisQueueService()
    return _queue_service
