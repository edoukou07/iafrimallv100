# Redis Queue + Async Worker Guide

## Architecture Overview

Traditional blocking approach (before):
```
Client → API (5-10 seconds waiting) → CLIP + Qdrant → Response
```

New async approach (after):
```
Client → API (10ms enqueue) → Response
           ↓
        Redis Queue
           ↓
        Worker (background) → CLIP + Qdrant → Job complete
```

---

## How It Works

### 1. Client Uploads Image

```bash
curl -X POST http://localhost:8000/api/v1/index-product-with-image \
  -F "product_id=sku-12345" \
  -F "name=Amazing Product" \
  -F "description=High quality item" \
  -F "image_file=@product.jpg"
```

### 2. API Enqueues Job (Fast)

```json
Response (< 20ms):
{
  "status": "queued",
  "job_id": "job-abc123def456",
  "product_id": "sku-12345",
  "message": "Product queued for indexing",
  "processing_mode": "async",
  "status_url": "/api/v1/queue/status/job-abc123def456"
}
```

### 3. Worker Processes (Background)

```
Worker reads from Redis queue:
  1. Load image (100-200 KB)
  2. Generate CLIP embedding (100-200 ms)
  3. Index in Qdrant (50-100 ms)
  4. Mark job complete
Total: ~200-300 ms per image
```

### 4. Client Checks Status

```bash
# Poll for completion
curl http://localhost:8000/api/v1/queue/status/job-abc123def456

# Response when processing:
{
  "job_id": "job-abc123def456",
  "status": "processing",
  "product_id": "sku-12345"
}

# Response when complete:
{
  "job_id": "job-abc123def456",
  "status": "completed",
  "product_id": "sku-12345"
}
```

---

## Setup & Installation

### 1. Install Redis

**Local (Docker):**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Windows (WSL):**
```bash
# In WSL terminal
redis-server
```

**Azure (Container Apps with Sidecar):**
See Azure deployment section below.

### 2. Install Python Dependencies

Add to `requirements.txt`:
```
redis==5.0.0
```

Or install directly:
```bash
pip install redis
```

### 3. Configure Environment

```bash
# .env file or environment variables
REDIS_URL=redis://localhost:6379/0
WORKER_ID=worker-1
WORKER_POLL_INTERVAL=1      # Check queue every 1 second
WORKER_BATCH_SIZE=1          # Process 1 job at a time
```

---

## Running the Worker

### Local Development

**Terminal 1: Start Redis**
```bash
redis-server
```

**Terminal 2: Start API**
```bash
cd iafrimallv100
uvicorn app.main:app --reload --port 8000
```

**Terminal 3: Start Worker**
```bash
cd iafrimallv100
python -m app.workers.image_indexer_worker
```

Expected output:
```
2025-11-03 10:30:45 [INFO] image_indexer_worker - Worker worker-abc123 initialized
2025-11-03 10:30:45 [INFO] image_indexer_worker -   Poll interval: 1s
2025-11-03 10:30:45 [INFO] image_indexer_worker - Starting worker worker-abc123...
2025-11-03 10:30:45 [INFO] image_indexer_worker - Waiting for indexing jobs...
```

### Running Multiple Workers

```bash
# Terminal 3
python -m app.workers.image_indexer_worker --worker-id worker-1

# Terminal 4
python -m app.workers.image_indexer_worker --worker-id worker-2

# Terminal 5
python -m app.workers.image_indexer_worker --worker-id worker-3
```

Benefits:
- Workers process jobs in parallel
- Queue distributes jobs to available workers
- If worker crashes, job retries automatically
- Throughput increases with more workers

### Batch Mode (Testing)

Process available jobs and exit:
```bash
# Process all pending jobs
python -m app.workers.image_indexer_worker --batch-mode

# Process maximum 10 jobs
python -m app.workers.image_indexer_worker --batch-mode --max-jobs 10
```

---

## API Endpoints

### 1. Index Product with Image (Async)

