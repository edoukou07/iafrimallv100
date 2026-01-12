# 📚 Documentation API - ECommerce AI Search

**Version:** 3.0  
**Date:** Novembre 2025  
**Base URL:** `http://localhost:8000/api/v1`

---

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Health & Monitoring](#health--monitoring)
4. [Recherche Sémantique](#recherche-sémantique)
5. [Recherche par Image](#recherche-par-image)
6. [Recherche Hybride](#recherche-hybride)
7. [Recherche Vocale](#recherche-vocale)
8. [Embeddings](#embeddings)
9. [Indexation de Produits](#indexation-de-produits)
10. [Modèles de Données](#modèles-de-données)
11. [Codes d'Erreur](#codes-derreur)
12. [Exemples d'Intégration](#exemples-dintégration)

---

## Vue d'ensemble

### Capacités Principales

L'API offre **4 types de recherche** pour trouver des produits:

| Type | Description | Modèle | Latence |
|------|-------------|--------|---------|
| **Sémantique** | Comprend le sens et le contexte | CLIP ViT Base-32 | ~100ms |
| **Image** | Recherche par image visuellement similaire | CLIP ViT Base-32 | ~150ms |
| **Hybride** | Combine recherche sémantique + mots-clés (BM25) | CLIP + BM25 | ~200ms |
| **Vocale** | Transcription audio + recherche sémantique | Whisper + CLIP | ~500ms |

### Architecture Technique

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT (Web/Mobile)                  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              FastAPI (Port 8000)                        │
│  ├─ /api/v1/search           (Recherche sémantique)   │
│  ├─ /api/v1/search-image     (Recherche image)        │
│  ├─ /api/v1/search-hybrid    (Recherche hybride)      │
│  ├─ /api/v1/voice-search     (Recherche vocale)       │
│  └─ /api/v1/embed*           (Embeddings)              │
└────────────────────┬────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼───────────┐ ┌──▼──────────┐ ┌─▼────────────────┐
│  CLIP Model   │ │ Whisper     │ │ Redis Queue      │
│  (512-dim)    │ │ (Audio)     │ │ (Async jobs)     │
└───────────────┘ └─────────────┘ └──────────────────┘
    │
┌───▼──────────────────────────────────┐
│   Qdrant Vector Database             │
│   (Azure 52.143.186.136:6333)       │
│   - Collections d'embeddings         │
│   - Recherche par similarité         │
└──────────────────────────────────────┘
```

---

## Health & Monitoring

### 🏥 Vérifier l'État de l'API

**Endpoint:** `GET /api/v1/health`

**Description:** Vérifie la connexion avec Qdrant et retourne les statistiques

**Réponse (Succès - 200):**
```json
{
  "status": "healthy",
  "service": "Image Search API (Container Apps)",
  "version": "3.0",
  "qdrant": {
    "connected": true,
    "stats": {
      "collection_count": 1,
      "collections": {
        "products": {
          "points_count": 1250,
          "vectors_count": 1250,
          "vector_size": 512
        }
      }
    }
  }
}
```

**Réponse (Erreur - 500):**
```json
{
  "status": "unhealthy",
  "error": "Connection refused: Cannot reach Qdrant at 52.143.186.136:6333"
}
```

**Curl:**
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

---

### 📊 Statistiques Détaillées

**Endpoint:** `GET /api/v1/stats`

**Réponse:**
```json
{
  "collections": {
    "products": {
      "points_count": 1250,
      "vectors_count": 1250,
      "vector_size": 512,
      "indexing_status": "ready",
      "created_at": "2025-10-15T10:30:00Z"
    }
  },
  "performance": {
    "avg_query_latency_ms": 125,
    "total_queries": 5420,
    "cache_hit_rate": 0.35
  }
}
```

---

## Recherche Sémantique

### 📝 Recherche par Texte

**Endpoint:** `POST /api/v1/search`

**Description:** Recherche produits par description textuelle avec compréhension du contexte (CLIP)

**Paramètres (Body - JSON):**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `query` | string | ✅ | - | Texte à rechercher (ex: "chemises rouges pas chères") |
| `limit` | integer | ❌ | 10 | Nombre de résultats (1-100) |

**Paramètres (Query - URL):**

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `score_threshold` | float | 0.3 | Score minimum de similarité (0.0-1.0) |

**Réponse (Succès - 200):**
```json
{
  "query": "chemises rouges pas chères",
  "results": [
    {
      "id": "shirt_001",
      "name": "Chemise Coton Rouge",
      "description": "Chemise en coton rouge confortable et durable",
      "image_url": "https://example.com/shirt_001.jpg",
      "image": "https://example.com/shirt_001.jpg",
      "price": 24.99,
      "category": "vêtements",
      "score": 0.87,
      "metadata": {
        "color": "rouge",
        "material": "coton",
        "size": "M-XL"
      }
    },
    {
      "id": "shirt_002",
      "name": "T-Shirt Rouge Budget",
      "description": "T-shirt rouge abordable pour tous les jours",
      "image_url": "https://example.com/shirt_002.jpg",
      "image": "https://example.com/shirt_002.jpg",
      "price": 14.99,
      "category": "vêtements",
      "score": 0.82,
      "metadata": {
        "color": "rouge",
        "material": "polyester",
        "size": "S-XXL"
      }
    }
  ],
  "count": 2,
  "method": "semantic (CLIP)",
  "execution_time_ms": 145.3
}
```

**Réponse (Erreur - 400):**
```json
{
  "detail": "Query cannot be empty"
}
```

**Curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "chemises rouges pas chères",
    "limit": 10
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/search",
    json={
        "query": "chemises rouges pas chères",
        "limit": 10
    }
)
results = response.json()["results"]
print(f"Trouvé {len(results)} produits")
for product in results:
    print(f"  - {product['name']} (score: {product['score']:.2f})")
```

**JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/api/v1/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'chemises rouges pas chères',
    limit: 10
  })
});

const data = await response.json();
console.log(`Trouvé ${data.count} produits`);
data.results.forEach(product => {
  console.log(`  - ${product.name} (score: ${product.score.toFixed(2)})`);
});
```

**Optimisations de Recherche:**

- **Préprocessing Texte:** Minuscules, suppression d'URL, nettoyage caractères spéciaux
- **Expansion de Requête:** Synonymes appliqués automatiquement
  - "chaussures" → "chaussures, chaussure, basket, sneaker, botte, sandal"
  - "cher" → "cher, couteux, premium, luxe, haut de gamme"
  - "bon" → "bon, excellent, super, genial, qualite"
- **Score Seuil:** 0.3 par défaut (ajustable)

---

## Recherche par Image

### 🖼️ Recherche Visuelle par URL ou Fichier

**Endpoint:** `POST /api/v1/search-image`

**Description:** Recherche produits visuellement similaires à une image

**Paramètres:**

| Paramètre | Type | Position | Requis | Description |
|-----------|------|----------|--------|-------------|
| `image_file` | file | Body | ✅ (si pas URL) | Fichier image (JPEG, PNG) |
| `image_url` | string | Query | ✅ (si pas fichier) | URL de l'image à chercher |
| `limit` | integer | Query | ❌ | Nombre de résultats (défaut: 10) |

**Formats acceptés:** JPEG, PNG, WebP, BMP

**Réponse (Succès - 200):**
```json
{
  "query_image": "dress_query.jpg",
  "model": "CLIP-ViT-Base-32",
  "embedding_dimension": 512,
  "count": 3,
  "results": [
    {
      "id": "dress_001",
      "name": "Red Summer Dress",
      "description": "Flowing red cotton summer dress perfect for warm days",
      "image_url": "https://example.com/dress_001.jpg",
      "image": "https://example.com/dress_001.jpg",
      "price": 49.99,
      "category": "dresses",
      "score": 0.91,
      "metadata": {
        "color": "red",
        "material": "cotton",
        "season": "summer"
      }
    },
    {
      "id": "dress_005",
      "name": "Red Party Dress",
      "description": "Elegant red dress for special occasions",
      "image_url": "https://example.com/dress_005.jpg",
      "image": "https://example.com/dress_005.jpg",
      "price": 79.99,
      "category": "dresses",
      "score": 0.87,
      "metadata": {
        "color": "red",
        "material": "polyester",
        "season": "all"
      }
    }
  ],
  "execution_time_ms": 182.4
}
```

**Curl (URL):**
```bash
curl -X POST "http://localhost:8000/api/v1/search-image?limit=10" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/dress.jpg"}'
```

**Curl (Fichier):**
```bash
curl -X POST "http://localhost:8000/api/v1/search-image?limit=10" \
  -F "image_file=@/path/to/dress.jpg"
```

**Python:**
```python
# Avec URL
response = requests.post(
    "http://localhost:8000/api/v1/search-image",
    params={"limit": 10},
    json={"image_url": "https://example.com/dress.jpg"}
)

# Avec fichier local
with open("dress.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/search-image",
        params={"limit": 10},
        files={"image_file": f}
    )

results = response.json()["results"]
```

**JavaScript:**
```javascript
// Avec URL
const response = await fetch('http://localhost:8000/api/v1/search-image?limit=10', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    image_url: 'https://example.com/dress.jpg'
  })
});

// Avec fichier local
const formData = new FormData();
formData.append('image_file', fileInput.files[0]);
const response = await fetch('http://localhost:8000/api/v1/search-image?limit=10', {
  method: 'POST',
  body: formData
});

const data = await response.json();
```

**Caractéristiques:**

- **Modèle:** CLIP-ViT-Base-32 (512-dimensional vectors)
- **Score Seuil:** 0.2 (plus bas que texte car distribution différente)
- **Latence:** ~150-180ms par recherche
- **Cache:** Résultats mémorisés pour images récurrentes

---

## Recherche Hybride

### 🔀 Combinaison Recherche Sémantique + Mots-clés

**Endpoint:** `POST /api/v1/search-hybrid`

**Description:** Fusionne résultats de recherche sémantique (CLIP) et recherche par mots-clés (BM25)

Cette approche améliore:
- ✅ Rappel (recall) - trouve plus de résultats pertinents
- ✅ Précision (precision) - classe mieux les résultats
- ✅ Variété - combine signification + termes exacts

**Paramètres (Body - JSON):**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `query` | string | ✅ | - | Texte à rechercher |
| `limit` | integer | ❌ | 10 | Nombre de résultats (1-100) |

**Paramètres (Query - URL):**

| Paramètre | Type | Défaut | Plage | Description |
|-----------|------|--------|-------|-------------|
| `semantic_weight` | float | 0.7 | 0.0-1.0 | Poids recherche sémantique (%) |
| `keyword_weight` | float | 0.3 | 0.0-1.0 | Poids recherche mots-clés (%) |

**Algorithme:** Reciprocal Rank Fusion (RRF)

```
Formule: fused_score = 
    semantic_weight * (1 / (rank_semantic + 60)) +
    keyword_weight * (1 / (rank_keyword + 60))

Paramètre +60 : évite instabilité avec premiers résultats
```

**Réponse (Succès - 200):**
```json
{
  "query": "chaussures sport pas chères",
  "results": [
    {
      "id": "shoes_001",
      "name": "Sneakers Running Bleu",
      "description": "Chaussures de sport légères et confortables",
      "image_url": "https://example.com/shoes_001.jpg",
      "image": "https://example.com/shoes_001.jpg",
      "price": 54.99,
      "category": "chaussures",
      "semantic_score": 0.89,
      "keyword_score": 0.85,
      "fused_score": 0.88,
      "rank_semantic": 1,
      "rank_keyword": 2,
      "metadata": {}
    },
    {
      "id": "shoes_002",
      "name": "Training Shoes Budget",
      "description": "Chaussures abordables pour l'entraînement",
      "image_url": "https://example.com/shoes_002.jpg",
      "image": "https://example.com/shoes_002.jpg",
      "price": 34.99,
      "category": "chaussures",
      "semantic_score": 0.76,
      "keyword_score": 0.92,
      "fused_score": 0.81,
      "rank_semantic": 3,
      "rank_keyword": 1,
      "metadata": {}
    }
  ],
  "count": 2,
  "method": "hybrid (CLIP + BM25)",
  "execution_time_ms": 215.7,
  "weights": {
    "semantic": 0.7,
    "keyword": 0.3
  }
}
```

**Curl:**
```bash
# Poids par défaut (70% sémantique, 30% mots-clés)
curl -X POST "http://localhost:8000/api/v1/search-hybrid?semantic_weight=0.7&keyword_weight=0.3" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "chaussures sport pas chères",
    "limit": 10
  }'

# Plus de poids sur recherche par mots-clés
curl -X POST "http://localhost:8000/api/v1/search-hybrid?semantic_weight=0.5&keyword_weight=0.5" \
  -H "Content-Type: application/json" \
  -d '{"query": "nike adidas puma", "limit": 10}'
```

**Python:**
```python
response = requests.post(
    "http://localhost:8000/api/v1/search-hybrid",
    params={
        "semantic_weight": 0.7,
        "keyword_weight": 0.3
    },
    json={
        "query": "chaussures sport pas chères",
        "limit": 10
    }
)

results = response.json()["results"]
for product in results:
    print(f"{product['name']}: "
          f"sémantique={product['semantic_score']:.2f}, "
          f"mots-clés={product['keyword_score']:.2f}, "
          f"fusionné={product['fused_score']:.2f}")
```

**Cas d'usage:**

- `semantic_weight=1.0, keyword_weight=0.0` : Recherche purement sémantique
- `semantic_weight=0.5, keyword_weight=0.5` : Équilibre parfait
- `semantic_weight=0.3, keyword_weight=0.7` : Privilégier les mots-clés exacts

---

## Recherche Vocale

### 🎤 Recherche par Audio

**Endpoint:** `POST /api/v1/voice-search`

**Description:** Transcrit audio en texte, puis effectue recherche sémantique

Processus:
1. ✅ Upload fichier audio
2. ✅ Transcription avec OpenAI Whisper (base model)
3. ✅ Détection automatique de langue
4. ✅ Préprocessing du texte transcrit
5. ✅ Recherche sémantique CLIP
6. ✅ Enrichissement avec images produits

**Paramètres:**

| Paramètre | Type | Position | Requis | Description |
|-----------|------|----------|--------|-------------|
| `audio_file` | file | Body | ✅ | Fichier audio |
| `language` | string | Query | ❌ | Code langue (ex: 'en', 'fr') - auto-détection si absent |
| `limit` | integer | Query | ❌ | Nombre de résultats (défaut: 10, max: 100) |

**Formats audio acceptés:** MP3, WAV, M4A, FLAC, OGG, WebM

**Taille maximale:** 25 MB

**Réponse (Succès - 200):**
```json
{
  "transcription": "je cherche des chaussures de sport pas chères",
  "language": "fr",
  "confidence": 0.97,
  "results": [
    {
      "id": "shoes_001",
      "name": "Sneakers Running Bleu",
      "description": "Chaussures de sport légères et confortables",
      "image": "https://example.com/shoes_001.jpg",
      "score": 0.89
    },
    {
      "id": "shoes_002",
      "name": "Training Shoes Budget",
      "description": "Chaussures abordables pour l'entraînement",
      "image": "https://example.com/shoes_002.jpg",
      "score": 0.76
    }
  ],
  "count": 2,
  "search_type": "voice",
  "execution_time_ms": 520.3
}
```

**Curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/voice-search?language=fr&limit=10" \
  -F "audio_file=@audio.wav"
```

**Python:**
```python
with open("query.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/voice-search",
        params={
            "language": "fr",
            "limit": 10
        },
        files={"audio_file": f}
    )

data = response.json()
print(f"Transcription: {data['transcription']}")
print(f"Confiance: {data['confidence']:.1%}")
print(f"Résultats: {data['count']} produits trouvés")
```

**JavaScript (Web):**
```javascript
// Enregistrement audio avec Web Audio API
const mediaRecorder = new MediaRecorder(stream);
const chunks = [];

mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
mediaRecorder.onstop = async () => {
  const audioBlob = new Blob(chunks, { type: 'audio/wav' });
  const formData = new FormData();
  formData.append('audio_file', audioBlob, 'query.wav');
  formData.append('language', 'fr');

  const response = await fetch('http://localhost:8000/api/v1/voice-search?limit=10', {
    method: 'POST',
    body: formData
  });

  const data = await response.json();
  console.log(`Transcription: ${data.transcription}`);
  console.log(`Confiance: ${(data.confidence * 100).toFixed(1)}%`);
  console.log(`Trouvé ${data.count} produits`);
};

mediaRecorder.start();
// ... enregistrement ...
mediaRecorder.stop();
```

**Optimisations:**

- **Modèle:** OpenAI Whisper (base) - bon compromis vitesse/qualité
- **Multi-langue:** Détection automatique ou spécification explicite
- **Score Seuil:** 0.3 (identique à recherche sémantique)
- **Latence:** ~500ms (transcription + recherche)

---

### 🔊 Infos du Modèle Whisper

**Endpoint:** `GET /api/v1/voice/model-info`

**Réponse:**
```json
{
  "model": "openai/whisper-base",
  "size": "140MB",
  "languages_supported": 99,
  "average_transcription_time_ms": 350,
  "accuracy": "~94% (benchmarked on English)"
}
```

### 🏥 Vérification Santé Service Vocal

**Endpoint:** `GET /api/v1/health/voice`

**Réponse:**
```json
{
  "status": "healthy",
  "service": "voice",
  "model_size": "base",
  "model_loaded": true,
  "device": "cpu"
}
```

---

## Embeddings

### 📦 Générer un Embedding Texte

**Endpoint:** `POST /api/v1/embed`

**Description:** Convertit texte en vecteur 512-dimensionnel (CLIP)

**Paramètres (Body - JSON):**

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `text` | string | ✅ | Texte à encoder |

**Réponse (Succès - 200):**
```json
{
  "text": "Red cotton shirt",
  "embedding": [
    0.1234, 0.5678, -0.2345, ..., 0.0123
  ],
  "dimension": 512,
  "model": "CLIP-ViT-Base-32"
}
```

**Curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/embed" \
  -H "Content-Type: application/json" \
  -d '{"text": "Red cotton shirt"}'
```

**Python:**
```python
response = requests.post(
    "http://localhost:8000/api/v1/embed",
    json={"text": "Red cotton shirt"}
)

embedding = response.json()["embedding"]
print(f"Dimension: {len(embedding)}")
print(f"Premiers 5 éléments: {embedding[:5]}")
```

---

### 🖼️ Générer un Embedding Image

**Endpoint:** `POST /api/v1/embed-image`

**Description:** Convertit image en vecteur 512-dimensionnel (CLIP)

**Paramètres:**

| Paramètre | Type | Position | Requis | Description |
|-----------|------|----------|--------|-------------|
| `image_file` | file | Body | ✅ | Fichier image |

**Réponse (Succès - 200):**
```json
{
  "image": "shirt.jpg",
  "embedding": [
    0.2456, -0.1234, 0.3456, ..., 0.0789
  ],
  "dimension": 512,
  "model": "CLIP-ViT-Base-32"
}
```

**Curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/embed-image" \
  -F "image_file=@shirt.jpg"
```

**Python:**
```python
with open("shirt.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/embed-image",
        files={"image_file": f}
    )

embedding = response.json()["embedding"]
```

---

## Indexation de Produits

### 📝 Indexer un Produit (Texte)

**Endpoint:** `POST /api/v1/index-product`

**Description:** Ajoute produit à la base de données Qdrant

**Paramètres (FormData):**

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `product_id` | string | ✅ | ID unique produit |
| `name` | string | ✅ | Nom produit |
| `description` | string | ✅ | Description détaillée |
| `metadata` | JSON | ❌ | Métadonnées (prix, catégorie, etc.) |

**Réponse (Succès - 200):**
```json
{
  "status": "success",
  "message": "Product indexed successfully",
  "product_id": "shirt_001",
  "embedding_type": "text",
  "embedding_dimension": 512
}
```

**Curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/index-product" \
  -F "product_id=shirt_001" \
  -F "name=Red Cotton Shirt" \
  -F "description=Beautiful red cotton shirt, perfect for casual wear" \
  -F 'metadata={"price": 29.99, "category": "clothing", "color": "red"}'
```

**Python:**
```python
response = requests.post(
    "http://localhost:8000/api/v1/index-product",
    data={
        "product_id": "shirt_001",
        "name": "Red Cotton Shirt",
        "description": "Beautiful red cotton shirt, perfect for casual wear"
    },
    files={"metadata": open("metadata.json", "rb")}
)
```

---

### 🖼️ Indexer un Produit avec Image

**Endpoint:** `POST /api/v1/index-product-with-image`

**Description:** Ajoute produit avec image - enqueuing asynchrone pour traitement en background

**Paramètres (FormData):**

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `product_id` | string | ✅ | ID unique produit |
| `name` | string | ✅ | Nom produit |
| `description` | string | ✅ | Description |
| `image_file` | file | ✅ | Image produit |
| `metadata` | JSON | ❌ | Métadonnées |

**Réponse (Succès - 202 - Queued):**
```json
{
  "status": "queued",
  "message": "Product queued for indexing",
  "job_id": "index_abc123def456",
  "product_id": "shirt_001",
  "embedding_type": "image",
  "embedding_dimension": 512,
  "queue_position": 3
}
```

**Curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/index-product-with-image" \
  -F "product_id=shirt_001" \
  -F "name=Red Cotton Shirt" \
  -F "description=Beautiful red cotton shirt" \
  -F "image_file=@shirt.jpg" \
  -F 'metadata={"price": 29.99, "category": "clothing"}'
```

**Vérifier Statut du Job:**

```bash
curl -X GET "http://localhost:8000/api/v1/queue/status/{job_id}"
```

**Réponse:**
```json
{
  "job_id": "index_abc123def456",
  "status": "completed",
  "product_id": "shirt_001",
  "embedding_type": "image",
  "vector_size": 512,
  "points_indexed": 1,
  "execution_time_ms": 450,
  "created_at": "2025-11-05T10:30:00Z",
  "completed_at": "2025-11-05T10:30:00.450Z"
}
```

---

## Modèles de Données

### SearchRequest

```json
{
  "query": "string (required)",
  "limit": "integer (default: 10, min: 1, max: 100)"
}
```

### SearchResult

```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "image": "string (URL)",
  "price": "float",
  "category": "string",
  "score": "float (0.0-1.0)",
  "metadata": "object"
}
```

### Product

```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "image_url": "string",
  "category": "string",
  "price": "float",
  "attributes": "object (optional)",
  "embedding": "array[float] (optional)",
  "created_at": "datetime (ISO 8601)"
}
```

### IndexJob

```json
{
  "job_id": "string (UUID)",
  "product_id": "string",
  "status": "string (queued|processing|completed|failed)",
  "embedding_type": "string (text|image)",
  "embedding_dimension": "integer (512)",
  "error_message": "string (if failed)",
  "retry_count": "integer",
  "created_at": "datetime (ISO 8601)",
  "completed_at": "datetime (ISO 8601, optional)"
}
```

---

## Codes d'Erreur

| Code | Message | Cause | Solution |
|------|---------|-------|----------|
| **400** | Query cannot be empty | Requête vide ou nulle | Fournir une requête non vide |
| **400** | Provide either image_url or text_query, not both | Ambiguïté | Choisir image OU texte |
| **400** | Invalid score_threshold | Valeur hors limites | Utiliser valeur entre 0.0 et 1.0 |
| **404** | Collection not found | Qdrant vide | Indexer des produits d'abord |
| **413** | Payload too large | Fichier image trop gros | Réduire taille à <25MB |
| **415** | Unsupported media type | Format fichier invalide | Utiliser JPEG, PNG, ou WAV |
| **500** | Failed to generate embedding | Erreur modèle CLIP | Vérifier santé du service (health) |
| **500** | Connection refused: Cannot reach Qdrant | Qdrant indisponible | Redémarrer Docker/service Qdrant |
| **503** | Service Unavailable | API surchargée | Réessayer avec backoff exponentiel |

**Exemple de gestion d'erreur (Python):**

```python
import requests
from requests.exceptions import RequestException
import time

def search_with_retry(query, max_retries=3, backoff_factor=2):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/search",
                json={"query": query, "limit": 10},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if response.status_code == 503 and attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                print(f"Service indisponible, réessai dans {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
        
        except RequestException as e:
            print(f"Erreur requête: {e}")
            raise
```

---

## Exemples d'Intégration

### Intégration Django

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import requests

API_BASE = "http://localhost:8000/api/v1"

@require_http_methods(["POST"])
def search_products(request):
    query = request.POST.get("q", "")
    
    if not query:
        return JsonResponse({"error": "Query required"}, status=400)
    
    try:
        response = requests.post(
            f"{API_BASE}/search",
            json={"query": query, "limit": 20},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        return JsonResponse({
            "results": data["results"],
            "count": data["count"],
            "execution_time_ms": data["execution_time_ms"]
        })
    
    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)
```

### Intégration React

```javascript
import React, { useState } from 'react';

function SearchComponent() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: 20 })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      setResults(data.results);
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSearch}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Rechercher..."
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Recherche...' : 'Chercher'}
        </button>
      </form>

      <div className="results">
        {results.map(product => (
          <div key={product.id} className="product-card">
            <img src={product.image} alt={product.name} />
            <h3>{product.name}</h3>
            <p>{product.description}</p>
            <p className="score">Score: {(product.score * 100).toFixed(1)}%</p>
            <p className="price">{product.price} €</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SearchComponent;
```

### Intégration Mobile (Flutter)

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class SearchService {
  static const String API_BASE = 'http://localhost:8000/api/v1';

  static Future<List<Product>> search(String query, {int limit = 10}) async {
    try {
      final response = await http.post(
        Uri.parse('$API_BASE/search'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'query': query, 'limit': limit}),
      );

      if (response.statusCode != 200) {
        throw Exception('Search failed: ${response.statusCode}');
      }

      final data = jsonDecode(response.body);
      return (data['results'] as List)
          .map((p) => Product.fromJson(p))
          .toList();
    } catch (e) {
      rethrow;
    }
  }
}

class Product {
  final String id;
  final String name;
  final String description;
  final String image;
  final double price;
  final double score;

  Product({
    required this.id,
    required this.name,
    required this.description,
    required this.image,
    required this.price,
    required this.score,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      image: json['image'],
      price: json['price'].toDouble(),
      score: json['score'].toDouble(),
    );
  }
}
```

---

## Performance & Optimisations

### Latence Typique par Recherche

| Type | Latence Moyenne | Min | Max | Remarques |
|------|-----------------|-----|-----|-----------|
| Texte/Sémantique | 100-150ms | 80ms | 300ms | Déterministe |
| Image | 150-200ms | 120ms | 400ms | Décodage image variable |
| Hybride | 200-250ms | 180ms | 500ms | Fusion + 2 sources |
| Vocale | 400-600ms | 350ms | 2000ms | Transcription en goulot |

### Optimisations Recommandées

#### Côté Client

```python
# 1. Cacher résultats pour requêtes identiques
import functools

@functools.lru_cache(maxsize=100)
def search_cached(query):
    # Cache pendant session
    pass

# 2. Batch requests
results = []
queries = ["chaussures", "chemises", "pantalons"]
for q in queries:
    # Meilleur: API batch endpoint (futur)
    results.append(search_product(q))

# 3. Pagination
limit = 10
offset = 0
for page in range(num_pages):
    results = search_product(query, limit=limit)  # offset via limit
    offset += limit
```

#### Côté Serveur

- **Index Qdrant:** Pré-indexer tous les produits
- **Redis Cache:** Résultats de requêtes populaires
- **Rate Limiting:** Limiter à 100 req/s par client
- **Connection Pool:** Réutiliser connexions

---

## Support & Troubleshooting

### Vérification Générale

```bash
# 1. API santé
curl http://localhost:8000/api/v1/health

# 2. Stats base de données
curl http://localhost:8000/api/v1/stats

# 3. Modèle vocal
curl http://localhost:8000/api/v1/voice/model-info

# 4. Test simple
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 1}'
```

### Problèmes Communs

**Problème:** `Connection refused: Cannot reach Qdrant`

**Solution:**
```bash
# Redémarrer Qdrant
docker-compose down
docker-compose up qdrant -d

# Vérifier santé
curl http://localhost:6333/health
```

---

**Document Version:** 3.0  
**Dernière mise à jour:** Novembre 2025  
**Auteur:** AI Team  
**Contact:** support@example.com
