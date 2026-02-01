# 🔌 Routes FastAPI Utilisées par Django

**Version:** 1.0  
**Date:** Novembre 2025  
**Contexte:** Appels depuis `iafrimall-django` vers FastAPI (`iafrimallv100`)

---

## 📋 Vue d'ensemble

Django agit comme **proxy client** qui appelle les endpoints FastAPI suivants:

```
Django (iafrimall-django)
    ↓
requests.post/get()
    ↓
FastAPI Backend (20.238.104.13:8000)
    ↓
/api/v1/*
```

Ce document liste **UNIQUEMENT les routes FastAPI** réellement appelées par Django.

**Base URL:** `http://20.238.104.13:8000/api/v1`

---

## 🛣️ Routes FastAPI Utilisées

### 1. Recherche Textuelle

#### `POST /api/v1/search`

**Appelée par:** `search/services.py` → `search_text()`  
**Utilisée dans:** 
- `/api/search/text/` (Django API)
- `/search/text/` (Interface Django)
- `similarity_views.py`

**Paramètres (JSON):**
```json
{
    "query": "blue shoes",
    "limit": 10
}
```

**Réponse (200):**
```json
{
    "query": "blue shoes",
    "results": [
        {
            "id": 1,
            "name": "Nike Blue Running Shoes",
            "description": "...",
            "image_url": "https://...",
            "price": 129.99,
            "category": "footwear",
            "score": 0.87
        }
    ],
    "count": 1
}
```

**Code Django (services.py):**
```python
def search_text(self, query: str, top_k: int = 10):
    success, data, error = self._make_request(
        'POST',
        'api/v1/search',
        json={'query': query, 'limit': top_k}
    )
    if success:
        results = data.get('results', [])
        return True, results, None
    return False, [], error
```

---

### 2. Recherche Visuelle

#### `POST /api/v1/search-image`

**Appelée par:** `search/services.py` → `search_image()`  
**Utilisée dans:**
- `/api/search/image/` (Django API)
- `/search/image/` (Interface Django)

**Paramètres (JSON) - Via URL:**
```json
{
    "image_url": "https://example.com/shoe.jpg",
    "limit": 10
}
```

**Paramètres (Multipart) - Via Fichier:**
```
file: <binary image data>
limit: 10
```

**Réponse (200):**
```json
{
    "query_image": "shoe.jpg",
    "results": [
        {
            "id": 5,
            "name": "Similar Blue Shoe",
            "description": "...",
            "image_url": "https://...",
            "score": 0.92
        }
    ],
    "count": 1
}
```

**Code Django (services.py):**
```python
def search_image(self, image_url: str = None, image_data: bytes = None, top_k: int = 10):
    if image_url:
        success, data, error = self._make_request(
            'POST',
            'api/v1/search-image',
            json={'image_url': image_url, 'limit': top_k}
        )
    elif image_data:
        files = {'file': ('image.jpg', image_data, 'image/jpeg')}
        success, data, error = self._make_request(
            'POST',
            'api/v1/search-image',
            files=files,
            data={'limit': top_k}
        )
```

---

### 3. Recherche Vocale

#### `POST /api/v1/voice-search`

**Appelée par:** `search/views.py` → `api_voice_search()`  
**Utilisée dans:** `/api/search/voice/` (Django API)

**Paramètres (Multipart):**
```
audio_file: <binary audio data> (WAV, MP3, M4A, FLAC, OGG)
language: en (optionnel)
limit: 10 (optionnel)
```

**Réponse (200):**
```json
{
    "transcription": "I need blue running shoes",
    "language": "en",
    "confidence": 0.97,
    "results": [
        {
            "id": 1,
            "name": "Nike Blue Running Shoes",
            "description": "...",
            "image_url": "https://...",
            "score": 0.88
        }
    ],
    "count": 1,
    "search_type": "voice"
}
```

