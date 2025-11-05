# 🔍 Image Search API - Documentation Complète

**Version:** 3.0  
**Dernière mise à jour:** November 5, 2025  
**Auteur:** IAFRIMALL Dev Team

---

## 📑 Table des Matières

1. [Présentation Générale](#présentation-générale)
2. [Architecture](#architecture)
3. [Routes API](#routes-api)
4. [Authentification](#authentification)
5. [Gestion d'Erreurs](#gestion-derreurs)
6. [Exemples d'Utilisation](#exemples-dutilisation)

---

## 🎯 Présentation Générale

### Vue d'ensemble

L'**Image Search API** est une API RESTful alimentée par:
- **CLIP (OpenAI)**: Modèle de vision multimodal pour embeddings 512-dimensionnels
- **Qdrant**: Base de données vectorielle ultra-rapide pour recherche sémantique
- **BM25**: Recherche par mots-clés pour hybrid search
- **FastAPI**: Framework web haute-performance

### Fonctionnalités Principales

✅ **Recherche par Image** - Trouvez des produits similaires visuellement  
✅ **Recherche par Texte** - Recherche sémantique avec preprocessing avancé  
✅ **Recherche Vocale** - Transcrire audio en texte puis chercher (Whisper)  
✅ **Hybrid Search** - Combine CLIP sémantique + BM25 keyword matching  
✅ **Filtrage Avancé** - Par catégorie, score minimum, et plus  
✅ **Cache Redis** - Résultats de recherche en cache  
✅ **Monitoring** - Statistiques de collection et santé Qdrant  

### Performance

| Métrique | Valeur |
|----------|--------|
| **Latence Moyenne** | 150-300ms |
| **Throughput** | 10+ req/sec |
| **Dimension Embeddings** | 512 (CLIP-ViT) |
| **Distance** | Cosine Similarity |
| **Modèle CLIP** | openai/clip-vit-base-patch32 |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Client Application              │
│    (e-commerce, Django Frontend)        │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         FastAPI Server (Port 8000)      │
│  ├─ /api/v1/search (Text Search)        │
│  ├─ /api/v1/search-image (Image)        │
│  ├─ /api/v1/search-hybrid (Hybrid)      │
│  ├─ /api/v1/voice-search (Voice)        │
│  └─ /api/v1/health (Monitoring)         │
└────┬──────────────┬──────────────┬──────┘
     │              │              │
     ▼              ▼              ▼
 ┌────────┐  ┌──────────┐  ┌──────────┐
 │ CLIP   │  │ Qdrant   │  │ BM25     │
 │Service │  │Vector DB │  │Indexer   │
 │        │  │          │  │          │
 │512-dim │  │Cosine    │  │Keyword   │
 │        │  │Similarity│  │Search    │
 └────────┘  └──────────┘  └──────────┘
     │              │
     └──────┬───────┘
            ▼
    ┌──────────────────┐
    │  Redis Cache     │
    │  (Résultats)     │
    └──────────────────┘
```

---

## 🛣️ Routes API

### 1. Santé du Service

#### `GET /api/v1/health`

**Description:** Vérifier l'état de tous les services (API, Qdrant, Cache)

**Réponse - Succès (200):**
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
      "vectors_count": 150,
      "segment_count": 1
    }
  }
}
```

**Réponse - Erreur (503):**
```json
{
  "status": "unhealthy",
  "error": "Failed to connect to Qdrant"
}
```

---

### 2. Recherche par Texte

#### `POST /api/v1/search`

**Description:** Recherche sémantique par texte avec preprocessing avancé

**Paramètres de Requête:**

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `query` | string | ✅ Requis | Texte à chercher |
| `limit` | integer | 10 | Nombre max de résultats |

**Corps de la Requête:**
```json
{
  "query": "blue shoes",
  "limit": 10
}
```

**Réponse - Succès (200):**
```json
{
  "query": "blue shoes",
  "results": [
    {
      "id": 1,
      "score": 0.87,
      "metadata": {
        "name": "Nike Blue Running Shoes",
        "description": "High-performance running shoes with blue design",
        "image_url": "https://example.com/shoe1.jpg",
        "price": 129.99,
        "category": "footwear",
        "url": "https://example.com/products/shoe1"
      }
    }
  ],
  "count": 1
}
```

**Réponse - Erreur (400):**
```json
{
  "detail": "Query cannot be empty"
}
```

**Features:**
- ✅ Preprocessing automatique (nettoyage, normalization)
- ✅ Score threshold intelligent: 0.3
- ✅ Query expansion avec synonymes
- ✅ Support du multilangue (Whisper)

---

### 3. Recherche par Image

#### `POST /api/v1/search-image`

**Description:** Recherche de produits similaires en uploadant une image

**Paramètres de Requête:**

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `file` | file | ✅ Requis | Fichier image (JPEG, PNG, etc.) |
| `limit` | integer | 10 | Nombre max de résultats |

**Format Fichier Accepté:**
- JPEG, PNG, GIF, WebP, BMP
- Taille max: 50MB
- Résolution recommandée: 224x224 (minimum)

**Réponse - Succès (200):**
```json
{
  "query_image": "product.jpg",
  "results": [
    {
      "id": 5,
      "score": 0.92,
      "metadata": {
        "name": "Similar Blue Shoe",
        "description": "Product visually similar to query",
        "image_url": "https://example.com/shoe2.jpg",
        "price": 119.99,
        "category": "footwear"
      }
    }
  ],
  "count": 1,
  "model": "CLIP",
  "embedding_dimension": 512
}
```

**Réponse - Erreur (400):**
```json
{
  "detail": "File must be an image"
}
```

**Features:**
- ✅ Score threshold: 0.2 (plus bas pour images)
- ✅ Support multiformat
- ✅ Traitement rapide avec CLIP-ViT

---

### 4. Recherche Hybride (CLIP + BM25)

#### `POST /api/v1/search-hybrid`

**Description:** Combine recherche sémantique (CLIP) + keyword (BM25)

**Paramètres de Requête:**

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `query` | string | ✅ Requis | Texte à chercher |
| `limit` | integer | 10 | Nombre max de résultats |
| `semantic_weight` | float | 0.7 | Poids CLIP (0-1) |
| `keyword_weight` | float | 0.3 | Poids BM25 (0-1) |

**Corps de la Requête:**
```json
{
  "query": "cheap electronics",
  "limit": 10
}
```

**Paramètres Query String:**
```
POST /api/v1/search-hybrid?semantic_weight=0.6&keyword_weight=0.4
```

**Réponse - Succès (200):**
```json
{
  "query": "cheap electronics",
  "results": [
    {
      "id": 10,
      "score": 0.89,
      "metadata": {
        "name": "Budget Electronics Item",
        "description": "Affordable electronics product",
        "image_url": "https://example.com/electronics.jpg",
        "price": 49.99,
        "category": "electronics"
      },
      "fused_score": 0.89,
      "semantic_score": 0.85,
      "keyword_score": 0.92
    }
  ],
  "count": 1,
  "method": "hybrid (CLIP + BM25)",
  "weights": {
    "semantic": 0.7,
    "keyword": 0.3
  }
}
```

**Algorithme:**
- **Reciprocal Rank Fusion**: Combine les rankings
- **Scoring Formula**: `fused = (semantic * weight1) + (keyword * weight2)`

**Use Cases:**
- "red shoes" → Trouve items rouges ET items shoes
- "expensive camera" → Items chers ET catégorie camera

---

### 5. Recherche Vocale

#### `POST /api/v1/voice-search`

**Description:** Transcrire audio + recherche par texte transcrit

**Paramètres de Requête:**

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `file` | file | ✅ Requis | Fichier audio |
| `language` | string | "auto" | Langue (auto, en, fr, etc.) |
| `limit` | integer | 10 | Nombre max de résultats |

**Format Fichier Accepté:**
- MP3, WAV, M4A, FLAC, OGG
- Taille max: 25MB
- Durée recommandée: <60 secondes

**Réponse - Succès (200):**
```json
{
  "transcription": "I need blue running shoes",
  "language": "en",
  "confidence": 0.95,
  "results": [
    {
      "id": 1,
      "score": 0.88,
      "metadata": {
        "name": "Nike Blue Running Shoes",
        "description": "High-performance running shoes",
        "image_url": "https://example.com/shoe1.jpg",
        "price": 129.99,
        "category": "footwear"
      }
    }
  ],
  "count": 1,
  "search_type": "voice"
}
```

**Pipeline:**
1. 🎤 Audio → WAV (FFmpeg)
2. 🗣️ WAV → Texte (Whisper)
3. 🔍 Texte → Embedding (CLIP)
4. 📊 Embedding → Recherche (Qdrant)

**Notes:**
- ✅ Support multilingue (40+ langues)
- ✅ Auto-détection langue
- ✅ Whisper model: base (~140MB)
- ⏱️ Première utilisation: ~1-2 min (téléchargement modèle)

---

### 6. Indexation de Produits

#### `POST /api/v1/index`

**Description:** Ajouter/indexer un produit pour recherche

**Corps de la Requête:**
```json
{
  "product_id": "prod_123",
  "name": "Blue Running Shoes",
  "description": "High-performance running shoes with advanced cushioning",
  "metadata": {
    "image_url": "https://example.com/shoe.jpg",
    "price": 129.99,
    "category": "footwear",
    "url": "https://example.com/products/shoe"
  }
}
```

**Réponse - Succès (200):**
```json
{
  "status": "indexed",
  "product_id": "prod_123",
  "qdrant_id": 9223372036854775807,
  "embedding_dimension": 512
}
```

---

### 7. Statistiques et Monitoring

#### `GET /api/v1/stats`

**Description:** Obtenir les statistiques de la collection

**Réponse - Succès (200):**
```json
{
  "collection": {
    "name": "products",
    "points_count": 150,
    "vectors_count": 150,
    "segment_count": 1
  },
  "embedding_service": {
    "type": "CLIP",
    "model": "openai/clip-vit-base-patch32",
    "dimension": 512,
    "device": "cpu"
  }
}
```

---

## 🔐 Authentification

Actuellement: **Aucune authentification requise** (API interne)

Pour production, implémenter:
```python
# Bearer Token
Authorization: Bearer YOUR_API_KEY

# Ou API Key
X-API-Key: YOUR_API_KEY
```

---

## ⚠️ Gestion d'Erreurs

### Codes de Réponse Courants

| Code | Signification | Exemple |
|------|---------------|---------|
| **200** | ✅ Succès | Résultats retournés |
| **400** | ❌ Mauvaise requête | Query vide |
| **404** | ❌ Non trouvé | Endpoint inexistant |
| **500** | ❌ Erreur serveur | Qdrant indisponible |
| **503** | ⚠️ Service indisponible | Modèle CLIP non chargé |

### Format d'Erreur Standard

```json
{
  "detail": "Description de l'erreur"
}
```

### Erreurs Courantes

| Erreur | Cause | Solution |
|--------|-------|----------|
| Query cannot be empty | Pas de query | Ajouter `"query": "..."` |
| File must be an image | Format invalide | Utiliser JPEG/PNG |
| Failed to generate embedding | Modèle non chargé | Redémarrer service |
| Qdrant connection error | BD indisponible | Vérifier Qdrant |

---

## 📝 Exemples d'Utilisation

### cURL

#### Recherche Texte
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "blue shoes",
    "limit": 5
  }'
```

#### Recherche Image
```bash
curl -X POST "http://localhost:8000/api/v1/search-image" \
  -F "file=@product.jpg" \
  -F "limit=5"
```

#### Recherche Vocale
```bash
curl -X POST "http://localhost:8000/api/v1/voice-search" \
  -F "file=@query.mp3" \
  -F "language=en" \
  -F "limit=10"
```

#### Recherche Hybride (70% semantic, 30% keyword)
```bash
curl -X POST "http://localhost:8000/api/v1/search-hybrid" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cheap electronics",
    "limit": 10
  }'
```

#### Recherche Hybride (Poids customisés)
```bash
curl -X POST "http://localhost:8000/api/v1/search-hybrid?semantic_weight=0.5&keyword_weight=0.5" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "red expensive shoes",
    "limit": 10
  }'
```

### Python

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Recherche Texte
response = requests.post(
    f"{BASE_URL}/search",
    json={"query": "blue shoes", "limit": 5}
)
results = response.json()
print(f"Trouvé {results['count']} résultats")

# Recherche Image
files = {"file": open("shoe.jpg", "rb")}
response = requests.post(
    f"{BASE_URL}/search-image",
    files=files,
    params={"limit": 5}
)
results = response.json()

# Recherche Hybride
response = requests.post(
    f"{BASE_URL}/search-hybrid",
    json={"query": "cheap electronics", "limit": 10},
    params={
        "semantic_weight": 0.6,
        "keyword_weight": 0.4
    }
)
results = response.json()
print(f"Scores: Semantic={results['weights']['semantic']}, Keyword={results['weights']['keyword']}")

# Santé
response = requests.get(f"{BASE_URL}/health")
print(response.json()["status"])
```

### JavaScript/Node.js

```javascript
const BASE_URL = "http://localhost:8000/api/v1";

// Recherche Texte
async function searchText(query, limit = 10) {
  const response = await fetch(`${BASE_URL}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit })
  });
  return await response.json();
}

