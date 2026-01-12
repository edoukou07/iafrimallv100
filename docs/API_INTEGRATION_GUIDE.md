# 🔍 Image Search API - Guide d'Intégration

**Version:** 3.0  
**URL API:** `http://20.238.104.13:8000`

---

## 📋 Résumé Rapide

L'**Image Search API** permet à votre e-commerce de:
- 🔎 Rechercher des produits par **texte** (requête sémantique)
- 📷 Rechercher par **image** (produits similaires visuellement)
- 🔄 **Indexer** de nouveaux produits avec embeddings
- 📊 **Monitorer** l'API et les tâches d'indexation
- 🚀 Générer des **embeddings CLIP** pour l'analyse

**Latence:** 150-300ms par requête | **Débit:** 10+ req/sec

---

## 🚀 Installation

### Option 1: Python/Requests (Recommandé)

```bash
pip install requests
```

**Exemple minimal:**

```python
import requests

API_URL = "http://20.238.104.13:8000"

# Recherche par texte
response = requests.post(
    f"{API_URL}/api/v1/search",
    json={"query": "blue shoes", "limit": 10},
    timeout=30
)
results = response.json()["results"]
```

### Option 2: JavaScript/Node.js

```bash
npm install axios
```

```javascript
const axios = require('axios');

const API_URL = "http://20.238.104.13:8000";

// Recherche par texte
const response = await axios.post(
  `${API_URL}/api/v1/search`,
  { query: "blue shoes", limit: 10 },
  { timeout: 30000 }
);
const results = response.data.results;
```

### Option 3: cURL

```bash
curl -X POST "http://20.238.104.13:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"blue shoes","limit":10}'
```

---

## 📚 Endpoints Disponibles

### 1️⃣ Recherche par Texte

```http
POST /api/v1/search
Content-Type: application/json

{
  "query": "red running shoes",
  "limit": 10
}
```

**Réponse:**
```json
{
  "query": "red running shoes",
  "count": 2,
  "results": [
    {
      "id": "123",
      "score": 0.89,
      "metadata": {
        "name": "Nike Red Running Shoes",
        "description": "High-performance red shoes",
        "image_url": "https://example.com/shoe1.jpg",
        "price": 129.99,
        "category": "footwear",
        "url": "https://example.com/products/shoe1"
      }
    }
  ]
}
```

**Paramètres:**

| Param | Type | Défaut | Description |
|-------|------|--------|-------------|
| `query` | string | ✅ Requis | Texte à rechercher |
| `limit` | int | 10 | Max résultats (1-100) |

**Python:**
```python
def search_products(query, limit=10):
    response = requests.post(
        f"{API_URL}/api/v1/search",
        json={"query": query, "limit": limit},
        timeout=30
    )
    return response.json()["results"]

shoes = search_products("red running shoes", limit=5)
for product in shoes:
    print(f"{product['metadata']['name']} - Score: {product['score']}")
```

---

### 2️⃣ Recherche par Image

```http
POST /api/v1/search-image
Content-Type: multipart/form-data

file: <image_file>
limit: 10
```

**Formats acceptés:** JPEG, PNG, GIF, WebP, BMP  
**Taille max:** 50MB

**Python:**
```python
def search_by_image(image_path, limit=10):
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {'limit': limit}
        response = requests.post(
            f"{API_URL}/api/v1/search-image",
            files=files,
            data=data,
            timeout=30
        )
    return response.json()["results"]

results = search_by_image("product.jpg", limit=10)
```

---

### 3️⃣ Générer un Embedding Texte

```http
POST /api/v1/embed
Content-Type: application/json

{
  "text": "red running shoes"
}
```

**Réponse:**
```json
{
  "embedding": [0.125, -0.234, 0.512, ...],
  "model": "clip-vit-base-patch32",
  "dimensions": 512
}
```

**Python:**
```python
def get_text_embedding(text):
    response = requests.post(
        f"{API_URL}/api/v1/embed",
        json={"text": text},
        timeout=30
    )
    return response.json()["embedding"]

embedding = get_text_embedding("blue shoes")
print(f"Embedding: {len(embedding)} dimensions")
```

---

### 4️⃣ Générer un Embedding Image

```http
POST /api/v1/embed-image
Content-Type: multipart/form-data

file: <image_file>
```

**Réponse:**
```json
{
  "embedding": [0.125, -0.234, 0.512, ...],
  "model": "clip-vit-base-patch32",
  "dimensions": 512
}
```

**Python:**
```python
def get_image_embedding(image_path):
    with open(image_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f"{API_URL}/api/v1/embed-image",
            files=files,
            timeout=30
        )
    return response.json()["embedding"]

embedding = get_image_embedding("shoe.jpg")
```

---

### 5️⃣ Indexer un Produit

```http
POST /api/v1/index-product
Content-Type: application/json

{
  "product_id": "123",
  "name": "Nike Red Running Shoes",
  "description": "High-performance red running shoes",
  "embedding": [0.1, 0.2, 0.3, ...],
  "metadata": {
    "price": 129.99,
    "category": "footwear",
    "url": "https://example.com/products/shoe1",
    "image_url": "https://example.com/shoe1.jpg"
  }
}
```

**Python:**
```python
def index_product(product_id, name, description, embedding, metadata=None):
    payload = {
        "product_id": product_id,
        "name": name,
        "description": description,
        "embedding": embedding,
        "metadata": metadata or {}
    }
    response = requests.post(
        f"{API_URL}/api/v1/index-product",
        json=payload,
        timeout=30
    )
    return response.json()["success"]
```

---

### 6️⃣ Indexer avec Image (Embedding Auto)