**Code Django (views.py):**
```python
def api_voice_search(request):
    audio_file = request.FILES['audio_file']
    backend_url = api_client.base_url.rstrip('/') + '/api/v1/voice-search'
    
    files = {'audio_file': (audio_file.name, file_content, audio_file.content_type)}
    params = {
        'limit': limit,
        'language': language
    }
    
    response = requests.post(
        backend_url,
        files=files,
        params=params,
        timeout=60
    )
```

---

### 4. Indexation Produit (Synchrone)

#### `POST /api/v1/index-product`

**Appelée par:** 
- `search/services.py` → `index_product()`
- `search/views.py` → `ProductCreateView.form_valid()`
- `search/views.py` → `api_reindex_product()`

**Utilisée dans:**
- `/products/add/` (Créer produit)
- `/api/index/<id>/` (Réindexer)

**Paramètres (Form Data):**
```
product_id: "uuid-string"
name: "Blue Shoes"
description: "Comfortable blue shoes"
metadata: "{}"
```

**Réponse (200):**
```json
{
    "status": "indexed",
    "product_id": "123",
    "qdrant_id": 9223372036854775807,
    "embedding_dimension": 512
}
```

**Code Django (services.py):**
```python
def index_product(self, name: str, description: str, image_url: str):
    data = {
        'product_id': str(uuid.uuid4()),
        'name': name,
        'description': description,
        'metadata': '{}'
    }
    
    url = f"{self.base_url}/api/v1/index-product"
    response = self.session.post(url, data=data, timeout=self.timeout)
```

---

### 5. Indexation Produit avec Image (Asynchrone)

#### `POST /api/v1/index-product-with-image`

**Appelée par:** `search/services.py` → `index_product_with_image()`  
**Utilisée dans:** `/api/index/` (Django API)

**Paramètres (Multipart):**
```
file: <binary image data> (JPEG, PNG)
name: "Blue Shoes"
description: "Comfortable blue shoes"
```

**Réponse (202 - Queued):**
```json
{
    "status": "queued",
    "job_id": "job_abc123def456",
    "product_id": "123",
    "message": "Product queued for indexing",
    "status_url": "/api/v1/queue/status/job_abc123def456"
}
```

**Code Django (services.py):**
```python
def index_product_with_image(self, name: str, description: str, image_data: bytes):
    files = {'file': ('image.jpg', image_data, 'image/jpeg')}
    data_dict = {'name': name, 'description': description}
    
    success, data, error = self._make_request(
        'POST',
        'api/v1/index-product-with-image',
        files=files,
        data=data_dict
    )
```

---

### 6. Infos Modèle Whisper

#### `GET /api/v1/voice/model-info`

**Appelée par:** `search/views.py` → `voice_search_page()`  
**Utilisée dans:** `/voice/` (Interface Django)

**Paramètres:** Aucun

**Réponse (200):**
```json
{
    "model": "openai/whisper-base",
    "size": "140MB",
    "languages_supported": 99,
    "average_transcription_time_ms": 350,
    "accuracy": "~94% (benchmarked on English)"
}
```

**Code Django (views.py):**
```python
def voice_search_page(request):
    backend_url = api_client.base_url.rstrip('/') + '/api/v1/voice/model-info'
    response = requests.get(backend_url, timeout=5)
    if response.status_code == 200:
        model_info = response.json()
```

---

### 7. Statut Job Asynchrone

#### `GET /api/v1/queue/status/{job_id}`

**Appelée par:** `search/services.py` → `get_job_status()`  
**Utilisée dans:** `/api/job-status/<job_id>/` (Django API)

**Paramètres URL:**
```
job_id: "job_abc123def456"
```

**Réponse (200):**
```json
{
    "job_id": "job_abc123def456",
    "status": "completed",
    "progress": 100,
    "product_id": "123",
    "embedding_type": "image",
    "vector_size": 512,
    "execution_time_ms": 450,
    "completed_at": "2025-11-05T10:30:00.450Z"
}
```

