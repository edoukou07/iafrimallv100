# 🔍 Guide Complet: Comment Fonctionne la Recherche de Similarité

## 📚 Vue d'Ensemble

La recherche de similarité dans ce projet combine:
- **CLIP (Contrastive Language-Image Pre-training)** pour les embeddings
- **Qdrant** pour la recherche vectorielle ultra-rapide
- **FastAPI** pour l'API backend
- **Django** pour l'interface web

---

## 🏗️ Architecture Complète

```
┌─────────────────────────────────────────────────────────────┐
│                    Utilisateur (Navigateur)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │   Django Frontend     │
         │  /search/text/        │
         │  /search/image/       │
         └───────────┬───────────┘
                     │
                     │ HTTP POST
                     │
         ┌───────────▼──────────────────┐
         │   FastAPI Backend             │
         │  POST /api/v1/search          │
         │  POST /api/v1/search-image    │
         └───────────┬──────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
    ┌───▼─────┐           ┌──────▼──────┐
    │  CLIP   │           │  Qdrant DB  │
    │ Model   │           │  (Vectors)  │
    │(512D)   │           └─────────────┘
    └─────────┘
```

---

## 🔤 1. RECHERCHE TEXTUELLE

### Flux Complet:

```
1. UTILISATEUR
   └─> Tape une requête: "T-shirt bleu coton"
   
2. DJANGO (TextSimilaritySearchView)
   └─> POST /search/text/
   └─> Extrait: query="T-shirt bleu coton", limit=10
   
3. FASTAPI
   POST /api/v1/search
   {
       "query": "T-shirt bleu coton",
       "limit": 10
   }
   
4. CLIP Text Embedding
   ┌─────────────────────────────────┐
   │ "T-shirt bleu coton"            │
   │        ↓ CLIPProcessor          │
   │        ↓ Tokenization           │
   │        ↓ CLIP Text Encoder      │
   │ Embedding 512D: [0.23, -0.45, ...]
   └─────────────────────────────────┘
   
5. QDRANT Search
   ├─ Prend: query_vector (512D)
   ├─ Calcul: Cosine Similarity avec tous les produits
   ├─ Tri: Par score (descending)
   └─ Retour: Top 10 résultats
   
6. RÉSULTATS
   [
       {
           "score": 0.95,
           "payload": {
               "product_id": "uuid-123",
               "name": "T-shirt Coton Bleu",
               "image_url": "...",
               "price": 29.99
           }
       },
       ...
   ]
```

### Code Python:

```python
# FastAPI: POST /api/v1/search
@router.post("/search")
async def search(request: SearchRequest):
    # 1. Valider requête
    if not request.query:
        raise HTTPException(status_code=400, detail="Query required")
    
    # 2. Générer embedding CLIP pour le texte
    embedding = embedding_service.embed_text(request.query)
    # Result: [0.23, -0.45, 0.67, ...] (512 dimensions)
    
    # 3. Chercher dans Qdrant
    search_results = qdrant_service.search(
        query_vector=embedding,
        limit=request.limit
    )
    
    # 4. Retourner résultats
    return SearchResponse(
        query=request.query,
        results=search_results,
        count=len(search_results)
    )
```

---

## 🖼️ 2. RECHERCHE PAR IMAGE

### Flux Complet:

```
1. UTILISATEUR
   └─> Upload une image: shirt.jpg
   
2. DJANGO (ImageSimilaritySearchView)
   └─> POST /search/image/
   └─> Envoie FormData avec fichier image
   
3. FASTAPI
   POST /api/v1/search-image
   Body: FormData(file=shirt.jpg)
   Params: ?limit=10
   
4. CLIP Image Embedding
   ┌──────────────────────────┐
   │ shirt.jpg (JPEG file)    │
   │        ↓ PIL.Image       │
   │ Resize to 224x224        │
   │        ↓ CLIPProcessor   │
   │ Normalize pixels         │
   │        ↓ CLIP Image      │
   │        Encoder           │
   │ Embedding 512D:          │
   │ [0.12, -0.34, ...]      │
   └──────────────────────────┘
   
5. QDRANT Search
   (Même que recherche textuelle)
   
6. RÉSULTATS
   Produits visuellement similaires avec scores
```

### Code Python:

```python
# FastAPI: POST /api/v1/search-image
@router.post("/search-image")
async def search_by_image(file: UploadFile = File(...), limit: int = Query(10)):
    # 1. Valider mime type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be image")
    
    # 2. Lire fichier
    image_data = await file.read()
    
    # 3. Générer embedding CLIP pour l'image
    embedding = image_embedding_service.embed_image(image_data)
    # Result: [0.12, -0.34, 0.56, ...] (512 dimensions)
    
    # 4. Chercher dans Qdrant
    search_results = qdrant_service.search(
        query_vector=embedding,
        limit=limit
    )
    
    # 5. Retourner résultats
    return {
        "query_image": file.filename,
        "results": search_results,
        "count": len(search_results)
    }
```

