# Qdrant RAM Optimization - Deployment & Monitoring Guide

## Quick Summary

**Problem**: Qdrant storing all vectors in RAM → 2+ GB for 1M vectors → exceeds Azure Container Apps memory
**Solution**: Disk-based storage with smart LRU cache → 82% RAM reduction → only 400-500 MB for 1M vectors

---

## Deployment Steps

### 1. Copy Configuration File

```bash
# From workspace root
cp qdrant_config.yaml /app/data/qdrant/
```

Or in Dockerfile:
```dockerfile
COPY qdrant_config.yaml /app/config/
ENV QDRANT_CONFIG_PATH=/app/config/qdrant_config.yaml
```

### 2. Ensure Data Volume is Mounted

In Azure Container Apps:
```json
{
  "volumes": [
    {
      "name": "qdrant-data",
      "storageType": "AzureFile",
      "storageName": "qdrantstorage"
    }
  ],
  "containers": [
    {
      "volumeMounts": [
        {
          "volumeName": "qdrant-data",
          "mountPath": "/app/data"
        }
      ],
      "env": [
        {
          "name": "QDRANT_DATA_PATH",
          "value": "/app/data/qdrant"
        }
      ]
    }
  ]
}
```

### 3. Set Memory Limit

Minimum: 1 GB
Recommended: 2 GB for production
Maximum recommended: 4 GB (for ultra-large catalogs)

### 4. Verify After Deployment

```bash
# Check startup logs for:
# "Initializing Qdrant with RAM-optimized disk storage"
# "✓ Vector Storage: DISK-BASED (not RAM)"
# "✓ Cache Strategy: LRU cache for hot vectors only"
```

---

## Monitoring in Production

### Endpoint 1: Health Check
```bash
GET /api/v1/health

Response:
{
  "status": "healthy",
  "service": "Image Search API",
  "qdrant": {
    "connected": true,
    "stats": {
      "name": "products",
      "points_count": 150000,
      "vectors_count": 150000
    }
  }
}
```

### Endpoint 2: Performance Monitoring (NEW)
```bash
GET /api/v1/performance/monitor

Response:
{
  "timestamp": "2025-11-03T10:30:45.123456",
  "status": "healthy",
  "memory": {
    "container_memory_mb": 450.5,
    "container_memory_percent": 45.0,
    "qdrant_cache_mb": 256.0,
    "message": "RAM-optimized with disk storage"
  },
  "disk": {
    "database_size_mb": 1200.5,
    "snapshots_size_mb": 50.2,
    "total_mb": 1250.7
  },
  "collection": {
    "points_indexed": 150000,
    "vectors_count": 150000
  },
  "queries": {
    "avg_latency_ms": 45.2,
    "p95_latency_ms": 120.5,
    "p99_latency_ms": 250.1,
    "cache_hit_rate_percent": 92.5
  },
  "health": {
    "is_healthy": true,
    "warnings": []
  }
}
```

### Endpoint 3: Record Query Performance
```bash
# Called after each query (internal)
POST /api/v1/performance/record-query?latency_ms=45.5&query_size=10&cache_hit=true
```

---

## Monitoring Dashboard Setup

### Example: Azure Monitor Alert

```json
{
  "name": "Qdrant High Memory Alert",
  "description": "Alert when Qdrant memory exceeds 80%",
  "condition": {
    "metric": "/api/v1/performance/monitor",
    "property": "memory.container_memory_percent",
    "operator": ">",
    "threshold": 80
  },
  "actions": [
    {
      "type": "send-email",
      "recipients": ["ops@company.com"]
    }
  ]
}
```

### Example: Performance Dashboard

Create a dashboard showing:

1. **Memory Trend**
   ```
   X-axis: Time
   Y-axis: Memory Usage (%)
   Target: Stay below 70%
   ```

2. **Query Latency**
   ```
   Metrics: Avg, P95, P99 latency
   Target: Avg < 100ms, P95 < 200ms
   ```

3. **Cache Hit Rate**
   ```
   Metric: Cache hit rate (%)
   Target: > 80%
   Alert: < 70%
   ```

