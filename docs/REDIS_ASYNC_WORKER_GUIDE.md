# Redis Async Worker Implementation Guide

## Overview

This implementation provides a **scalable, async-based image indexing system** using:
- **Redis** as the task queue (BLPOP for blocking)
- **Multiple async workers** processing tasks concurrently
- **FastAPI endpoints** for task management
- **Docker Compose** for orchestration

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Server                        │
│  /queue/enqueue - Post indexing tasks                        │
│  /queue/status - Check task status                           │
│  /queue/workers - List active workers                        │
│  /queue/stats - Get queue statistics                         │
└──────────────┬──────────────────────────────────────────────┘
               │ (RPUSH tasks)
               ▼
        ┌──────────────┐
        │    Redis     │ ◄──── BLPOP (blocking)
        │ Task Queue   │
        └──────────────┘
               ▲
     ┌─────────┴─────────┬──────────────┐
     │                   │              │
     ▼                   ▼              ▼
┌─────────┐        ┌─────────┐    ┌─────────┐
│ Worker1 │        │ Worker2 │ .. │ WorkerN │
│(Async)  │        │(Async)  │    │(Async)  │
└────┬────┘        └────┬────┘    └────┬────┘
     │                  │             │
     └──────────────────┼─────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  Qdrant Vector   │
              │   Database       │
              └──────────────────┘
```

### Files Created

1. **`docker-compose.yml`**
   - Redis service with persistence
   - Qdrant vector database
   - API container
   - 2 worker containers (scalable)

2. **`app/workers/image_indexer_worker.py`**
   - Async worker implementation
   - BLPOP queue polling
   - Batch processing support
   - Retry logic with exponential backoff
   - Status reporting to Redis

3. **`app/api/queue_routes.py`**
   - FastAPI routes for queue management
   - Task enqueueing endpoint
   - Status tracking endpoints
   - Worker health monitoring
   - Queue statistics

## Usage

### Starting the System

```bash
# Navigate to project directory
cd iafrimallv100

# Start with Docker Compose
docker-compose up -d

# Check status
docker-compose logs -f api
docker-compose logs -f worker1
```

### Enqueueing Tasks

```bash
# Create an indexing task
curl -X POST http://localhost:8000/queue/enqueue \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "/path/to/image.jpg",
    "product_id": "prod-123",
    "name": "Product Name",
    "description": "Product description",
    "metadata": {"category": "electronics"}
  }'

# Response:
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "enqueued",
  "message": "Task ... enqueued successfully",
  "queue_length": 5
}
```

### Checking Task Status

```bash
curl http://localhost:8000/queue/status/550e8400-e29b-41d4-a716-446655440000
```

### Monitoring Workers

```bash
# List active workers
curl http://localhost:8000/queue/workers

# Get queue statistics
curl http://localhost:8000/queue/stats
```

## Configuration

### Environment Variables

**API/General:**
- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379/0`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

**Worker-specific:**
- `WORKER_ID`: Worker identifier (required)
- `WORKER_POLL_INTERVAL`: Seconds between polls (default: `1`)
- `WORKER_BATCH_SIZE`: Tasks per batch (default: `1`)
- `TASK_TIMEOUT`: Task timeout in seconds (default: `300`)

### Docker Compose Variables

Workers can be configured in `docker-compose.yml`:

```yaml
environment:
  - REDIS_URL=redis://redis:6379/0
  - WORKER_ID=worker-1
  - WORKER_POLL_INTERVAL=1
  - WORKER_BATCH_SIZE=1
  - LOG_LEVEL=INFO
```

## Key Features

### 1. Async/Await

Workers use `asyncio` for high concurrency:
```python
async def process_batch(self) -> int:
    # Collect multiple tasks
    # Process concurrently with gather()
    results = await asyncio.gather(
        *[self.process_task(task) for task in tasks],
        return_exceptions=False
    )
```

### 2. Blocking Queue Polling

Uses Redis `BLPOP` instead of polling:
```python
async def poll_queue(self) -> Optional[Dict]:
    result = await self.redis.blpop(
        "image_indexing_queue",
        timeout=int(self.poll_interval)
    )
    if result:
        queue_name, task_json = result
        return json.loads(task_json)
```

### 3. Automatic Retry

Tasks are retried with exponential backoff:
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def _process_image_task(self, task):
    # Automatically retries on failure
    pass