---

## 🧠 3. CLIP MODEL (Cœur du Système)

### Qu'est-ce que CLIP?

**CLIP = Contrastive Language-Image Pre-training**

```
┌──────────────────┐        ┌──────────────────┐
│  Image Encoder   │        │  Text Encoder    │
│  (Vision)        │        │  (Language)      │
│                  │        │                  │
│  Input: Image    │        │  Input: Text     │
│  Output: 512D    │        │  Output: 512D    │
│  Vector          │        │  Vector          │
└────────┬─────────┘        └────────┬─────────┘
         │                           │
         └───────────┬───────────────┘
                     │
            Embeddings dans le même espace!
            
        Similarité(Image, Text) = 
            Cosine(Image_Embedding, Text_Embedding)
```

### Avantages:

✅ **Multimodal**: Texte et image dans le même espace vectoriel  
✅ **Rapide**: 512 dimensions (compact, pas lourd)  
✅ **Pré-entraîné**: Sur des millions de paires image-texte  
✅ **Performant**: ~95% accuracy sur benchmarks

### Initialisation:

```python
# app/services/embedding_service.py
from transformers import CLIPProcessor, CLIPModel

class EmbeddingService:
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        self.model = CLIPModel.from_pretrained(model_name)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.model.eval()
```

---

## 📊 4. QDRANT (Base de Données Vectorielle)

### Architecture:

```
┌──────────────────────────────────────────┐
│         Qdrant Collection                │
│  (ex: "products_embeddings")             │
└──────────────┬───────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼──┐  ┌───▼──┐  ┌───▼──┐
│Point │  │Point │  │Point │  ...
│  ID: 1  │  ID: 2  │  ID: 3  │
│Vector  │Vector  │Vector  │
│Payload │Payload │Payload │
└────────┘  └────────┘  └────────┘

Payload = {
    "product_id": "uuid-123",
    "name": "T-shirt Bleu",
    "category": "clothing",
    "price": 29.99,
    "image_url": "..."
}
```

### Initialisation:

```python
# app/services/qdrant_service.py
class QdrantService:
    def __init__(self, host="qdrant", port=6333, collection_name="products"):
        self.client = QdrantClient(
            host=host,
            port=port,
            prefer_grpc=False,  # Use HTTP
            https=False
        )
        # Create collection if not exists
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=512,  # CLIP embedding dimension
                distance=Distance.COSINE  # Cosine similarity
            )
        )
```

### Stockage d'un Produit:

```python
def upsert_product(self, product_id: str, embedding: List[float], metadata: Dict):
    point = PointStruct(
        id=hash(product_id) % (10 ** 8),  # Convert UUID to int
        vector=embedding,                   # 512-dimensional vector
        payload={                           # Metadata
            "product_id": product_id,
            "name": metadata["name"],
            "image_url": metadata["image_url"],
            ...
        }
    )
    self.client.upsert(collection_name="products", points=[point])
```

### Recherche:

```python
def search(self, embedding: List[float], top_k: int = 10):
    results = self.client.search(
        collection_name="products",
        query_vector=embedding,  # 512D query vector
        limit=top_k,
        with_payload=True  # Include metadata
    )
    
    return [{
        "score": result.score,      # 0.0 to 1.0 (cosine similarity)
        "payload": result.payload   # Product metadata
    } for result in results]
```

---

## 🔄 5. PROCESSUS COMPLET D'INDEXATION

### Quand un Produit est Ajouté:

```
1. Upload Produit (Django)
   └─> Name, Description, Image
   
2. FastAPI (POST /api/v1/index-product)
   ├─ Génère CLIP embedding pour image
   ├─ Stocke dans Qdrant
   └─ Met à jour status: "indexed"
   
3. Résultat
   └─> Produit maintenant searchable!
```

### Code FastAPI:

```python
@router.post("/index-product")
async def index_product(
    product_id: str = Form(...),
    name: str = Form(...),
    image_file: UploadFile = File(...),
    ...
):
    # 1. Lire l'image
    image_data = await image_file.read()
    
    # 2. Générer embedding
    embedding = image_embedding_service.embed_image(image_data)
    
    # 3. Stocker dans Qdrant
    qdrant_service.upsert_product(
        product_id=product_id,
        embedding=embedding,
        metadata={
            "name": name,
            "image_url": image_url,
            ...
        }
    )
    
    # 4. Retourner confirmation
    return {"status": "indexed", "product_id": product_id}
```

---

## 📈 6. SIMILARITÉ - EXPLICATION MATHÉMATIQUE