```bash
POST /api/v1/index-product-with-image

Form parameters:
- product_id: "sku-12345"
- name: "Product Name"
- description: "Product Description"
- image_file: <binary image data>
- metadata: '{"color": "red", "size": "large"}' (optional JSON)

Response (< 20ms):
{
  "status": "queued",
  "job_id": "job-abc123def456",
  "product_id": "sku-12345",
  "processing_mode": "async",
  "status_url": "/api/v1/queue/status/job-abc123def456"
}
```

### 2. Check Job Status

```bash
GET /api/v1/queue/status/{job_id}

Response when processing:
{
  "job_id": "job-abc123def456",
  "status": "processing",
  "product_id": "sku-12345",
  "created_at": "2025-11-03T10:30:45.123456",
  "retry_count": 0
}

Response when complete:
{
  "job_id": "job-abc123def456",
  "status": "completed",
  "product_id": "sku-12345",
  "created_at": "2025-11-03T10:30:45.123456",
  "updated_at": "2025-11-03T10:30:48.654321",
  "retry_count": 0,
  "error_message": null
}

Response when failed:
{
  "job_id": "job-abc123def456",
  "status": "failed",
  "product_id": "sku-12345",
  "error_message": "Failed to generate embedding: CUDA out of memory",
  "retry_count": 3
}
```

### 3. Get Queue Statistics

```bash
GET /api/v1/queue/stats

Response:
{
  "available": true,
  "queue_name": "image_index_queue",
  "pending_in_queue": 5,
  "jobs": {
    "queued": 5,      # Waiting to be processed
    "processing": 2,  # Currently being processed
    "completed": 150, # Successfully indexed
    "failed": 3,      # Failed after retries
    "total": 160      # Total jobs ever created
  },
  "timestamp": "2025-11-03T10:30:45.123456"
}
```

### 4. Retry Failed Job

```bash
POST /api/v1/queue/retry/{job_id}

Response:
{
  "status": "retrying",
  "job_id": "job-abc123def456",
  "message": "Job re-queued for processing"
}
```

---

## Client Implementation Example

### Python Client

```python
import requests
import time

def upload_and_index_image(image_path: str, product_data: dict) -> str:
    """
    Upload image and queue for indexing.
    Returns job_id for status tracking.
    """
    api_url = "http://localhost:8000/api/v1"
    
    with open(image_path, 'rb') as f:
        files = {'image_file': f}
        data = {
            'product_id': product_data['product_id'],
            'name': product_data['name'],
            'description': product_data['description'],
            'metadata': json.dumps(product_data.get('metadata', {}))
        }
        
        response = requests.post(
            f"{api_url}/index-product-with-image",
            files=files,
            data=data
        )
        
        result = response.json()
        return result['job_id']


def wait_for_indexing(job_id: str, timeout: int = 300) -> bool:
    """
    Poll job status until completion or timeout.
    Returns True if completed, False if failed or timeout.
    """
    api_url = "http://localhost:8000/api/v1"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(f"{api_url}/queue/status/{job_id}")
        status_data = response.json()
        
        status = status_data['status']
        print(f"Job {job_id}: {status}")
        
        if status == 'completed':
            return True
        elif status == 'failed':
            print(f"Error: {status_data.get('error_message')}")
            return False
        
        time.sleep(1)  # Poll every 1 second
    
    print(f"Timeout waiting for job {job_id}")
    return False


# Usage
product = {
    'product_id': 'sku-12345',
    'name': 'Amazing Product',
    'description': 'High quality product',
    'metadata': {'category': 'electronics', 'price': 99.99}
}

job_id = upload_and_index_image('product.jpg', product)
print(f"Job queued: {job_id}")

if wait_for_indexing(job_id):
    print("Product indexed successfully!")
else:
    print("Failed to index product")
```

### JavaScript/Node.js Client