```

### 4. Status Tracking

Workers report status to Redis:
```python
async def report_status(self):
    status = {
        "worker_id": self.worker_id,
        "timestamp": datetime.utcnow().isoformat(),
        "tasks_processed": self.tasks_processed,
        "tasks_failed": self.tasks_failed,
        "status": "running"
    }
    await self.redis.setex(
        f"worker_status:{self.worker_id}",
        60,  # Expire in 60 seconds
        json.dumps(status)
    )
```

## Scaling

### Adding More Workers

1. **Update `docker-compose.yml`:**
   ```yaml
   worker3:
     build: .
     environment:
       - WORKER_ID=worker-3
       - REDIS_URL=redis://redis:6379/0
     depends_on:
       - redis
     command: python -m app.workers.image_indexer_worker --worker-id worker-3
   ```

2. **Start new worker:**
   ```bash
   docker-compose up -d worker3
   ```

### Increasing Batch Size

Workers can process multiple tasks concurrently:
```bash
# Start worker with batch size of 5
docker run -e WORKER_BATCH_SIZE=5 ...
```

## Performance Considerations

### Queue Polling

- **`BLPOP` with timeout**: Efficient, no CPU spinning
- **Poll interval**: Balance between latency and resource usage
- **Batch processing**: Reduces overhead for high-volume queues

### Retry Strategy

- **Exponential backoff**: `2s → 4s → 8s` (configurable)
- **Max attempts**: 3 by default
- **Task timeout**: 300s default, adjustable per deployment

### Resource Optimization

- **Async workers**: Handle 100s of concurrent tasks
- **Redis persistence**: AOF enabled for durability
- **Status expiry**: 60s for automatic cleanup
- **Task expiry**: 24h for tracking, then auto-delete

## Monitoring

### Check Worker Logs

```bash
# Specific worker
docker-compose logs -f worker1

# All containers
docker-compose logs -f

# Tail last 100 lines
docker-compose logs --tail=100 -f
```

### Redis Queue Size

```bash
# Via redis-cli
docker exec image-search-redis redis-cli LLEN image_indexing_queue

# Via API
curl http://localhost:8000/queue/stats
```

### Worker Health

```bash
# Check which workers are running
docker-compose ps

# Worker status via API
curl http://localhost:8000/queue/workers
```

## Troubleshooting

### Workers Not Processing Tasks

1. **Check Redis connection:**
   ```bash
   docker exec image-search-redis redis-cli ping
   ```

2. **Check worker logs:**
   ```bash
   docker-compose logs worker1 | grep -i error
   ```

3. **Verify queue has tasks:**
   ```bash
   docker exec image-search-redis redis-cli LLEN image_indexing_queue
   ```

### High Task Failure Rate

1. **Check task timeout:**
   - Increase `TASK_TIMEOUT` if tasks are timing out
   - Check log messages for specific errors

2. **Check image paths:**
   - Ensure `image_path` in tasks is valid
   - Check volume mounts in docker-compose

3. **Worker capacity:**
   - Check if workers are overloaded
   - Reduce `BATCH_SIZE` or add more workers

### Memory Usage

1. **Check Redis memory:**
   ```bash
   docker exec image-search-redis redis-cli INFO memory
   ```

2. **Monitor worker memory:**
   ```bash
   docker stats worker1 worker2
   ```

## Development Notes

### Running Locally (No Docker)

```bash
# Install requirements
pip install -r requirements.txt

# Start Redis (requires Redis installed or Docker Redis container)
redis-server

# Start API
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start worker
python -m app.workers.image_indexer_worker --worker-id worker-1
```

### Testing

```bash
# Generate test tasks
curl -X POST http://localhost:8000/queue/enqueue \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "test_image.jpg",
    "product_id": "test-001"
  }'

# Batch test
for i in {1..10}; do
  curl -X POST http://localhost:8000/queue/enqueue \
    -H "Content-Type: application/json" \
    -d "{\"image_path\": \"image$i.jpg\", \"product_id\": \"prod-$i\"}"
done
```

## Next Steps

1. **Implement actual image processing** in `_process_image_task()`
2. **Add authentication** to queue endpoints
3. **Implement persistent job storage** (database instead of Redis-only)
4. **Add monitoring** (Prometheus metrics, etc.)
5. **Add task priority levels** to queue
6. **Implement dead-letter queue** for failed tasks
7. **Add web dashboard** for queue visualization