**Code Django (services.py):**
```python
def get_job_status(self, job_id: str):
    success, data, error = self._make_request(
        'GET',
        f'api/v1/queue/status/{job_id}'
    )
```

---

### 8. Statistiques Queue

#### `GET /api/v1/queue/stats`

**Appelée par:** `search/services.py` → `get_queue_stats()`  
**Statut:** Disponible mais **pas activement utilisée**

**Paramètres:** Aucun

**Réponse (200):**
```json
{
    "queue_length": 5,
    "processing": 2,
    "completed": 150,
    "failed": 3
}
```

---

### 9. Données Performance

#### `GET /api/v1/performance/monitor`

**Appelée par:** `search/services.py` → `get_performance_data()`  
**Statut:** Disponible mais **pas activement utilisée**

**Paramètres:** Aucun

**Réponse (200):**
```json
{
    "avg_query_latency_ms": 125,
    "total_queries": 5420,
    "cache_hit_rate": 0.35
}
```

---

### 10. Texte en Embedding

#### `POST /api/v1/embed`

**Appelée par:** `search/services.py` → `embed_text()`  
**Statut:** Disponible mais **pas activement utilisée dans Django**

**Paramètres (JSON):**
```json
{
    "text": "Red cotton shirt"
}
```

**Réponse (200):**
```json
{
    "text": "Red cotton shirt",
    "embedding": [0.1234, 0.5678, -0.2345, ...],
    "dimension": 512
}
```

---

### 11. Image en Embedding

#### `POST /api/v1/embed-image`

**Appelée par:** `search/services.py` → `embed_image()`  
**Statut:** Disponible mais **pas activement utilisée dans Django**

**Paramètres (Multipart ou JSON):**

**Fichier:**
```
file: <binary image data>
```

**URL:**
```json
{
    "image_url": "https://example.com/shirt.jpg"
}
```

**Réponse (200):**
```json
{
    "image": "shirt.jpg",
    "embedding": [0.2456, -0.1234, 0.3456, ...],
    "dimension": 512
}
```

---

### 12. Supprimer Produit (Qdrant)

#### `DELETE /api/v1/collections/products/points/{product_id}`

**Appelée par:** `search/services.py` → `delete_product()`  
**Utilisée dans:** `/api/admin/delete-all/` (Admin)

**Paramètres URL:**
```
product_id: "9223372036854775807" (Qdrant Vector ID)
```

**Réponse (200):**
```json
{
    "status": "deleted"
}
```

**Code Django (services.py):**
```python
def delete_product(self, product_id: str) -> bool:
    url = f"{self.base_url}/api/v1/collections/products/points/{product_id}"
    response = self.session.delete(url, timeout=self.timeout)
```

---

## 📊 Résumé des Routes

| # | Route | Méthode | Utilisée? | Lieu d'Appel |
|---|-------|---------|-----------|-------------|
| 1 | `/api/v1/search` | POST | ✅ Active | Text Search |
| 2 | `/api/v1/search-image` | POST | ✅ Active | Image Search |
| 3 | `/api/v1/voice-search` | POST | ✅ Active | Voice Search |
| 4 | `/api/v1/index-product` | POST | ✅ Active | Product Creation |
| 5 | `/api/v1/index-product-with-image` | POST | ✅ Active | Async Indexing |
| 6 | `/api/v1/voice/model-info` | GET | ✅ Active | Voice UI |
| 7 | `/api/v1/queue/status/{id}` | GET | ✅ Active | Job Polling |
| 8 | `/api/v1/queue/stats` | GET | ❌ Inactive | Not used |
| 9 | `/api/v1/performance/monitor` | GET | ❌ Inactive | Not used |
| 10 | `/api/v1/embed` | POST | ❌ Inactive | Not used |
| 11 | `/api/v1/embed-image` | POST | ❌ Inactive | Not used |
| 12 | `/api/v1/collections/products/points/{id}` | DELETE | ✅ Active | Delete Admin |

---

## 🔄 Flux d'Appels Django → FastAPI