### Cosine Similarity:

```
Similarity = Dot Product / (Norm A × Norm B)

Exemple avec 2 vecteurs 3D:
A = [0.5, 0.3, 0.2]  (Embedding du T-shirt bleu)
B = [0.4, 0.4, 0.1]  (Embedding du T-shirt bleu clair)

Dot Product = 0.5×0.4 + 0.3×0.4 + 0.2×0.1 = 0.3
Norm A = √(0.5² + 0.3² + 0.2²) = 0.62
Norm B = √(0.4² + 0.4² + 0.1²) = 0.58

Similarity = 0.3 / (0.62 × 0.58) = 0.834 → 83.4%

Résultat:
- 1.0 = Identique
- 0.8+ = Très similaire
- 0.5  = Modérément similaire
- 0.0  = Complètement différent
```

---

## 🚀 7. PERFORMANCE ET OPTIMISATIONS

### Temps Typiques:

```
Tâche                              Temps
────────────────────────────────────────
Embedding Text (CLIP)              ~50ms
Embedding Image (CLIP)             ~100ms
Qdrant Search (10 résultats)       ~5ms
─────────────────────────────────  ─────
Temps Total (Text Search)          ~60ms
Temps Total (Image Search)         ~110ms
```

### Optimisations Appliquées:

1. **Model Quantization**: CLIP optimisé pour CPU/GPU
2. **Batch Processing**: Traiter plusieurs embeddings
3. **Caching**: Résultats de recherche cachés
4. **Index Optimisation**: Qdrant utilise HNSW pour recherche rapide

---

## 🔗 8. INTÉGRATION DJANGO

### Flux Django → FastAPI:

```python
# search/similarity_views.py

class TextSimilaritySearchView(View):
    def post(self, request):
        query = request.POST.get('query')
        limit = int(request.POST.get('limit', 10))
        
        # Appel FastAPI
        response = requests.post(
            "http://localhost:8000/api/v1/search",
            json={"query": query, "limit": limit},
            timeout=30
        )
        
        results = response.json().get('results', [])
        
        # Enrichir avec données Django
        enriched = []
        for item in results:
            product_id = item['payload']['product_id']
            try:
                product = Product.objects.get(id=product_id)
                enriched.append({
                    'product': product,
                    'score': item['score'],
                    'similarity': item['score'] * 100
                })
            except Product.DoesNotExist:
                pass
        
        return render(request, 'similarity_results.html', {
            'results': enriched,
            'count': len(enriched)
        })
```

---

## 📊 9. STRUCTURE DE DONNÉES

### Request (Django → FastAPI):

```json
{
    "query": "T-shirt bleu coton",
    "limit": 10
}
```

### Response (FastAPI → Django):

```json
{
    "query": "T-shirt bleu coton",
    "results": [
        {
            "score": 0.95,
            "payload": {
                "product_id": "uuid-123",
                "name": "T-shirt Coton Bleu",
                "description": "Confortable et durable",
                "image_url": "/media/images/tshirt.jpg",
                "category": "clothing",
                "price": 29.99
            }
        },
        {
            "score": 0.87,
            "payload": {
                "product_id": "uuid-456",
                ...
            }
        }
    ],
    "count": 2
}
```

---

## 🎯 10. CAS D'USAGE

### Text Search:
✅ "T-shirt bleu coton pas cher"  
✅ "Chaussures de sport femme"  
✅ "Robe soirée noire"

### Image Search:
✅ Upload photo de T-shirt → Trouver similaires  
✅ Upload photo de chaussures → Trouver alternatives  
✅ Upload photo de produit → Trouver marque similaire

---

## 🔧 11. CONFIGURATION

### Environment Variables:

```bash
# .env
CLIP_MODEL="openai/clip-vit-base-patch32"  # Model CLIP
QDRANT_HOST="qdrant"                       # Docker service name
QDRANT_PORT=6333                           # Qdrant port
COLLECTION_NAME="products"                 # DB collection
IMAGE_SEARCH_API_URL="http://localhost:8000"  # FastAPI URL
```

### Docker Compose:

```yaml
services:
  fastapi:
    build: .
    ports:
      - "8000:8000"
    environment:
      - QDRANT_HOST=qdrant
      - CLIP_MODEL=openai/clip-vit-base-patch32
    depends_on:
      - qdrant
  
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
```

---

## 📚 12. RESSOURCES

- [CLIP Paper](https://arxiv.org/abs/2103.14030)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [HuggingFace CLIP](https://huggingface.co/openai/clip-vit-base-patch32)
- [FastAPI](https://fastapi.tiangolo.com/)

---

**Résumé**: La recherche de similarité = **Text/Image → CLIP Embedding (512D) → Qdrant Search → Résultats Triés** 🚀
