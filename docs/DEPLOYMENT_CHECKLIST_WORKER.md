# Redis Async Worker Implementation - Deployment Checklist

## ✅ Completed Components

### Core Implementation
- [x] **Async Redis Worker** (`app/workers/image_indexer_worker.py`)
  - Async/await based architecture
  - BLPOP blocking queue polling
  - Batch task processing
  - Automatic retry with exponential backoff
  - Status reporting to Redis
  - Graceful shutdown handling
  - Full CLI argument support

- [x] **Queue API Endpoints** (`app/api/queue_routes.py`)
  - POST /queue/enqueue - Task enqueueing
  - GET /queue/status/:id - Task status tracking
  - GET /queue/stats - Queue statistics
  - GET /queue/workers - Worker monitoring
  - POST /queue/flush - Queue management

- [x] **Docker Compose Configuration** (`docker-compose.yml`)
  - Redis with persistence (AOF)
  - Qdrant vector database
  - FastAPI application service
  - 2 pre-configured worker services
  - Health checks
  - Networking and volumes

- [x] **Test Suite** (`test_async_worker.py`)
  - Redis connection testing
  - Task enqueueing validation
  - Status tracking verification
  - Queue statistics monitoring
  - Worker health checks
  - Batch task testing
  - Real-time queue monitoring

### Documentation
- [x] `REDIS_ASYNC_WORKER_GUIDE.md` - Complete implementation guide
- [x] `README_ASYNC_WORKER.md` - Quick reference and architecture
- [x] `DEPLOYMENT_CHECKLIST.md` - This file

### Startup Scripts
- [x] `quickstart-redis-worker.sh` - Linux/macOS startup
- [x] `quickstart-redis-worker.bat` - Windows startup
- [x] `requirements-async-worker.txt` - Python dependencies

## 🚀 Pre-Deployment Steps

### 1. Environment Setup
- [ ] Install Docker and Docker Compose
- [ ] Clone/update project repository
- [ ] Verify Python 3.8+ is installed
- [ ] Review `requirements-async-worker.txt` for dependencies

### 2. Configuration
- [ ] Update `docker-compose.yml` with production settings:
  - [ ] Redis memory limits
  - [ ] Worker replicas (increase from 2 if needed)
  - [ ] Resource constraints (CPU, memory)
  - [ ] Volume mount paths for persistence

- [ ] Set environment variables:
  ```bash
  REDIS_URL=redis://redis:6379/0
  LOG_LEVEL=INFO (or DEBUG for troubleshooting)
  WORKER_POLL_INTERVAL=1
  WORKER_BATCH_SIZE=1 (increase for high-volume)
  TASK_TIMEOUT=300 (adjust based on image processing time)
  ```

### 3. Security
- [ ] Change Redis password (update docker-compose.yml and connection strings)
- [ ] Add API authentication to queue endpoints
- [ ] Configure network isolation (no public Redis exposure)
- [ ] Enable Redis persistence with proper file permissions
- [ ] Use HTTPS for API if exposing externally

### 4. Monitoring Setup
- [ ] Configure logging aggregation (ELK, CloudWatch, etc.)
- [ ] Set up alerts for:
  - [ ] Redis connection failures
  - [ ] High task failure rate (>5%)
  - [ ] Queue size exceeding threshold
  - [ ] Worker unavailability

- [ ] Create dashboards for:
  - [ ] Queue length over time
  - [ ] Worker status and count
  - [ ] Task success/failure rates
  - [ ] System resource usage

## 🔧 Deployment Steps

### 1. Build and Start System

**Using Docker Compose (Recommended):**
```bash
# Navigate to project directory
cd iafrimallv100

# Build images
docker-compose build

# Start services
docker-compose up -d

# Verify services
docker-compose ps
```

**Alternative - Manual Start:**
```bash
# Install dependencies
pip install -r requirements-async-worker.txt

# Start Redis container
docker run -d --name redis-worker -p 6379:6379 redis:7-alpine

# Start Qdrant container
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant

# Start API
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start workers
python -m app.workers.image_indexer_worker --worker-id worker-1 &
python -m app.workers.image_indexer_worker --worker-id worker-2 &
```

### 2. Validate Deployment

```bash
# Test Redis connection
docker exec image-search-redis redis-cli ping
# Expected: PONG

# Test API
curl http://localhost:8000/queue/stats
# Expected: JSON with queue statistics

# Check workers
curl http://localhost:8000/queue/workers
# Expected: JSON with worker list
```

### 3. Run Test Suite

```bash
# Full test suite
python test_async_worker.py --test full

# Monitor queue
python test_async_worker.py --monitor 60
```

## ✅ Post-Deployment Verification

### 1. Service Health
- [ ] All containers running: `docker-compose ps`
- [ ] Redis responding: `redis-cli ping` → PONG
- [ ] API responding: `curl http://localhost:8000/queue/stats`
- [ ] Workers reporting status: `curl http://localhost:8000/queue/workers`

### 2. Queue Operations
- [ ] Can enqueue tasks:
  ```bash
  curl -X POST http://localhost:8000/queue/enqueue \
    -H "Content-Type: application/json" \
    -d '{"image_path": "/test.jpg", "product_id": "test-1"}'
  ```

- [ ] Tasks are being processed:
  ```bash
  # Monitor in separate terminal
  python test_async_worker.py --monitor 30
  
  # Enqueue test tasks
  for i in {1..5}; do
    curl -X POST http://localhost:8000/queue/enqueue \
      -H "Content-Type: application/json" \
      -d "{\"image_path\": \"/img$i.jpg\", \"product_id\": \"prod-$i\"}"
  done
  ```

