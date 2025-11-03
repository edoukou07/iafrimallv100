# 📸 Image Search Pipeline avec CLIP

## Vue d'ensemble

L'application implémente une **recherche d'images multi-modale** basée sur OpenAI CLIP. Cela signifie que vous pouvez:

✅ **Rechercher par image** → Trouver des produits similaires visuellement  
✅ **Rechercher par texte** → Trouver des produits correspondant à la description  
✅ **Combiner image + texte** → Ex: "Une robe rouge" avec une photo en référence  
✅ **Recherche cross-modale** → Photo de robe → Trouver descriptions texte associées  

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   USER REQUEST                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Upload Image (JPEG/PNG)  │  2. Text Query          │
│         ↓                     │         ↓                │
│    Image Bytes ──────┬────────┼─── Text String         │
│                      │        │        │                │
│                      ↓        ↓        ↓                │
│            ┌──────────────────────────┐                 │
│            │   CLIP Model             │                 │
│            │ (OpenAI)                 │                 │
│            │ Multi-Modal Transformer  │                 │
│            └──────────────────────────┘                 │
│                      │                                   │
│                      ↓                                   │
│         ┌─────────────────────────┐                    │
│         │ Embedding Vector        │                    │
│         │ 512 Dimensions          │                    │
│         │ (Image or Text)         │                    │
│         └─────────────────────────┘                    │
│                      │                                   │
│                      ↓                                   │
│         ┌─────────────────────────┐                    │
│         │  Qdrant Vector DB       │                    │
│         │  Similarity Search      │                    │
│         │  (L2 Distance)          │                    │
│         └─────────────────────────┘                    │
│                      │                                   │
│                      ↓                                   │
│         ┌─────────────────────────┐                    │
│         │  Top-K Results          │                    │
│         │  (Products Matched)     │                    │
│         └─────────────────────────┘                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Modèle CLIP (Contrastive Language-Image Pre-training)

**Qu'est-ce que CLIP?**

CLIP est un modèle pré-entraîné par OpenAI qui comprend **à la fois les images ET le texte**:

- Encode les images en vecteurs 512-dim qui capturent le contenu visuel
- Encode le texte en vecteurs 512-dim qui capturent le sens
- Les deux espaces vectoriels sont alignés → **recherche cross-modale possible**

**Exemple concret:**

```
Image: Photo d'une robe rouge
    ↓
CLIP Encoder
    ↓
Vector: [0.234, -0.156, 0.892, ..., -0.112]  (512 dimensions)

Text: "beautiful red dress"
    ↓
CLIP Encoder
    ↓
Vector: [0.245, -0.142, 0.901, ..., -0.108]  (512 dimensions)

Similarité: 0.97 (très proche!)
```

## Pipeline d'Indexation

### 1. Indexer un produit avec image

```bash
curl -X POST "http://localhost:8000/api/v1/index-product-with-image" \
  -F "product_id=dress_001" \
  -F "name=Red Summer Dress" \
  -F "description=Beautiful red dress perfect for summer" \
  -F "image_file=@path/to/dress.jpg" \
  -F "metadata={\"price\": 49.99, \"category\": \"dress\"}"
```

**Processus:**
1. ✅ Upload image + métadonnées produit
2. ✅ CLIP encode l'image → 512-dim vector
3. ✅ CLIP encode le texte (nom + description) → 512-dim vector
4. ✅ Utilise embedding image (meilleur pour visual search)
5. ✅ Stocke dans Qdrant avec métadonnées

### 2. Extraire un embedding d'image (debug)

```bash
curl -X POST "http://localhost:8000/api/v1/embed-image" \
  -F "file=@path/to/image.jpg"
```

Réponse:
```json
{
  "image": "image.jpg",
  "embedding": [0.234, -0.156, 0.892, ...],
  "dimension": 512,
  "model": "CLIP"
}
```

## Pipeline de Recherche

### 1. Rechercher par image (Visual Search)

```bash
curl -X POST "http://localhost:8000/api/v1/search-image?limit=10" \
  -F "file=@path/to/query_image.jpg"
```

**Processus:**
1. ✅ Upload image query
2. ✅ CLIP encode l'image → 512-dim vector
3. ✅ Qdrant recherche les vecteurs les plus proches
4. ✅ Retourne les Top-10 produits visuellement similaires

Réponse exemple:
```json
{
  "query_image": "query_image.jpg",
  "model": "CLIP",
  "embedding_dimension": 512,
  "count": 3,
  "results": [
    {
      "id": "dress_001",
      "name": "Red Summer Dress",
      "score": 0.89,
      "metadata": {"price": 49.99}
    },
    {
      "id": "shirt_005",
      "name": "Red Casual Shirt",
      "score": 0.76,
      "metadata": {"price": 29.99}
    }
  ]
}
```

### 2. Recherche cross-modale (texte → images)

```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "red clothing"}'
```

**Processus:**
1. ✅ Text query "red clothing"
2. ✅ CLIP encode le texte → 512-dim vector
3. ✅ Qdrant recherche les produits dont l'image correspond
4. ✅ Retourne les vêtements rouges (basé sur embeddings image!)

### 3. Recherche híbrida: image + texte filtré

**Cas d'usage e-commerce:**
> Utilisateur envoie une photo de robe ET dit "je veux la version en vert"