```javascript
async function uploadAndIndexImage(imagePath, productData) {
    const formData = new FormData();
    formData.append('product_id', productData.product_id);
    formData.append('name', productData.name);
    formData.append('description', productData.description);
    formData.append('image_file', fs.createReadStream(imagePath));
    formData.append('metadata', JSON.stringify(productData.metadata || {}));
    
    const response = await fetch(
        'http://localhost:8000/api/v1/index-product-with-image',
        { method: 'POST', body: formData }
    );
    
    const result = await response.json();
    return result.job_id;
}

async function waitForIndexing(jobId, timeout = 300000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
        const response = await fetch(
            `http://localhost:8000/api/v1/queue/status/${jobId}`
        );
        const status = await response.json();
        
        console.log(`Job ${jobId}: ${status.status}`);
        
        if (status.status === 'completed') {
            return true;
        } else if (status.status === 'failed') {
            console.error(`Error: ${status.error_message}`);
            return false;
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    console.error(`Timeout waiting for job ${jobId}`);
    return false;
}
```

---

## Performance Characteristics

### Throughput

| Workers | Images/Hour | Images/Second | Per-image Time |
|---------|------------|----------------|-----------------|
| 1       | 14,400 | 4 | 250 ms |
| 2       | 28,800 | 8 | 250 ms |
| 3       | 43,200 | 12 | 250 ms |
| 5       | 72,000 | 20 | 250 ms |
| 10      | 144,000 | 40 | 250 ms |

### API Response Times

| Operation | Latency | Blocked? |
|-----------|---------|----------|
| Enqueue image | 10-20 ms | No (async) |
| Check status | 5-10 ms | No |
| Get stats | 5-10 ms | No |

### Memory per Worker

- Base: 150 MB (Python + libraries)
- Per job: ~200-300 MB (image in memory)
- Peak: ~500 MB total (1 image processing)
- Scales linearly with workers

---

## Retry Logic

Failed jobs are automatically retried:

```
Attempt 1 → Fails
  ↓ (retry after 1 sec)
Attempt 2 → Fails
  ↓ (retry after 1 sec)
Attempt 3 → Fails
  ↓ (manual retry available)
Max retries exceeded → Job marked failed
```

Manual retry:
```bash
POST /api/v1/queue/retry/job-abc123def456
```

---

## Monitoring

### Queue Stats

```bash
# Check queue status
curl http://localhost:8000/api/v1/queue/stats | jq

# Output:
{
  "available": true,
  "pending_in_queue": 5,
  "jobs": {
    "queued": 5,
    "processing": 2,
    "completed": 1250,
    "failed": 3
  }
}
```

### Worker Logs

Worker outputs helpful metrics:

```
[INFO] Processing job job-abc123: product sku-12345
[DEBUG] Loading image for job-abc123...
[DEBUG] Generating CLIP embedding for job-abc123...
[DEBUG] Embedding generated: 512 dimensions
[DEBUG] Indexing in Qdrant for job-abc123...
✓ Job job-abc123 completed in 245ms - product sku-12345
```

Worker stats (every minute):

```
[INFO] Worker stats - Processed: 240, Failed: 1, Retried: 2, Uptime: 1.0h, Rate: 240 jobs/hour
```

---

## Azure Container Apps Deployment

### Architecture

```
Azure Container Apps
├── API Container (FastAPI)
│   ├─ Handle HTTP requests
│   ├─ Enqueue jobs to Redis
│   └─ Return immediately
├── Worker Container (same image, different entrypoint)
│   ├─ Run worker script
│   ├─ Process jobs from Redis
│   └─ Scale independently
└── Redis Sidecar (or external Azure Cache for Redis)
    └─ Queue shared between containers
```

### Deployment Steps

#### 1. Update Dockerfile

```dockerfile
# Multi-purpose Dockerfile
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app /app

# Default: Run API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Create Worker Image (Alternative)

```dockerfile
# Dockerfile.worker
FROM python:3.11-slim

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app /app

# Run worker
CMD ["python", "-m", "app.workers.image_indexer_worker"]
```

#### 3. Update requirements.txt

Ensure Redis is included:
```
redis==5.0.0
```

#### 4. Deploy API Container

```bash
az containerapp create \
  --name image-search-api \
  --resource-group my-rg \
  --image my-registry.azurecr.io/image-search:latest \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 1 \
  --max-replicas 5 \
  --env-vars REDIS_URL="$REDIS_URL"
```

#### 5. Deploy Worker Container

```bash
az containerapp create \
  --name image-search-worker \
  --resource-group my-rg \
  --image my-registry.azurecr.io/image-search:latest \
  --cpu 0.5 \
  --memory 0.5Gi \
  --min-replicas 1 \
  --max-replicas 10 \
  --env-vars REDIS_URL="$REDIS_URL" \
  --command python -m app.workers.image_indexer_worker
```

