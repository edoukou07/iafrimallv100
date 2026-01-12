# 🔍 Image Search API - Guide d'Intégration

**Version:** 3.0  
**URL API:** `http://20.238.104.13:8000`

---

## 📋 Résumé Rapide

L'**Image Search API** permet à votre e-commerce de:
- 🔎 Rechercher des produits par **texte** (requête sémantique)
- 📷 Rechercher par **image** (produits similaires visuellement)
- 🎤 Rechercher par **voix** (audio → texte → recherche)
- 🔄 **Indexer** de nouveaux produits avec embeddings
- 📊 Récupérer des **statistiques** et monitoring

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

## 📚 Endpoints Essentiels

### 1️⃣ Vérifier la Santé du Service

```http
GET /api/v1/health
```

**Réponse:**
```json
{
  "status": "healthy",
  "service": "Image Search API (Container Apps)",
  "version": "3.0",
  "qdrant": {
    "connected": true,
    "stats": {
      "name": "products",
      "points_count": 150,
      "vectors_count": 150
    }
  }
}
```

**Utilisation:**
```python
response = requests.get(f"{API_URL}/api/v1/health")
if response.json()["status"] == "healthy":
    print("API opérationnelle")
```

---

### 2️⃣ Recherche par Texte

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
    },
    {
      "id": "456",
      "score": 0.76,
      "metadata": {
        "name": "Adidas Red Sports Shoes",
        "description": "Comfortable red athletic shoes",
        "image_url": "https://example.com/shoe2.jpg",
        "price": 99.99,
        "category": "footwear",
        "url": "https://example.com/products/shoe2"
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
    data = response.json()
    return data["results"]

# Utilisation
shoes = search_products("red running shoes", limit=5)
for product in shoes:
    print(f"{product['metadata']['name']} - Score: {product['score']}")
```

---

### 3️⃣ Recherche par Image

```http
POST /api/v1/search-image
Content-Type: multipart/form-data

file: <image_file>
limit: 10
```

**Réponse:** Identique à la recherche texte

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

# Utilisation
results = search_by_image("product.jpg", limit=10)
```

**JavaScript:**
```javascript
async function searchByImage(imageFile, limit = 10) {
  const formData = new FormData();
  formData.append('file', imageFile);
  formData.append('limit', limit);

  const response = await axios.post(
    `${API_URL}/api/v1/search-image`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000
    }
  );
  return response.data.results;
}
```

---

### 4️⃣ Recherche Hybride (Texte + Mots-clés)

```http
POST /api/v1/search-hybrid
Content-Type: application/json

{
  "query": "red shoes",
  "limit": 10
}
```

Combine **recherche sémantique CLIP** + **BM25 keyword matching** pour meilleurs résultats.

**Python:**
```python
response = requests.post(
    f"{API_URL}/api/v1/search-hybrid",
    json={"query": "red shoes", "limit": 10}
)
results = response.json()["results"]
```

---

### 5️⃣ Recherche Vocale

```http
POST /api/v1/voice-search
Content-Type: multipart/form-data

file: <audio_file>
limit: 10
```

**Formats acceptés:** MP3, WAV, OGG, FLAC, M4A  
**Taille max:** 50MB

**Fonctionnement:**
1. Audio → Transcription (Whisper)
2. Texte transcrit → Recherche sémantique
3. Retour des résultats

**Python:**
```python
def search_by_voice(audio_path, limit=10):
    with open(audio_path, 'rb') as f:
        files = {'file': f}
        data = {'limit': limit}
        response = requests.post(
            f"{API_URL}/api/v1/voice-search",
            files=files,
            data=data,
            timeout=30
        )
    return response.json()["results"]
```

---

### 6️⃣ Indexer un Produit

```http
POST /api/v1/index-product
Content-Type: application/json

{
  "product_id": "123",
  "name": "Nike Red Running Shoes",
  "description": "High-performance red running shoes",
  "embedding": [0.1, 0.2, 0.3, ...],  // 512 dimensions
  "metadata": {
    "price": 129.99,
    "category": "footwear",
    "url": "https://example.com/products/shoe1",
    "image_url": "https://example.com/shoe1.jpg"
  }
}
```

**Retour:**
```json
{
  "success": true,
  "product_id": "123",
  "qdrant_id": 9876543210,
  "indexed": true
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

### 7️⃣ Indexer avec Image (Embedding Auto)

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

# Utilisation
success = index_product_with_image(
    product_id="123",
    name="Nike Red Shoes",
    description="High-performance red running shoes",
    image_path="shoe.jpg",
    metadata={
        "price": "129.99",
        "category": "footwear",
        "url": "https://example.com/products/shoe1"
    }
)
```

---

### 8️⃣ Récupérer les Statistiques

```http
GET /api/v1/stats
```

**Réponse:**
```json
{
  "name": "products",
  "points_count": 1250,
  "vectors_count": 1250,
  "segment_count": 5,
  "indexed_at": "2026-01-10T10:15:32Z"
}
```

**Python:**
```python
response = requests.get(f"{API_URL}/api/v1/stats")
stats = response.json()
print(f"Total produits indexés: {stats['points_count']}")
```

---

## 🔧 Gestion d'Erreurs

**Tous les appels doivent gérer les erreurs:**

```python
def safe_search(query, limit=10):
    try:
        response = requests.post(
            f"{API_URL}/api/v1/search",
            json={"query": query, "limit": limit},
            timeout=30
        )
        response.raise_for_status()  # Vérifie le statut HTTP
        return response.json()["results"]
    
    except requests.exceptions.Timeout:
        print("Erreur: Requête timeout (>30s)")
        return []
    except requests.exceptions.ConnectionError:
        print("Erreur: Impossible de se connecter à l'API")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"Erreur HTTP {e.response.status_code}: {e.response.text}")
        return []
    except ValueError:
        print("Erreur: Réponse JSON invalide")
        return []
```

**Codes d'erreur courants:**

| Code | Signification |
|------|---------------|
| 200 | ✅ Succès |
| 400 | ❌ Requête invalide (query vide, etc.) |
| 404 | ❌ Endpoint non trouvé |
| 500 | ❌ Erreur serveur |
| 503 | ❌ Service indisponible |

---

## 🎯 Cas d'Usage Courants

### Barre de Recherche E-commerce

```python
def product_search_bar(query):
    """Intégration simple pour barre de recherche"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/search",
            json={"query": query, "limit": 20},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()["results"]
    except:
        pass
    return []
```

### Recherche Inverse (Upload Image)

```python
def reverse_image_search(image_bytes):
    """Client télécharge une image, trouve produits similaires"""
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

### Bulk Indexing (Import Catalogue)

```python
def index_all_products(products_list):
    """Indexer plusieurs produits"""
    indexed = 0
    failed = 0
    
    for product in products_list:
        try:
            payload = {
                "product_id": product["id"],
                "name": product["name"],
                "description": product["description"],
                "embedding": product["embedding"],  # CLIP embedding 512-dim
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
                print(f"Erreur indexing {product['id']}")
        except Exception as e:
            failed += 1
            print(f"Exception: {e}")
    
    print(f"Indexé: {indexed}, Échoué: {failed}")
```

---

## ⚙️ Configuration Recommandée

### Timeouts

```python
# Recherche simple: 10-15s
requests.post(..., timeout=15)

# Upload image/audio: 30-60s
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

### Rate Limiting

- **Max:** 10 requêtes/seconde par IP
- **Dépassement:** Status 429 (Retry-After header)

---

## 📞 Support

**Base URL:** `http://20.238.104.13:8000`  
**Documentation Interactive:** `http://20.238.104.13:8000/docs`  
**Health Check:** `http://20.238.104.13:8000/api/v1/health`

---

## 🔒 Notes Sécurité

- ✅ API sans authentification (réseau interne recommandé)
- ✅ HTTPS recommandé en production
- ✅ Validez tous les inputs côté client
- ✅ Limitez la taille des uploads (50MB max)

---

## 📊 Monitoring

Vérifiez la santé de l'API avant chaque requête critique:

```python
def is_api_healthy():
    try:
        response = requests.get(
            f"{API_URL}/api/v1/health",
            timeout=5
        )
        return response.status_code == 200
    except:
        return False
```

---

**Version 3.0 - Janvier 2026**