### Flux 1: Recherche Textuelle
```
User Browser
    ↓
GET /search/text/ (Django Template)
    ↓
POST /api/search/text/ (Django API)
    ↓
similarity_views.py
    ↓
POST /api/v1/search (FastAPI)
    ↓
CLIP Embeddings + Qdrant Search
    ↓
Résultats JSON
```

### Flux 2: Recherche Vocale
```
User Browser (Web Audio API)
    ↓
POST /api/search/voice/ (Django FormData)
    ↓
views.api_voice_search()
    ↓
POST /api/v1/voice-search (FastAPI Multipart)
    ↓
Whisper Transcription + CLIP Search
    ↓
Django enrichit avec Product.image_url
    ↓
Résultats JSON enrichis
```

### Flux 3: Créer Produit
```
User Browser
    ↓
POST /products/add/ (Django Form)
    ↓
ProductCreateView.form_valid()
    ↓
POST /api/v1/index-product (FastAPI Sync)
    ↓
CLIP Embedding + Qdrant Index
    ↓
Django met à jour Product.embedding_status = 'completed'
```

### Flux 4: Indexation Asynchrone
```
Django API
    ↓
POST /api/index/ (Django FormData)
    ↓
api_index_product()
    ↓
POST /api/v1/index-product-with-image (FastAPI)
    ↓
Enqueue dans Redis Queue
    ↓
Django crée Job + Product
    ↓
202 Queued Response
    ↓
Django polls GET /api/v1/queue/status/{job_id}
    ↓
Jusqu'à status = 'completed'
```

---

## 🔧 Configuration Django

**Fichier:** `iafrimall-django/config/settings.py`

```python
# API Configuration
IMAGE_SEARCH_API_URL = "http://20.238.104.13:8000"  # ou localhost:8000 en dev
IMAGE_SEARCH_API_TIMEOUT = 60  # secondes
```

**Client Singleton:**

```python
# search/services.py
def get_api_client() -> APIClient:
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client
```

---

## 📝 Exemples d'Utilisation

### Python (Django)

```python
from search.services import get_api_client

api_client = get_api_client()

# Recherche texte
success, results, error = api_client.search_text("blue shoes", top_k=10)

# Recherche image
success, results, error = api_client.search_image(image_url="https://...", top_k=10)

# Indexer produit
success, data, error = api_client.index_product("Shoes", "Description", "https://...")

# Statut job
success, status, error = api_client.get_job_status("job_abc123")

# Supprimer produit
api_client.delete_product("9223372036854775807")
```

### cURL

```bash
# Recherche texte
curl -X POST "http://20.238.104.13:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"blue shoes","limit":10}'

# Recherche vocale
curl -X POST "http://20.238.104.13:8000/api/v1/voice-search" \
  -F "audio_file=@query.wav" \
  -F "language=en"

# Statut job
curl "http://20.238.104.13:8000/api/v1/queue/status/job_abc123"

# Infos Whisper
curl "http://20.238.104.13:8000/api/v1/voice/model-info"
```

---

## ⚠️ Erreurs Courantes

| Erreur | Cause | Solution |
|--------|-------|----------|
| Connection refused | FastAPI offline | Vérifier `http://20.238.104.13:8000` |
| 404 Not Found | Endpoint inexistant | Vérifier chemin `/api/v1/` |
| 400 Bad Request | Paramètres invalides | Valider JSON/FormData |
| 503 Service Unavailable | FastAPI surchargée | Réessayer avec backoff |
| Timeout | Requête trop lente | Augmenter timeout (par défaut 60s) |

---

## 📞 Support

**Documentation complète FastAPI:** 
- `iafrimallv100/docs/API_DOCUMENTATION.md`

**Routes configurées dans:**
- `iafrimallv100/app/api/routes.py`

**Client Django:**
- `iafrimall-django/search/services.py`

---

**Document Version:** 1.0  
**Dernière mise à jour:** Novembre 2025  
**Statut:** ✅ Production