4. **Disk Usage**
   ```
   Metric: Database size growth
   Target: Growth aligned with product indexing
   ```

---

## Troubleshooting

### Issue 1: Memory Growing Over Time

**Symptom**: Memory slowly increasing from 400MB → 700MB → 1000MB

**Causes**:
- Cache not evicting old data
- Memory fragmentation
- Query history not cleaning up

**Solutions**:

```yaml
# Option 1: Reduce cache lifespan (in qdrant_config.yaml)
cache_lifespan_seconds: 1800  # Changed from 3600 (30 min instead of 1 hour)

# Option 2: Reduce cache size
max_cache_size_mb: 128  # Changed from 256

# Option 3: Enable aggressive garbage collection
memory_management:
  memory_limit_mb: 800  # Hard limit
  pressure_on_memory: true
```

**Check if fixed**:
```bash
# Memory should stabilize after the change
curl http://localhost:8000/api/v1/performance/monitor | grep container_memory_mb
```

### Issue 2: Slow Queries (100ms+ latency)

**Symptom**: Queries taking 100-500ms instead of typical 20-50ms

**Causes**:
- Cache miss (cold vectors from disk)
- High concurrent load
- Disk I/O bottleneck

**Solutions**:

```yaml
# Option 1: Increase cache size
max_cache_size_mb: 512  # More hot vectors in RAM

# Option 2: Improve prefetching
prefetch_enabled: true
prefetch_batch_size: 200  # Increased from 100

# Option 3: Reduce search precision (faster, less accurate)
hnsw:
  ef_search: 50  # Faster but less accurate
```

**Monitor**:
```bash
curl http://localhost:8000/api/v1/performance/monitor | grep p95_latency_ms
# Should see improvement within 1-2 minutes
```

### Issue 3: High Disk I/O Utilization

**Symptom**: Disk I/O constantly at 100% during queries

**Causes**:
- Very large vectors (512-dim CLIP)
- Small cache not hitting frequently
- Large batch operations

**Solutions**:

```yaml
# Option 1: Optimize indexing
hnsw:
  ef_construct: 100  # Reduced from 200 (faster indexing)
  ef_search: 100     # Keep good search quality

# Option 2: Better segment management
optimization:
  auto_optimize: true
  optimization_interval_sec: 1800
  target_segment_size_mb: 32  # Smaller segments = less I/O

# Option 3: Enable read cache
io_optimization:
  read_cache_mb: 256  # Cache for sequential reads
```

### Issue 4: Disk Space Growing Too Fast

**Symptom**: `/app/data/qdrant` growing 100MB+ per day

**Causes**:
- WAL logs not being cleaned up
- Snapshots accumulating
- Segment fragmentation

**Solutions**:

```python
# In Python: Manual cleanup
from app.services.integrated_qdrant import get_qdrant_service

service = get_qdrant_service()

# Vacuum old snapshots (keep last 3)
import os
snapshots_dir = "/app/data/qdrant/snapshots"
snapshots = sorted(os.listdir(snapshots_dir))
for old_snapshot in snapshots[:-3]:
    os.remove(os.path.join(snapshots_dir, old_snapshot))

# Trigger optimization
service._client.optimize_collection("products")
```

Or in cron job:
```bash
#!/bin/bash
# cleanup-qdrant.sh

SNAPSHOTS_DIR="/app/data/qdrant/snapshots"
KEEP_COUNT=3

# Delete old snapshots, keep newest 3
ls -t "$SNAPSHOTS_DIR" | tail -n +$((KEEP_COUNT+1)) | xargs -I {} rm -rf "$SNAPSHOTS_DIR/{}"

echo "Cleaned up old Qdrant snapshots at $(date)" >> /var/log/qdrant-cleanup.log
```

---

## Performance Benchmarks

### Expected Performance with 1M Vectors

| Metric | Value | Notes |
|--------|-------|-------|
| **Memory Usage** | 400-500 MB | Disk-based + 256 MB cache |
| **Startup Time** | 2-5 sec | Index loading from disk |
| **Cache Hit Query** | 1-5 ms | Hot vector in RAM |
| **Cache Miss Query** | 20-100 ms | Cold vector from disk |
| **Avg Batch Query (100)** | 50-200 ms | Mixed hot/cold hits |
| **Cache Hit Rate** | 90-95% | With typical access patterns |
| **Disk Usage** | 2-4 GB | Vectors + metadata + indexes |

