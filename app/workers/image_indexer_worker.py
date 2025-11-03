#!/usr/bin/env python3
"""
Async Redis-based Worker for Image Indexing

Features:
- Async/await for high concurrency
- Redis BLPOP for blocking queue polling
- Batch processing of indexing jobs
- Automatic retry with exponential backoff
- Status reporting to Redis
- Graceful shutdown handling

Usage:
    python -m app.workers.image_indexer_worker --worker-id worker-1

Environment Variables:
    REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
    LOG_LEVEL: Logging level (default: INFO)
"""

import asyncio
import json
import logging
import os
import sys
import argparse
from datetime import datetime
from typing import Optional, Dict, Any

try:
    import redis
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AsyncImageIndexerWorker:
    """Async worker for processing image indexing tasks from Redis queue"""

    def __init__(
        self,
        redis_url: str,
        worker_id: str,
        poll_interval: float = 1.0,
        batch_size: int = 1,
        task_timeout: int = 300
    ):
        """
        Initialize the async worker.
        
        Args:
            redis_url: Redis connection URL
            worker_id: Unique worker identifier
            poll_interval: Seconds between queue polls
            batch_size: Number of tasks to process per batch
            task_timeout: Task execution timeout in seconds
        """
        if aioredis is None:
            raise ImportError("redis is required. Install with: pip install redis")
            
        self.redis_url = redis_url
        self.worker_id = worker_id
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.task_timeout = task_timeout
        self.redis: Optional[aioredis.Redis] = None
        self.running = False
        self.tasks_processed = 0
        self.tasks_failed = 0
        logger.info(
            f"Worker {worker_id} initialized: "
            f"poll_interval={poll_interval}s, batch_size={batch_size}"
        )

    async def connect(self) -> None:
        """Establish Redis connection"""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf8",
                decode_responses=True
            )
            await self.redis.ping()
            logger.info(f"✓ Connected to Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"✗ Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info(f"✓ Disconnected from Redis")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _process_image_task(self, task: Dict[str, Any]) -> bool:
        """
        Process an image indexing task with retry logic.
        
        Args:
            task: Task data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        task_id = task.get("task_id", "unknown")
        try:
            logger.debug(f"Processing task {task_id}")
            
            # Simulate image processing (replace with actual logic)
            await asyncio.sleep(0.1)
            
            logger.info(f"✓ Task {task_id} processed successfully")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error processing task {task_id}: {e}")
            raise

    async def process_task(self, task: Dict[str, Any]) -> bool:
        """
        Process a single task with timeout and error handling.
        
        Args:
            task: Task data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        task_id = task.get("task_id", "unknown")
        try:
            logger.info(f"Processing task {task_id}")
            
            if not task.get("image_path"):
                logger.error(f"Task {task_id}: Missing image_path")
                return False

            # Process with timeout
            try:
                result = await asyncio.wait_for(
                    self._process_image_task(task),
                    timeout=self.task_timeout
                )
                
                if result:
                    self.tasks_processed += 1
                    logger.info(f"✓ Task {task_id} completed")
                    return True
                else:
                    self.tasks_failed += 1
                    logger.error(f"✗ Task {task_id} processing returned False")
                    return False
                    
            except asyncio.TimeoutError:
                self.tasks_failed += 1
                logger.error(f"✗ Task {task_id} exceeded timeout ({self.task_timeout}s)")
                return False

        except Exception as e:
            self.tasks_failed += 1
            logger.error(f"✗ Unexpected error in task {task_id}: {e}", exc_info=True)
            return False

    async def poll_queue(self) -> Optional[Dict[str, Any]]:
        """
        Poll Redis queue for tasks using BLPOP (blocking pop).
        
        Returns:
            Task dictionary or None if timeout
        """
        try:
            # BLPOP blocks until element available or timeout
            result = await self.redis.blpop(
                "image_indexing_queue",
                timeout=int(self.poll_interval)
            )
            
            if result:
                queue_name, task_json = result
                return json.loads(task_json)
            return None
            
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"✗ Error polling queue: {e}")
            return None

    async def process_batch(self) -> int:
        """
        Process a batch of tasks concurrently.
        
        Returns:
            Number of tasks processed
        """
        tasks = []
        
        # Collect tasks for batch
        for _ in range(self.batch_size):
            task = await self.poll_queue()
            if task:
                tasks.append(task)
            else:
                break

        if not tasks:
            return 0

        logger.info(f"Processing batch: {len(tasks)} tasks")
        
        # Process tasks concurrently
        results = await asyncio.gather(
            *[self.process_task(task) for task in tasks],
            return_exceptions=False
        )
        
        successful = sum(1 for r in results if r)
        logger.info(f"Batch complete: {successful}/{len(tasks)} successful")
        
        return len(tasks)

    async def report_status(self) -> None:
        """Report worker status to Redis with expiry"""
        try:
            status = {
                "worker_id": self.worker_id,
                "timestamp": datetime.utcnow().isoformat(),
                "tasks_processed": self.tasks_processed,
                "tasks_failed": self.tasks_failed,
                "status": "running" if self.running else "stopped"
            }
            
            await self.redis.setex(
                f"worker_status:{self.worker_id}",
                60,  # Expire after 60 seconds
                json.dumps(status)
            )
            
        except Exception as e:
            logger.error(f"✗ Error reporting status: {e}")

    async def run(self) -> None:
        """Main worker event loop"""
        logger.info(f"▶ Starting worker {self.worker_id}")
        self.running = True
        
        status_report_interval = 30
        last_status_report = datetime.utcnow()
        
        try:
            while self.running:
                try:
                    # Report status periodically
                    now = datetime.utcnow()
                    if (now - last_status_report).total_seconds() >= status_report_interval:
                        await self.report_status()
                        last_status_report = now
                    
                    # Process tasks
                    tasks_processed = await self.process_batch()
                    
                    if tasks_processed == 0:
                        # No tasks, brief sleep before retry
                        await asyncio.sleep(self.poll_interval)
                        
                except KeyboardInterrupt:
                    logger.info(f"⏹ Worker {self.worker_id} received interrupt")
                    self.running = False
                except Exception as e:
                    logger.error(f"✗ Error in worker loop: {e}", exc_info=True)
                    await asyncio.sleep(self.poll_interval)
                    
        finally:
            await self.report_status()
            logger.info(
                f"⏹ Worker stopped. Stats - "
                f"Processed: {self.tasks_processed}, "
                f"Failed: {self.tasks_failed}"
            )

    async def shutdown(self) -> None:
        """Graceful shutdown"""
        logger.info(f"Shutting down worker {self.worker_id}...")
        self.running = False
        await self.disconnect()


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Async Redis-based image indexer worker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables:
  REDIS_URL              Redis connection URL (default: redis://localhost:6379/0)
  LOG_LEVEL              Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
  WORKER_POLL_INTERVAL   Seconds between queue polls (default: 1)
  WORKER_BATCH_SIZE      Tasks per batch (default: 1)
  TASK_TIMEOUT           Task timeout in seconds (default: 300)
        """
    )
    parser.add_argument(
        "--worker-id",
        type=str,
        required=True,
        help="Unique worker identifier (required)"
    )
    parser.add_argument(
        "--redis-url",
        type=str,
        default=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        help="Redis connection URL"
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=float(os.getenv("WORKER_POLL_INTERVAL", "1.0")),
        help="Seconds between queue polls"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.getenv("WORKER_BATCH_SIZE", "1")),
        help="Number of tasks to process per batch"
    )
    parser.add_argument(
        "--task-timeout",
        type=int,
        default=int(os.getenv("TASK_TIMEOUT", "300")),
        help="Task execution timeout in seconds"
    )
    return parser.parse_args()


async def main():
    """Main async entry point"""
    args = parse_arguments()
    
    logger.info("=" * 60)
    logger.info(f"Async Image Indexer Worker")
    logger.info("=" * 60)
    
    worker = AsyncImageIndexerWorker(
        redis_url=args.redis_url,
        worker_id=args.worker_id,
        poll_interval=args.poll_interval,
        batch_size=args.batch_size,
        task_timeout=args.task_timeout
    )
    
    try:
        await worker.connect()
        await worker.run()
    except Exception as e:
        logger.error(f"✗ Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await worker.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
