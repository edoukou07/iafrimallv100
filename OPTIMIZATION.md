# OPTIMIZATION.md - Bonnes Pratiques et Optimisations

## 🚀 Performance Tuning

### 1. Optimisation du Modèle CLIP

#### Mode Évaluation (eval mode)
```python
# Déjà inclus dans embedding_service.py
self.model.eval()  # Désactive dropout, batch norm
```

#### Quantization (réduction mémoire)
```python
# Pour déploiement edge ou faible mémoire
from torch.quantization import quantize_dynamic
quantized_model = quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
```

#### Utiliser GPU
```bash
# Si GPU disponible
docker run --gpus all -d image-search-api
```

### 2. Optimisation Qdrant

#### Indexation
```python
# Dans qdrant_service.py - utiliser batch upsert
self.client.upsert(
    collection_name=self.collection_name,
    points=points  # Batch de 1000+ points
)
```

#### Recherche
```python
# Utiliser les filtres Qdrant natifs pour pré-filtrage
from qdrant_client.http.models import FieldCondition, MatchValue

filters = Filter(
    must=[
        FieldCondition(
            key="category",
            match=MatchValue(value="clothing")
        )
    ]
)

results = self.client.search(
    query_filter=filters,
    limit=top_k
)
```

#### Réplication et HA
```yaml
# docker-compose.yml
qdrant:
  environment:
    - QDRANT_GRPC_INTERFACE=0.0.0.0
    - QDRANT_REST_API_KEY=your-key
    - QDRANT_READ_ONLY=false
```

### 3. Optimisation Redis/Cache

#### Stratégie de Cache
```python
# Dans cache_service.py - Stratégie LRU
redis_client = redis.Redis(
    host=host,
    port=port,
    decode_responses=True,
    max_connections=50,
    socket_keepalive=True
)
```

#### Monitoring Cache
```python
# Vérifier hit rate
info = redis_client.info('stats')
hit_rate = info['keyspace_hits'] / (info['keyspace_hits'] + info['keyspace_misses'])
print(f"Cache hit rate: {hit_rate:.2%}")
```

### 4. Optimisation API FastAPI

#### Pipelining
```python
# Accepter plusieurs requêtes batch
@app.post("/api/v1/search-batch")
async def search_batch(requests: List[SearchRequest]):
    # Traiter en parallèle
    tasks = [
        asyncio.create_task(
            process_search(req)
        ) for req in requests
    ]
    return await asyncio.gather(*tasks)
```

#### Connection Pooling
```python
# Dans dependencies.py
from httpx import AsyncClient

client = AsyncClient(limits=httpx.Limits(max_connections=100))
```

#### Compression
```python
# app/main.py
from fastapi.middleware.gzip import GZIPMiddleware
app.add_middleware(GZIPMiddleware, minimum_size=1000)
```

---

## 📊 Benchmarking

### Outils

```bash
# Apache Bench
ab -n 1000 -c 50 http://localhost:8000/api/v1/health

# wrk (concurrent requests)
wrk -t12 -c400 -d30s --script=script.lua http://localhost:8000/api/v1/health

# locust (load testing)
locust -f locustfile.py --host=http://localhost:8000
```

### Profiling

```python
# Ajouter profiling
from pyinstrument import Profiler

profiler = Profiler()
profiler.start()
# ... code ...
profiler.stop()
print(profiler.output_text())
```

### Résultats Attendus

| Opération | Sans Cache | Avec Cache | Avec GPU |
|-----------|-----------|-----------|---------|
| Recherche image | 250ms | 50ms | 150ms |
| Recherche texte | 150ms | 30ms | 80ms |
| Health check | 5ms | N/A | 5ms |

---

## 🔍 Monitoring et Observabilité

### Logs Structurés
```python
# app/utils/logger.py
import json
from pythonjsonlogger import jsonlogger

handler = logging.FileHandler('logs/app.json')
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### Métriques Prometheus
```python
# app/api/metrics.py
from prometheus_client import Counter, Histogram

search_count = Counter('search_total', 'Total searches')
search_duration = Histogram('search_duration_seconds', 'Search duration')

@app.post("/api/v1/search")
async def search(request):
    with search_duration.time():
        # ... search logic ...
        search_count.inc()
```

### APM (Application Performance Monitoring)
```python
# Intégration Datadog
from ddtrace import tracer

@tracer.wrap(span_name="search_operation")
def search(query):
    # ... logic ...
    pass
```

---

## 🛡️ Sécurité

### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/search")
@limiter.limit("100/minute")
async def search(request):
    pass
```

### Input Validation
```python
from pydantic import validator, HttpUrl

class SearchRequest(BaseModel):
    image_url: Optional[HttpUrl] = None  # Valide URLs
    text_query: Optional[str] = None
    top_k: int = Field(default=10, ge=1, le=100)
    
    @validator('text_query')
    def validate_text(cls, v):
        if v and len(v) > 500:
            raise ValueError('Text too long')
        return v
```

### CORS Configuration
```python
# À personnaliser pour production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

---

## 🎯 Scalabilité

### Horizontal Scaling (Kubernetes)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: image-search-api
spec:
  replicas: 3  # Augmenter pour plus de requêtes
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

### Load Balancing
```bash
# Nginx configuration
upstream backend {
    least_conn;
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}

server {
    listen 80;
    location /api/v1/ {
        proxy_pass http://backend;
    }
}
```

### Database Sharding (optionnel)
```python
# Si vous avez des millions de produits
# Partitionner Qdrant par catégorie ou région
collections = [
    "products_clothing",
    "products_electronics",
    "products_home"
]
```

---

## 🧪 Testing Performance

### Load Test Script
```python
# tests/load_test.py
import asyncio
import aiohttp

async def load_test():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(1000):
            task = session.post(
                'http://localhost:8000/api/v1/search',
                json={"text_query": "shirt", "top_k": 10}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        success = sum(1 for r in responses if r.status == 200)
        print(f"Success rate: {success/len(responses)*100:.1f}%")

asyncio.run(load_test())
```

### Stress Test
```bash
# 10,000 requêtes simultanées
siege -u search_urls.txt -c 100 -r 100
```

---

## 📈 Checklist d'Optimisation

- [ ] GPU activé si disponible
- [ ] Batch processing pour indexation (1000+ items)
- [ ] Cache Redis utilisé activement (>50% hit rate)
- [ ] Compression GZIP activée
- [ ] Rate limiting en place
- [ ] Monitoring/Logs actifs
- [ ] Load test passé (>500 req/s)
- [ ] Replicas Kubernetes >1
- [ ] Health checks configurés
- [ ] Timeouts appropriés
- [ ] Connection pooling activé
- [ ] Backups automatiques

---

## 🚨 Troubleshooting Perf

### Latence haute?
1. Vérifier les logs: `docker-compose logs -f`
2. Vérifier cache hit rate
3. Vérifier GPU utilization: `nvidia-smi`
4. Profiler avec pyinstrument

### Qdrant lent?
1. Vérifier la taille de la collection: `/api/v1/collections`
2. Considérer indexation (vecteurs quantifiés)
3. Augmenter replicas

### Memory leak?
1. Profiler: `memory_profiler`
2. Vérifier imports circulaires
3. Vérifier fermeture connexions

---

## 📚 Ressources

- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/concepts/)
- [Qdrant Optimization](https://qdrant.tech/documentation/tutorials/)
- [CLIP Quantization](https://pytorch.org/blog/quantization/)
- [Redis Best Practices](https://redis.com/blog/)