// Recherche Image
async function searchImage(file, limit = 10) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("limit", limit);
  
  const response = await fetch(`${BASE_URL}/search-image`, {
    method: "POST",
    body: formData
  });
  return await response.json();
}

// Exemple
const results = await searchText("blue shoes", 5);
console.log(`Found ${results.count} results`);
results.results.forEach(r => {
  console.log(`${r.metadata.name} (Score: ${(r.score * 100).toFixed(1)}%)`);
});
```

---

## 🔧 Configuration

### Variables d'Environnement

```bash
# API
API_PORT=8000
API_HOST=0.0.0.0

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=products

# CLIP Model
CLIP_MODEL=openai/clip-vit-base-patch32
DEVICE=cpu  # ou cuda

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379

# Whisper (Voice)
WHISPER_MODEL=base  # tiny, small, base, medium, large
```

---

## 📊 Benchmarks

### Latence par Type de Recherche

| Type | Temps Moyen | Min | Max | Notes |
|------|------------|-----|-----|-------|
| **Text Search** | 180ms | 120ms | 300ms | Avec preprocessing |
| **Image Search** | 250ms | 200ms | 400ms | Includes CLIP encoding |
| **Voice Search** | 2-3s | 1.5s | 5s | Include transcription Whisper |
| **Hybrid Search** | 300ms | 250ms | 500ms | CLIP + BM25 fusion |

### Performance par Collection Size

| Produits | Temps (ms) | Notes |
|----------|-----------|-------|
| 100 | ~150 | Optimal |
| 1,000 | ~180 | Normal |
| 10,000 | ~250 | Acceptable |
| 100,000 | ~400 | Recommander sharding |

---

## 🚨 Troubleshooting

### Problem: "Connection refused"
```
❌ Erreur: Cannot connect to Qdrant
✅ Solution: Vérifier que Qdrant est lancé
   docker-compose up -d
```

### Problem: "Out of memory"
```
❌ Erreur: CUDA out of memory
✅ Solution: Utiliser CPU ou augmenter RAM
   DEVICE=cpu
```

### Problem: "Slow responses"
```
❌ Erreur: Latence > 1 seconde
✅ Solution: 
   1. Réduire limit
   2. Utiliser GPU
   3. Augmenter RAM
   4. Vérifier Qdrant status
```

---

## 📚 Ressources

- **CLIP Paper**: https://arxiv.org/abs/2103.14030
- **Qdrant Docs**: https://qdrant.tech/documentation/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Whisper**: https://github.com/openai/whisper

---

## 📞 Support

Pour issues/questions:
- GitHub Issues: [iafrimallv100](https://github.com/edoukou07/iafrimallv100)
- Email: support@iafrimall.com

---

**Dernière mise à jour:** November 5, 2025  
**Statut:** ✅ Production Ready
