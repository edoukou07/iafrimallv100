# 🚀 API V2 - Guide d'Intégration Frontend

> **Base URL**: `http://20.238.104.13:8000`  
> **Version**: V2 avec Named Vectors  
> **Collection Qdrant**: `products_v2`

---

## 📋 Table des Matières

1. [Recherche Texte](#1-recherche-texte)
2. [Recherche Image](#2-recherche-image)
3. [Recherche Multimodale](#3-recherche-multimodale)
4. [Indexation Batch (Async)](#4-indexation-batch-async)
5. [Indexation Batch (Sync)](#5-indexation-batch-sync)
6. [Liste des Produits Indexés](#6-liste-des-produits-indexés)
7. [Détails d'un Produit](#7-détails-dun-produit)
8. [Statistiques](#8-statistiques)
9. [Health Check](#9-health-check)
10. [Structure des Données](#10-structure-des-données)

---

## 1. Recherche Texte

Recherche sémantique par texte utilisant le vecteur `text_vector` (512 dimensions CLIP).

### Endpoint
```
POST /api/v1/v2/search
```

### Headers
```
Content-Type: application/json
```

### Body (JSON)
```json
{
  "query": "robe rouge élégante",
  "limit": 10
}
```

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `query` | string | ✅ | Texte de recherche (langage naturel) |
| `limit` | integer | ❌ | Nombre de résultats (défaut: 10, max: 100) |

### Réponse (200 OK)
```json
{
  "query": "robe rouge élégante",
  "results": [
    {
      "id": "prod-123",
      "score": 0.87,
      "metadata": {
        "title": "Robe de Soirée Rouge",
        "description": "Magnifique robe rouge pour occasions spéciales",
        "price": 25000,
        "sale_price": 20000,
        "currency": "XOF",
        "category_name": "Robes",
        "provider_name": "Fashion Store",
        "image_url": "https://example.com/image.jpg",
        "tags": ["robe", "rouge", "soirée"],
        "has_text_embedding": true,
        "has_image_embedding": true
      }
    }
  ],
  "count": 10,
  "vector_used": "text_vector"
}
```

### Exemple JavaScript
```javascript
const response = await fetch('http://20.238.104.13:8000/api/v1/v2/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'robe rouge élégante',
    limit: 10
  })
});
const data = await response.json();
console.log(data.results);
```

---

## 2. Recherche Image

Recherche visuelle par image utilisant le vecteur `image_vector` (512 dimensions CLIP).

### Endpoint
```
POST /api/v1/v2/search-image
```

### Headers
```
Content-Type: multipart/form-data
```

### Body (FormData)
| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `file` | File | ✅ | Image à rechercher (JPEG, PNG, WebP) |
| `limit` | integer | ❌ | Nombre de résultats (défaut: 10) |

### Réponse (200 OK)
```json
{
  "results": [
    {
      "id": "prod-456",
      "score": 0.92,
      "metadata": {
        "title": "Sac à Main Cuir",
        "description": "Sac en cuir véritable",
        "price": 45000,
        "currency": "XOF",
        "category_name": "Accessoires",
        "provider_name": "Luxury Bags",
        "image_url": "https://example.com/bag.jpg",
        "has_text_embedding": true,
        "has_image_embedding": true
      }
    }
  ],
  "count": 10,
  "vector_used": "image_vector"
}
```

### Exemple JavaScript
```javascript
const formData = new FormData();
formData.append('file', imageFile);  // File object
formData.append('limit', '10');

const response = await fetch('http://20.238.104.13:8000/api/v1/v2/search-image', {
  method: 'POST',
  body: formData
});
const data = await response.json();
```

---

## 3. Recherche Multimodale

Recherche combinant texte ET image avec pondération ajustable.

### Endpoint
```
POST /api/v1/v2/search-multimodal
```

### Headers
```
Content-Type: multipart/form-data
```

### Body (FormData)
| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `text_query` | string | ❌* | Texte de recherche |
| `image_file` | File | ❌* | Image à rechercher |
| `limit` | integer | ❌ | Nombre de résultats (défaut: 10) |
| `text_weight` | float | ❌ | Poids du texte 0-1 (défaut: 0.5) |
| `image_weight` | float | ❌ | Poids de l'image 0-1 (défaut: 0.5) |

> *Au moins `text_query` ou `image_file` doit être fourni.

### Réponse (200 OK)
```json
{
  "results": [...],
  "count": 10,
  "method": "multimodal",
  "weights": {
    "text": 0.6,
    "image": 0.4
  }
}
```

### Exemple JavaScript
```javascript
const formData = new FormData();
formData.append('text_query', 'sac cuir noir');
formData.append('image_file', imageFile);
formData.append('text_weight', '0.6');
formData.append('image_weight', '0.4');
formData.append('limit', '20');

const response = await fetch('http://20.238.104.13:8000/api/v1/v2/search-multimodal', {
  method: 'POST',
  body: formData
});
```

---

## 4. Indexation Batch (Async)

Indexation asynchrone de plusieurs produits. Les résultats sont envoyés via callback.

### Endpoint
```
POST /indexation/products
```

### Headers
```
Content-Type: application/json
Authorization: Bearer <API_KEY>  (optionnel)
```

### Body (JSON)
```json
{
  "batchId": "batch-20260201-001",
  "callbackUrl": "https://votre-backend.com/api/callback/indexation/",
  "products": [
    {
      "id": "prod-001",
      "title": "iPhone 15 Pro",
      "slug": "iphone-15-pro",
      "description": "Le dernier iPhone avec puce A17 Pro",
      "shortDescription": "iPhone 15 Pro 256GB",
      "price": 750000,
      "salePrice": 699000,
      "currency": "XOF",
      "category": {
        "id": "cat-electronics",
        "name": "Électronique",
        "slug": "electronique"
      },
      "provider": {
        "id": "provider-001",
        "storeName": "Apple Store CI"
      },
      "images": [
        {
          "url": "https://example.com/iphone.jpg",
          "altText": "iPhone 15 Pro",
          "isPrimary": true
        }
      ],
      "tags": ["apple", "iphone", "smartphone"],
      "attributes": [
        { "name": "Couleur", "value": "Noir" },
        { "name": "Stockage", "value": "256GB" }
      ],
      "seoTitle": "iPhone 15 Pro - Apple Store CI",
      "seoDescription": "Achetez l'iPhone 15 Pro",
      "seoKeywords": ["iphone", "apple", "smartphone"],
      "metadata": {}
    }
  ]
}
```

### Réponse (202 Accepted)
```json
{
  "status": "accepted",
  "batchId": "batch-20260201-001",
  "productsReceived": 1,
  "message": "Batch accepted for processing. Results will be sent to callback URL.",
  "estimatedTimeSeconds": 3
}
```

### Callback Reçu (POST vers callbackUrl)
```json
{
  "batchId": "batch-20260201-001",
  "results": [
    {
      "productId": "prod-001",
      "success": true,
      "hasTextEmbedding": true,
      "hasImageEmbedding": true,
      "processingTimeMs": 2500
    }
  ],
  "totalProcessed": 1,
  "successCount": 1,
  "failureCount": 0,
  "processingTimeMs": 2500
}
```

---

## 5. Indexation Batch (Sync)

Indexation synchrone (bloquante) - **pour tests uniquement** (max 50 produits).

### Endpoint
```
POST /indexation/products/sync
```

### Body
Même structure que l'indexation async.

### Réponse (200 OK)
Retourne directement le callback (même structure).

---

## 6. Liste des Produits Indexés

Récupérer tous les produits indexés avec pagination.

### Endpoint
```
GET /indexation/products
```

### Query Parameters
| Param | Type | Défaut | Description |
|-------|------|--------|-------------|
| `limit` | integer | 50 | Produits par page (max 100) |
| `offset` | integer | null | ID pour pagination |

### Réponse (200 OK)
```json
{
  "status": "success",
  "data": [
    {
      "id": "prod-001",
      "qdrant_id": 3860791872220546060,
      "title": "iPhone 15 Pro",
      "description": "Le dernier iPhone...",
      "short_description": "iPhone 15 Pro 256GB",
      "price": 750000,
      "sale_price": 699000,
      "currency": "XOF",
      "category_name": "Électronique",
      "category_id": "cat-electronics",
      "provider_name": "Apple Store CI",
      "provider_id": "provider-001",
      "image_url": "https://example.com/iphone.jpg",
      "images": [],
      "tags": ["apple", "iphone"],
      "attributes": [],
      "has_text_embedding": true,
      "has_image_embedding": true,
      "indexed_at": "2026-02-01T19:43:17.461522"
    }
  ],
  "count": 50,
  "next_offset": 1234567890,
  "has_more": true
}
```

### Pagination
```javascript
// Page 1
const page1 = await fetch('/indexation/products?limit=50');
const data1 = await page1.json();

// Page 2
if (data1.has_more) {
  const page2 = await fetch(`/indexation/products?limit=50&offset=${data1.next_offset}`);
}
```

---

## 7. Détails d'un Produit

Récupérer un produit spécifique par son ID.

### Endpoint
```
GET /indexation/products/{product_id}
```

### Réponse (200 OK)
```json
{
  "status": "success",
  "data": {
    "id": "prod-001",
    "qdrant_id": 3860791872220546060,
    "title": "iPhone 15 Pro",
    "description": "Le dernier iPhone...",
    "price": 750000,
    "currency": "XOF",
    "category_name": "Électronique",
    "provider_name": "Apple Store CI",
    "image_url": "https://example.com/iphone.jpg",
    "has_text_embedding": true,
    "has_image_embedding": true,
    "indexed_at": "2026-02-01T19:43:17.461522"
  }
}
```

### Réponse (404 Not Found)
```json
{
  "detail": "Product not found"
}
```

---

## 8. Statistiques

Obtenir les statistiques de la collection Qdrant.

### Endpoint
```
GET /api/v1/v2/stats
```

### Réponse (200 OK)
```json
{
  "collection": {
    "name": "products_v2",
    "points_count": 150,
    "vectors_count": 300,
    "vector_config": {
      "text_vector": "512d CLIP",
      "image_vector": "512d CLIP"
    },
    "status": "green"
  }
}
```

---

## 9. Health Check

Vérifier l'état du service.

### Endpoint
```
GET /indexation/health
```

### Réponse (200 OK)
```json
{
  "status": "healthy",
  "service": "Batch Indexation Service",
  "qdrant": {
    "connected": true,
    "collection": "products_v2"
  },
  "vectors": {
    "text_vector": "512d CLIP",
    "image_vector": "512d CLIP"
  }
}
```

---

## 10. Structure des Données

### ProductToIndex (pour indexation)

```typescript
interface ProductToIndex {
  id: string;                    // Requis - ID unique
  title: string;                 // Requis - Titre du produit
  slug: string;                  // Requis - Slug URL-friendly
  price: number;                 // Requis - Prix
  description?: string;          // Description longue
  shortDescription?: string;     // Description courte
  salePrice?: number;            // Prix soldé
  currency?: string;             // Devise (défaut: "XOF")
  category?: {
    id: string;
    name: string;
    slug: string;
  };
  provider?: {
    id: string;
    storeName?: string;
  };
  images?: Array<{
    url: string;
    altText?: string;
    isPrimary?: boolean;
  }>;
  tags?: string[];
  attributes?: Array<{
    name: string;
    value: string;
  }>;
  seoTitle?: string;
  seoDescription?: string;
  seoKeywords?: string[];
  metadata?: object;
}
```

### SearchResult (résultat de recherche)

```typescript
interface SearchResult {
  id: string;                    // ID du produit
  score: number;                 // Score de similarité (0-1)
  metadata: {
    title: string;
    description?: string;
    price: number;
    sale_price?: number;
    currency: string;
    category_name?: string;
    provider_name?: string;
    image_url?: string;
    tags?: string[];
    has_text_embedding: boolean;
    has_image_embedding: boolean;
  };
}
```

---



---

## ⚠️ Codes d'Erreur

| Code | Description |
|------|-------------|
| 200 | Succès |
| 202 | Accepté (async) |
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Accès refusé |
| 404 | Non trouvé |
| 422 | Erreur de validation |
| 500 | Erreur serveur |

---

## 📝 Notes Importantes

1. **Images**: L'URL de l'image principale est utilisée pour générer `image_vector`
2. **Texte**: Le titre, description, tags et attributs sont combinés pour `text_vector`
3. **Limite Batch**: Max 500 produits par batch async, 50 pour sync
4. **Score**: Plus le score est proche de 1, plus le résultat est pertinent
5. **CORS**: Le serveur accepte les requêtes cross-origin

---

## 📞 Support

- **Base URL**: `http://20.238.104.13:8000`
- **Documentation Swagger**: `http://20.238.104.13:8000/docs`
- **Collection Qdrant**: `products_v2`

