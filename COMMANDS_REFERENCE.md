# Redis Async Worker - Useful Commands

## Starting the System

### Windows
```bash
.\quickstart-redis-worker.bat
```

### Linux/macOS
```bash
bash quickstart-redis-worker.sh
```

### Manual Start
```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

## API Endpoints

### Enqueue Single Task
```bash
curl -X POST http://localhost:8000/queue/enqueue \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "/path/to/image.jpg",
    "product_id": "prod-001",
    "name": "Product Name",
    "description": "Product description",
    "metadata": {"category": "electronics"}
  }'
```

### Enqueue Batch Tasks
```bash
# Linux/macOS
for i in {1..10}; do
  curl -X POST http://localhost:8000/queue/enqueue \
    -H "Content-Type: application/json" \
    -d "{\"image_path\": \"/img$i.jpg\", \"product_id\": \"prod-$i\"}" &
done
wait

# Windows PowerShell
for ($i = 1; $i -le 10; $i++) {
  $body = @{
    image_path = "/img$i.jpg"
    product_id = "prod-$i"
  } | ConvertTo-Json
  curl -X POST http://localhost:8000/queue/enqueue `
    -H "Content-Type: application/json" `
    -d $body
}
```

### Check Task Status
```bash
curl http://localhost:8000/queue/status/{TASK_ID}
```

### Get Queue Statistics
```bash
curl http://localhost:8000/queue/stats
```

### List Active Workers
```bash
curl http://localhost:8000/queue/workers
```

### Format JSON Output (requires jq)
```bash
curl http://localhost:8000/queue/stats | jq .
curl http://localhost:8000/queue/workers | jq '.workers[] | {worker_id, status, tasks_processed}'
```

## Testing

### Run Full Test Suite
```bash
python test_async_worker.py --test full
```

### Test Specific Functionality
```bash
# Redis connection only
python test_async_worker.py --test redis

# Task enqueueing
python test_async_worker.py --test enqueue

# Queue statistics
python test_async_worker.py --test stats

# Worker status
python test_async_worker.py --test workers

# Batch task creation
python test_async_worker.py --test batch
```

### Monitor Queue in Real-time
```bash
# 60-second continuous monitoring
python test_async_worker.py --monitor 60

# 5-minute monitoring
python test_async_worker.py --monitor 300
```

## Docker Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker1
docker-compose logs -f redis

# Last 100 lines
docker-compose logs --tail=100 -f

# Specific timestamp
docker-compose logs --since 2024-01-15T10:00:00
```

### Manage Services
```bash
# Stop all services
docker-compose down

# Stop specific service
docker-compose stop api

# Restart service
docker-compose restart worker1

# View service status
docker-compose ps

# Remove volumes (data loss!)
docker-compose down -v
```

### Scale Workers
```bash
# Scale to 5 worker instances
docker-compose up -d --scale worker=5

# Scale back to 2
docker-compose up -d --scale worker=2
```

### Execute Commands in Container
```bash
# Redis CLI
docker exec -it image-search-redis redis-cli

# Python shell in worker
docker exec -it image-search-worker-1 python

# Check container processes
docker exec image-search-api ps aux
```

## Redis Commands

### Connect to Redis
```bash
docker exec -it image-search-redis redis-cli
```

### Once in Redis CLI
```bash
# Check connection
ping

# Queue length
LLEN image_indexing_queue

# View all keys
KEYS *

# View worker status
GET worker_status:worker-1

# Delete a key
DEL image_indexing_queue

# Monitor Redis in real-time
MONITOR

# Get memory info
INFO memory

# Get stats
INFO stats

# Exit
QUIT
```

## Performance Testing

### Load Generation
```bash
# Create 1000 tasks
for i in {1..1000}; do
  curl -s -X POST http://localhost:8000/queue/enqueue \
    -H "Content-Type: application/json" \
    -d "{\"image_path\": \"/img$i.jpg\", \"product_id\": \"prod-$i\"}" >/dev/null &
done
wait
```

### Monitor While Loading
```bash
# In separate terminal
while true; do
  STATS=$(curl -s http://localhost:8000/queue/stats)
  echo "$(date): $(echo $STATS | jq '.queue_length,.total_tasks_processed')"
  sleep 1
done
```

### Benchmark with Apache Bench
```bash
# Generate task JSON
echo '{
  "image_path": "/test.jpg",
  "product_id": "test-001",
  "name": "Test",
  "description": "Test"
}' > task.json

# Run benchmark
ab -n 1000 -c 10 \
  -p task.json \
  -T application/json \
  http://localhost:8000/queue/enqueue
```

## Monitoring & Diagnostics

### Check Worker Health
```bash
curl http://localhost:8000/queue/workers | jq '.workers[] | select(.status == "running")'
```

### Monitor Task Processing
```bash
# Monitor loop
while true; do
  clear
  echo "=== Queue Status ==="
  curl -s http://localhost:8000/queue/stats | jq '{queue_length, active_workers, total_tasks_processed, total_tasks_failed}'
  sleep 2
done
```

### Check System Resources
```bash
# Docker container resources
docker stats --no-stream

# Continuous monitoring
docker stats

# Specific container
docker stats image-search-api
```

### Check Logs for Errors
```bash
# Recent errors
docker-compose logs | grep -i error

# Errors from specific service
docker-compose logs worker1 | grep -i error

# Follow errors in real-time
docker-compose logs -f 2>&1 | grep -i error
```

## Maintenance

### Backup Redis Data
```bash
# Copy Redis data file
docker cp image-search-redis:/data/dump.rdb ./redis_backup_$(date +%s).rdb

# Backup entire volume
docker run --rm -v image-search_redis_data:/data \
  -v $(pwd):/backup \
  busybox tar czf /backup/redis_backup.tar.gz /data
```

### Clear Queue (Development Only!)
```bash
# Via API
curl -X POST http://localhost:8000/queue/flush

# Via Redis CLI
docker exec -it image-search-redis redis-cli DEL image_indexing_queue
```

### Health Check
```bash
# API health
curl http://localhost:8000/docs

# Redis health
docker exec image-search-redis redis-cli ping

# Qdrant health
curl http://localhost:6333/health

# Quick check script
bash -c '
  echo "Checking API..."
  curl -s http://localhost:8000/queue/stats > /dev/null && echo "  ✓ API OK" || echo "  ✗ API DOWN"
  
  echo "Checking Redis..."
  docker exec image-search-redis redis-cli ping > /dev/null && echo "  ✓ Redis OK" || echo "  ✗ Redis DOWN"
  
  echo "Checking Qdrant..."
  curl -s http://localhost:6333/health > /dev/null && echo "  ✓ Qdrant OK" || echo "  ✗ Qdrant DOWN"
'
```

## Troubleshooting

### Restart Everything
```bash
# Soft restart (keeps data)
docker-compose restart

# Hard restart (removes containers, keeps volumes)
docker-compose down && docker-compose up -d

# Complete reset (loses all data!)
docker-compose down -v && docker-compose up -d
```

### Check Connectivity
```bash
# Test Redis from API
docker exec image-search-api python -c "import redis; r = redis.Redis.from_url('redis://redis:6379/0'); print(r.ping())"

# Test from worker
docker exec image-search-worker-1 python -c "import aioredis; print('aioredis installed')"
```

### View Worker Details
```bash
# Get all worker information
curl -s http://localhost:8000/queue/workers | jq '.'

# List worker IDs only
curl -s http://localhost:8000/queue/workers | jq '.workers[].worker_id'

# Check specific worker
curl -s http://localhost:8000/queue/workers | jq '.workers[] | select(.worker_id == "worker-1")'
```

### Increase Logging
```bash
# Set debug logging in docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG

# Restart services
docker-compose restart

# View debug logs
docker-compose logs -f worker1 | grep DEBUG
```

## Development Commands

### Start Services Individually
```bash
# Terminal 1: Start Redis
docker run -p 6379:6379 redis:7-alpine

# Terminal 2: Start API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3: Start Worker 1
python -m app.workers.image_indexer_worker --worker-id worker-1

# Terminal 4: Start Worker 2
python -m app.workers.image_indexer_worker --worker-id worker-2

# Terminal 5: Run tests
python test_async_worker.py --monitor 60
```

### Debug Worker
```bash
# Run with verbose logging
LOG_LEVEL=DEBUG python -m app.workers.image_indexer_worker --worker-id debug-worker-1

# Run with increased timeout
python -m app.workers.image_indexer_worker --worker-id debug-worker-1 --task-timeout 600

# Run batch mode (process queue and exit)
python -m app.workers.image_indexer_worker --worker-id debug --batch-mode --max-jobs 10
```

### Profile Performance
```bash
# Generate load and monitor
python test_async_worker.py --test batch  # Enqueue 3 tasks

# Monitor real-time
python test_async_worker.py --monitor 30

# Check resource usage
docker stats --no-stream
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `docker-compose up -d` | Start all services |
| `docker-compose down` | Stop all services |
| `docker-compose logs -f` | View all logs |
| `curl http://localhost:8000/queue/stats` | Get queue stats |
| `curl http://localhost:8000/queue/workers` | List workers |
| `python test_async_worker.py --test full` | Run tests |
| `python test_async_worker.py --monitor 60` | Monitor 60 seconds |
| `docker exec -it image-search-redis redis-cli` | Redis CLI |
| `docker exec image-search-redis redis-cli LLEN image_indexing_queue` | Queue length |
| `docker compose ps` | Service status |

## Aliases (Optional)

Add these to your shell profile for convenience:

```bash
# Linux/macOS (~/.bashrc or ~/.zshrc)
alias worker-start='docker-compose up -d'
alias worker-stop='docker-compose down'
alias worker-logs='docker-compose logs -f'
alias worker-test='python test_async_worker.py --test full'
alias worker-monitor='python test_async_worker.py --monitor 60'
alias worker-status='curl -s http://localhost:8000/queue/stats | jq .'
alias worker-ps='docker-compose ps'

# PowerShell Profile (find with: $PROFILE)
New-Alias -Name worker-start -Value 'docker-compose up -d'
New-Alias -Name worker-stop -Value 'docker-compose down'
New-Alias -Name worker-logs -Value 'docker-compose logs -f'
New-Alias -Name worker-test -Value 'python test_async_worker.py --test full'
```

Usage: `worker-start`, `worker-stop`, `worker-logs`, etc.