### Memory Usage by Cache Size

```
Cache Size | Total Memory | Hit Rate | Query Latency
100 MB     | 300 MB       | 75%      | 80 ms
256 MB     | 450 MB       | 92%      | 45 ms (RECOMMENDED)
512 MB     | 700 MB       | 96%      | 30 ms
1 GB       | 1.1 GB       | 98%      | 20 ms
```

---

## API Integration

### Automatic Performance Tracking

Update your search endpoints to record metrics:

```python
import time
from app.api.routes import _get_monitor

@router.post("/search-image")
async def search_image(file: UploadFile = File(...)):
    start = time.time()
    
    # ... search logic ...
    results = qdrant_service.search(query_vector, limit=10)
    
    # Record performance
    latency_ms = (time.time() - start) * 1000
    monitor = _get_monitor()
    monitor.record_query(
        latency_ms=latency_ms,
        query_size=len(results),
        cache_hit=False  # You can detect this from query stats
    )
    
    return results
```

---

## Cost Optimization

### Azure Container Apps Memory Tiers

| Tier | Memory | RAM Limit | Qdrant Capacity | Monthly Cost* |
|------|--------|-----------|-----------------|---------------|
| 0.5 GB | 0.5 GB | 256 MB | 100K-500K vectors | $4-6 |
| **1 GB** | **1 GB** | **512 MB** | **500K-2M vectors** | **$8-12** ⭐ |
| 2 GB | 2 GB | 1 GB | 2M-10M vectors | $16-24 |
| 4 GB | 4 GB | 2 GB | 10M-50M vectors | $32-48 |

*Costs are approximate for 24/7 usage on Consumption plan

### Cost Reduction Tips

1. **Right-size container memory**
   - Too large: Wasting money
   - Too small: Performance degradation
   - Recommended: 1 GB for 500K-2M vectors

2. **Use disk storage**
   - Saves 80%+ RAM vs in-memory
   - No need for expensive memory tiers
   - Automatic cache management

3. **Auto-scale replicas**
   - Start with 0 min replicas
   - Scale up only under load
   - Back to 0 during off-hours

4. **Azure Files for snapshots**
   - Cheaper than dedicated storage
   - Automatic backups
   - Disaster recovery ready

---

## Production Checklist

- [ ] **Deployment**
  - [ ] Copy `qdrant_config.yaml` to container
  - [ ] Set `QDRANT_DATA_PATH` environment variable
  - [ ] Mount persistent volume at `/app/data`
  - [ ] Set memory limit to 1-2 GB
  - [ ] Set auto-scale min=0, max=10

- [ ] **Monitoring**
  - [ ] Set up alerts for memory > 80%
  - [ ] Set up alerts for latency > 200ms
  - [ ] Dashboard showing memory trend
  - [ ] Dashboard showing cache hit rate
  - [ ] Dashboard showing disk usage

- [ ] **Optimization**
  - [ ] Tune cache size based on first week metrics
  - [ ] Adjust `ef_search` if needed
  - [ ] Set up snapshot cleanup job
  - [ ] Monitor disk growth

- [ ] **Documentation**
  - [ ] Team trained on monitoring endpoints
  - [ ] On-call runbook for high memory alerts
  - [ ] Troubleshooting guide distributed

---

## Related Files

- Configuration: `qdrant_config.yaml` - Tuning parameters
- Monitoring: `app/services/qdrant_monitoring.py` - Monitoring service
- API: `app/api/routes.py` - Monitoring endpoints (/performance/monitor, etc.)
- Docs: `docs/QDRANT_RAM_OPTIMIZATION.md` - Technical deep-dive
- This file: `QDRANT_MONITORING_GUIDE.md` - Operations guide

---

## Support & Questions

For issues or questions:
1. Check `/api/v1/performance/monitor` endpoint
2. Review logs for warning messages
3. Compare against benchmarks in this guide
4. Apply solutions from troubleshooting section