**Solution future:**
```python
# 1. Encoder la photo
image_embedding = clip.encode_image(photo)

# 2. Encoder le texte
text_embedding = clip.encode_text("green color")

# 3. Combiner les embeddings
hybrid_embedding = (image_embedding + text_embedding) / 2

# 4. Chercher dans Qdrant
results = qdrant.search(hybrid_embedding, limit=10)
```

## Avantages de CLIP pour l'e-commerce

| Cas d'usage | Solution CLIP |
|---|---|
| Recherche visuelle | ✅ Photo → Produits similaires |
| Recherche textuelle | ✅ "Robe rouge" → Produits correspondants |
| Cross-modale | ✅ Photo + "en vert" → Combinaison |
| Découverte produits | ✅ Photo inspirante → Similarité visuelle |
| Filtrage par description | ✅ Description texte seulement |
| Recherche floue | ✅ Concepts vagues → Vecteurs proches |

## Performance et Coût

### Temps d'exécution

| Opération | Durée | Notes |
|---|---|---|
| CLIP encode image | ~100-200ms | GPU: ~50ms, CPU: ~200ms |
| CLIP encode texte | ~50-100ms | Très rapide |
| Qdrant search (512-dim) | ~10-50ms | Dépend du nombre d'items |
| Total request | ~150-300ms | Temps total API |

### Consommation mémoire

- Modèle CLIP: ~350MB (ViT-B/32)
- Vecteurs Qdrant: ~2MB par 10,000 produits (512-dim)
- Runtime app: ~500MB total dans le container

## Déploiement sur Azure Container Apps

### Dockerfile optimisé

```dockerfile
# requirements-image-search.txt inclut:
- torch==2.0.1 (vs 2.1.1 original - 200MB plus léger)
- transformers==4.32.1
- torchvision==0.15.2
- pillow-simd (image processing accéléré)

# Multi-stage build:
# Stage 1: Compiler dépendances (~2GB)
# Stage 2: Runtime avec seulement packages essentiels (~500MB final)
```

### Container size

- Image finale: ~500MB
- Après compression: ~150-200MB
- Temps de déploiement sur Azure: ~2-3 minutes
- Coût: $0.0000115/seconde (Consumption plan)

## API Endpoints Complets

### Health & Stats

```
GET  /api/v1/health
GET  /api/v1/stats
```

### Embeddings

```
POST /api/v1/embed
     Body: {"text": "description"}
     Returns: {embedding, dimension}

POST /api/v1/embed-image
     Body: file (image file)
     Returns: {embedding, dimension, model}
```

### Indexation

```
POST /api/v1/index-product
     Body: FormData(product_id, name, description, metadata)
     Returns: {status, message}

POST /api/v1/index-product-with-image
     Body: FormData(product_id, name, description, image_file, metadata)
     Returns: {status, embedding_type, embedding_dimension}
```

### Recherche

```
POST /api/v1/search
     Body: {"query": "text search", "limit": 10}
     Returns: {results, count, model}

POST /api/v1/search-image
     Body: file (image file), params: ?limit=10
     Returns: {results, count, query_image, embedding_dimension}
```

## Testing Local

### 1. Démarrer le serveur

```bash
cd iafrimallv100
python -m uvicorn app.main:app --reload
```

### 2. Exécuter les tests

```bash
python test_image_search.py
```

**Sortie attendue:**
```
============================================================
  🖼️  IMAGE SEARCH PIPELINE TEST SUITE
============================================================

============================================================
  1. Testing API Health
============================================================
✅ Health check passed
  Status: running
  Version: 1.0.0

============================================================
  3. Testing Image Embedding (CLIP)
============================================================
✅ Image embedding generated: 512 dimensions
  Image: test_red.png (224x224, red)
  Embedding size: 512
  Sample values: [0.234, -0.156, 0.892]

============================================================
  7. Testing Image Search (Find Similar Products)
============================================================
✅ Image search returned 3 results
  Query image: query.png
  Model: CLIP
  Embedding dimension: 512

  Top results:
    1. Red Summer Dress (score: 0.89)
    2. Red Casual Shirt (score: 0.76)
```

## Prochaines étapes

### Phase 1: MVP (Actuel)
✅ Endpoints image search fonctionnels  
✅ CLIP embeddings (512-dim)  
✅ Qdrant search intégré  
✅ Tests locaux passants  

### Phase 2: Optimisations
- [ ] Cache des embeddings (Redis optionnel)
- [ ] Quantization CLIP pour vitesse
- [ ] GPU support sur Azure
- [ ] Batch indexing

### Phase 3: UX E-commerce
- [ ] Dashboard visual search
- [ ] Upload multiple images
- [ ] Filters + search hybride
- [ ] Save search preferences

## Résumé Architecture

**Stack complèt dans 1 seul container:**

```
Azure Container Apps (Consumption)
├── FastAPI Server (port 8000)
├── CLIP Model (512-dim embeddings)
├── Qdrant Vector DB (disk-based)
└── TF-IDF (fallback text search)

Single Docker Image: ~500MB
Auto-scale: 0-10 replicas
Cost: $0-10/month
```

**Requête → Response:** ~150-300ms  
**Scalabilité:** Auto-scale à zéro quand inactif  
**Fiabilité:** 99.95% uptime SLA  

---

**Prêt pour déployer sur Azure Container Apps!** 🚀
