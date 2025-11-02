# Image Search API - CLIP + Qdrant

## Structure du Projet

```
image-search-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application FastAPI principale
│   ├── config.py               # Configuration de l'application
│   ├── dependencies.py         # Dépendances et initialisation des services
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # Routes API
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Schémas Pydantic
│   ├── services/
│   │   ├── __init__.py
│   │   ├── embedding_service.py    # Service CLIP pour embeddings
│   │   ├── qdrant_service.py       # Service Qdrant pour recherche vectorielle
│   │   ├── cache_service.py        # Service Redis pour cache
│   │   └── search_service.py       # Service de recherche orchestrateur
│   └── utils/
│       ├── __init__.py
│       └── logger.py           # Configuration du logger
├── tests/
│   └── test_api.py             # Tests API
├── docker-compose.yml          # Configuration Docker Compose
├── Dockerfile                  # Configuration Docker
├── requirements.txt            # Dépendances Python
├── .env.example                # Variables d'environnement exemple
└── README.md                   # Documentation
```

## Services

### 1. EmbeddingService
- Gère le modèle CLIP pour générer des embeddings
- Supporte les images (URL ou fichier local) et le texte
- Normalise les embeddings pour la recherche cosinus

### 2. QdrantService
- Gère la base de données vectorielle Qdrant
- Upsert de produits avec embeddings
- Recherche vectorielle avec filtres
- Gestion des collections

### 3. CacheService
- Gère Redis pour le cache des résultats
- TTL configurable
- Génération automatique de clés de cache

### 4. SearchService
- Orchestre les trois services précédents
- Implémente la logique métier
- Caching automatique des résultats
- Filtrage par catégorie et prix

## 🛠️ Prochaines Étapes

1. **Démarrer les services** :
   ```bash
   docker-compose up -d
   ```

2. **Vérifier la santé** :
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

3. **Indexer des produits** :
   ```bash
   curl -X POST http://localhost:8000/api/v1/index-product \
     -H "Content-Type: application/json" \
     -d '{
       "id": "prod_001",
       "name": "Example Product",
       "description": "A great product",
       "image_url": "https://example.com/image.jpg",
       "category": "electronics",
       "price": 99.99
     }'
   ```

4. **Effectuer une recherche** :
   ```bash
   curl -X POST http://localhost:8000/api/v1/search \
     -H "Content-Type: application/json" \
     -d '{
       "image_url": "https://example.com/search.jpg",
       "top_k": 10
     }'
   ```

5. **Accéder à la documentation interactive** :
   Ouvrir http://localhost:8000/docs dans un navigateur

## 📊 Configuration Recommandée pour Production

```env
ENVIRONMENT=production
DEBUG=False
MODEL_NAME=openai/CLIP-ViT-L-14
EMBEDDING_DIM=768
TOP_K=20
CACHE_TTL=7200
```

## 🔐 Sécurité

- Changez QDRANT_API_KEY en production
- Utilisez REDIS_PASSWORD pour Redis
- Validez les URLs d'images
- Limitez les requêtes (rate limiting)

Besoin d'aide ? Consultez README.md pour des exemples complets.