- [ ] Can check task status: `curl http://localhost:8000/queue/status/[task-id]`

### 3. Worker Performance
- [ ] Workers processing tasks without errors
- [ ] Logs show no ERROR entries in normal operation
- [ ] Task success rate > 95%
- [ ] Response time acceptable (check queue/stats)

### 4. Data Persistence
- [ ] Redis data survives container restart:
  ```bash
  # Get queue length before restart
  docker exec image-search-redis redis-cli LLEN image_indexing_queue
  
  # Stop and restart
  docker-compose restart redis
  
  # Verify data is still there
  docker exec image-search-redis redis-cli LLEN image_indexing_queue
  ```

## 📊 Performance Benchmarking

### 1. Baseline Tests
```bash
# Enqueue 1000 tasks and measure time
time for i in {1..1000}; do
  curl -s -X POST http://localhost:8000/queue/enqueue \
    -H "Content-Type: application/json" \
    -d "{\"image_path\": \"/img$i.jpg\", \"product_id\": \"prod-$i\"}" >/dev/null
done
```

### 2. Monitor Performance
- [ ] Queue processing time
- [ ] Worker CPU/memory usage
- [ ] Redis memory usage
- [ ] Network bandwidth

### 3. Load Testing
```bash
# Using Apache Bench
ab -n 1000 -c 10 \
  -p task.json \
  -T application/json \
  http://localhost:8000/queue/enqueue
```

## 🔄 Scaling Operations

### Add More Workers
```bash
# Update docker-compose.yml to add worker3, worker4, etc
# Then start new workers:
docker-compose up -d worker3 worker4

# Verify they registered
curl http://localhost:8000/queue/workers
```

### Increase Worker Capacity
```bash
# For CPU-bound tasks (image processing):
# 1. Increase batch size
# 2. Allocate more CPU resources

# Update in docker-compose.yml or via env:
export WORKER_BATCH_SIZE=5
export TASK_TIMEOUT=600  # Increase if tasks take longer
```

### Handle High Queue Backlog
```bash
# Option 1: Add more workers
docker-compose scale worker=5

# Option 2: Increase batch size and reduce poll interval
docker run -e WORKER_BATCH_SIZE=10 -e WORKER_POLL_INTERVAL=0.5 ...

# Option 3: Add dedicated high-performance worker pool
docker run -e WORKER_ID=fast-worker-1 \
  -e WORKER_BATCH_SIZE=20 \
  --cpus="2" \
  --memory="4g" ...
```

## 🚨 Troubleshooting Checklist

### Workers Not Processing Tasks
- [ ] Check Redis connection: `docker logs [container]`
- [ ] Verify queue has tasks: `redis-cli LLEN image_indexing_queue`
- [ ] Check worker logs: `docker-compose logs worker1`
- [ ] Verify network connectivity: `docker network inspect [network]`

### High Task Failure Rate
- [ ] Check task logs for errors
- [ ] Verify image paths are accessible
- [ ] Increase TASK_TIMEOUT if tasks are timing out
- [ ] Check worker resource limits

### Memory Issues
- [ ] Monitor Redis memory: `redis-cli INFO memory`
- [ ] Set Redis maxmemory policy
- [ ] Monitor worker memory: `docker stats`
- [ ] Reduce batch size if memory constrained

### API Not Responding
- [ ] Check API logs: `docker-compose logs api`
- [ ] Verify port 8000 is not in use
- [ ] Restart API: `docker-compose restart api`
- [ ] Check network connectivity

## 📈 Maintenance Tasks

### Daily
- [ ] Monitor error logs for anomalies
- [ ] Check queue length remains reasonable
- [ ] Verify all workers are running

### Weekly
- [ ] Review task success/failure rates
- [ ] Check system resource usage trends
- [ ] Test failover procedures
- [ ] Backup Redis data

### Monthly
- [ ] Review and optimize batch size settings
- [ ] Update dependencies if security patches available
- [ ] Perform full disaster recovery test
- [ ] Review and adjust capacity based on usage

## 🔐 Security Hardening

### Before Production Deployment
- [ ] Change Redis default password
- [ ] Disable Redis persistence if not needed
- [ ] Set resource limits for containers
- [ ] Configure firewall rules
- [ ] Enable Redis AUTH
- [ ] Use encrypted connections (TLS)
- [ ] Implement API rate limiting
- [ ] Add authentication to API endpoints
- [ ] Configure RBAC if using Kubernetes

### SSL/TLS Setup
```bash
# Generate certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout redis.key -out redis.crt

# Update Redis configuration
# Update API to use HTTPS
```

## 🎯 Success Criteria

The deployment is successful when:
- [x] All containers are running and healthy
- [x] API responds to requests with 200 status
- [x] Tasks can be enqueued and processed
- [x] Workers report status correctly
- [x] No ERROR logs in normal operation
- [x] Queue processes tasks at expected rate
- [x] Test suite passes all tests
- [x] System handles expected load
- [x] Data persists across restarts

## 📝 Sign-Off

- [ ] Deployment completed by: _________________ Date: _______
- [ ] Tested by: _________________ Date: _______
- [ ] Approved for production by: _________________ Date: _______

## 📞 Support Contacts

- **DevOps**: [contact info]
- **Database**: [contact info]
- **Application**: [contact info]
- **On-call**: [contact info]

## 📚 Related Documentation

- `REDIS_ASYNC_WORKER_GUIDE.md` - Implementation guide
- `README_ASYNC_WORKER.md` - Architecture and usage
- `docker-compose.yml` - Infrastructure configuration
- `app/workers/image_indexer_worker.py` - Worker implementation
- `app/api/queue_routes.py` - API endpoints