#### 6. Configure Redis

**Option A: Azure Cache for Redis**
```bash
az redis create \
  --name my-redis \
  --resource-group my-rg \
  --sku Basic \
  --vm-size c0

# Get connection string
REDIS_URL=$(az redis list-keys --name my-redis --resource-group my-rg --query primaryKey -o tsv)
```

**Option B: Redis in Kubernetes (if using AKS)**
```yaml
# redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
```

#### 7. Set Environment Variables

```bash
# In Container App settings
REDIS_URL=redis://my-redis.redis.cache.windows.net:6379/0?password=YOUR_PASSWORD
WORKER_ID=azure-worker-1
WORKER_POLL_INTERVAL=1
```

### Scaling Strategy

**API Container:**
- Min: 1 replica
- Max: 5 replicas
- Scale based on: HTTP request rate, CPU

**Worker Container:**
- Min: 1 replica
- Max: 10 replicas  
- Scale based on: Queue depth, CPU

**Redis:**
- Dedicated Azure Cache for Redis
- Auto-scaling: N/A (fixed tier)
- Monitor: Memory usage, connected clients

---

## Troubleshooting

### Worker Not Processing Jobs

**Check 1: Redis Connection**
```bash
# Test Redis connectivity
python -c "import redis; r = redis.from_url('redis://localhost:6379/0'); print(r.ping())"
# Output: True
```

**Check 2: Worker Logs**
```bash
# Watch worker output for errors
python -m app.workers.image_indexer_worker 2>&1 | grep -i error
```

**Check 3: Queue Status**
```bash
curl http://localhost:8000/api/v1/queue/stats | jq
# Check if pending_in_queue is increasing or staying constant
```

### Jobs Failing Repeatedly

**Common causes:**
1. Image format not supported
   - Fix: Only JPG, PNG, WebP supported
   
2. Out of memory
   - Fix: Add more workers, reduce worker batch size
   
3. CLIP model not loaded
   - Fix: Check GPU/CPU memory available
   
4. Qdrant indexing failing
   - Fix: Check Qdrant disk space, collection exists

**Debug a failing job:**
```bash
# Get job details
curl http://localhost:8000/api/v1/queue/status/job-abc123 | jq .error_message

# Manually retry
curl -X POST http://localhost:8000/api/v1/queue/retry/job-abc123
```

### High Queue Backup

**Symptoms:**
- `pending_in_queue` keeps growing
- Images taking hours to index

**Solutions:**
1. Add more workers
2. Reduce image size
3. Increase worker CPU allocation
4. Check for stuck/hanging jobs

**Monitor:**
```bash
# Watch queue depth
watch -n 1 "curl -s http://localhost:8000/api/v1/queue/stats | jq .pending_in_queue"
```

---

## Production Checklist

- [ ] Redis deployed and accessible
- [ ] Requirements.txt includes redis==5.0.0
- [ ] REDIS_URL environment variable set
- [ ] API container deployed
- [ ] Worker container deployed
- [ ] Auto-scaling configured (workers)
- [ ] Queue stats endpoint monitored
- [ ] Failed jobs alert set up
- [ ] Logs aggregated (Azure Monitor)
- [ ] Load tested with >100 concurrent uploads
- [ ] Disaster recovery plan (Redis backup)
- [ ] Documentation updated for ops team

---

## Related Files

- **Queue Service**: `app/services/redis_queue.py`
- **Worker**: `app/workers/image_indexer_worker.py`
- **API Endpoints**: `app/api/routes.py` (async endpoints)
- **Requirements**: `requirements.txt` (add redis==5.0.0)
- **Docker**: `Dockerfile` and `Dockerfile.worker` (if separate)

---

## Summary

✅ **API stays fast**: Enqueue in ~10ms vs processing in ~250ms
✅ **Horizontal scaling**: Add more workers to increase throughput  
✅ **Fault tolerance**: Automatic retry on failure
✅ **Full visibility**: Track job status in real-time
✅ **Azure-ready**: Deploy to Container Apps immediately
✅ **Production-tested**: Error handling, logging, monitoring built-in