```http
POST /api/v1/index-product-with-image
Content-Type: multipart/form-data

product_id: "123"
name: "Nike Red Running Shoes"
description: "High-performance red running shoes"
file: <image_file>
price: "129.99"
category: "footwear"
url: "https://example.com/products/shoe1"
```

L'API calcule automatiquement l'embedding CLIP de l'image.

**Python:**
```python
def index_product_with_image(product_id, name, description, image_path, metadata):
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {
            'product_id': product_id,
            'name': name,
            'description': description,
            **metadata
        }
        response = requests.post(
            f"{API_URL}/api/v1/index-product-with-image",
            files=files,
            data=data,
            timeout=30
        )
    return response.json()["success"]
```

---

### 7️⃣ Vérifier le Statut d'une Tâche

```http
GET /api/v1/queue/status/{job_id}
```

**Réponse:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "product_id": "123",
  "product_name": "Nike Red Shoes",
  "progress": 100,
  "indexed_at": "2026-01-10T10:15:32Z",
  "error": null
}
```

**Statuts:** `pending`, `processing`, `completed`, `failed`

**Python:**
```python
def check_job_status(job_id):
    response = requests.get(
        f"{API_URL}/api/v1/queue/status/{job_id}",
        timeout=10
    )
    return response.json()

status = check_job_status("550e8400-e29b-41d4-a716-446655440000")
print(f"Statut: {status['status']}")
```

---

### 8️⃣ Récupérer les Statistiques de la Queue

```http
GET /api/v1/queue/stats
```

**Réponse:**
```json
{
  "total_jobs": 150,
  "pending": 5,
  "completed": 140,
  "failed": 5,
  "processing": 1,
  "avg_time_ms": 2345
}
```

**Python:**
```python
response = requests.get(f"{API_URL}/api/v1/queue/stats")
stats = response.json()
print(f"En attente: {stats['pending']}")
print(f"Complétées: {stats['completed']}")
```

---

### 9️⃣ Récupérer les Métriques de Performance

```http
GET /api/v1/performance/monitor
```

**Réponse:**
```json
{
  "avg_search_latency_ms": 245,
  "p95_latency_ms": 380,
  "p99_latency_ms": 520,
  "requests_per_sec": 8.5,
  "total_requests": 15432,
  "uptime_hours": 48.5,
  "cpu_usage_percent": 42,
  "memory_usage_mb": 1024
}
```

**Python:**
```python
def get_performance_metrics():
    response = requests.get(
        f"{API_URL}/api/v1/performance/monitor",
        timeout=10
    )
    return response.json()

metrics = get_performance_metrics()
print(f"Latence moyenne: {metrics['avg_search_latency_ms']}ms")
```

---

### 🔟 Supprimer un Produit de l'Index

```http
DELETE /api/v1/collections/products/points/{product_id}
```

**Réponse:**
```json
{
  "success": true,
  "product_id": "123",
  "message": "Product removed from index"
}
```

**Python:**
```python
def delete_product(product_id):
    response = requests.delete(
        f"{API_URL}/api/v1/collections/products/points/{product_id}",
        timeout=10
    )
    return response.json()["success"]

delete_product("123")
```

---

## 🔧 Gestion d'Erreurs

```python
def safe_search(query, limit=10):
    try:
        response = requests.post(
            f"{API_URL}/api/v1/search",
            json={"query": query, "limit": limit},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["results"]
    
    except requests.exceptions.Timeout:
        print("Erreur: Timeout (>30s)")
        return []
    except requests.exceptions.ConnectionError:
        print("Erreur: Impossible de se connecter")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"Erreur HTTP {e.response.status_code}")
        return []
```

**Codes d'erreur:**

| Code | Signification |
|------|---------------|
| 200 | ✅ Succès |
| 400 | ❌ Requête invalide |
| 404 | ❌ Endpoint non trouvé |
| 500 | ❌ Erreur serveur |
| 503 | ❌ Service indisponible |

---

## 🎯 Cas d'Usage Courants

### Barre de Recherche

```python
def product_search_bar(query):
    try:
        response = requests.post(
            f"{API_URL}/api/v1/search",
            json={"query": query, "limit": 20},
            timeout=10
        )
        return response.json()["results"] if response.status_code == 200 else []
    except:
        return []
```

### Recherche Inverse Image

```python
def reverse_image_search(image_bytes):
    try:
        files = {'file': ('image.jpg', image_bytes, 'image/jpeg')}
        response = requests.post(
            f"{API_URL}/api/v1/search-image",
            files=files,
            data={'limit': 10}
        )
        return response.json()["results"]
    except:
        return []
```

### Bulk Indexing

```python
def index_all_products(products_list):
    indexed = 0
    failed = 0
    
    for product in products_list:
        try:
            payload = {
                "product_id": product["id"],
                "name": product["name"],
                "description": product["description"],
                "embedding": product["embedding"],
                "metadata": {
                    "price": product["price"],
                    "category": product["category"],
                    "url": product["url"],
                    "image_url": product["image_url"]
                }
            }
            response = requests.post(
                f"{API_URL}/api/v1/index-product",
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                indexed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
    
    return {"indexed": indexed, "failed": failed}
```

---

## ⚙️ Configuration Recommandée

### Timeouts

```python
# Recherche simple: 10-15s
requests.post(..., timeout=15)

# Upload image: 30-60s
requests.post(..., timeout=60)
```

### Retry Logic

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

---

## 📞 Support

**Base URL:** `http://20.238.104.13:8000`  
**Documentation:** `http://20.238.104.13:8000/docs`  
**Health:** `http://20.238.104.13:8000/api/v1/health`

---

## 🔒 Notes Sécurité

- API sans authentification (réseau interne recommandé)
- HTTPS recommandé en production
- Validez tous les inputs
- Limite upload: 50MB max

---

**Version 3.0 - Janvier 2026**
