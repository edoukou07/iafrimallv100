╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║            🏗️  FONCTIONNEMENT COMPLET DE L'APPLICATION                         ║
║              Image Search API - CLIP + Qdrant + Redis                         ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

📚 TABLE DES MATIÈRES
════════════════════════════════════════════════════════════════════════════════

1. Vue d'ensemble générale
2. Architecture en couches
3. Flux de données pour recherche
4. Services individuels
5. Technologies utilisées
6. Exemple d'exécution complet

════════════════════════════════════════════════════════════════════════════════

1️⃣ VUE D'ENSEMBLE GÉNÉRALE
════════════════════════════════════════════════════════════════════════════════

L'application permet de:
✓ Rechercher des produits par IMAGE
✓ Rechercher des produits par TEXTE
✓ Indexer des produits pour recherche future
✓ Filtrer par catégorie et prix
✓ Obtenir les produits les plus similaires

    CLIENT (Navigateur ou API)
            ↓
    FASTAPI SERVER (Port 8000)
            ↓
    ┌───────────────────────────────┐
    │   SERVICES MÉTIER             │
    ├───────────────────────────────┤
    │ • CLIP Embeddings             │
    │ • Qdrant Vector Search        │
    │ • Redis Caching               │
    │ • Search Orchestration        │
    └───────────────────────────────┘
            ↓
    BASE DE DONNÉES / SERVICES
    • Qdrant (vecteurs)
    • Redis (cache)

════════════════════════════════════════════════════════════════════════════════

2️⃣ ARCHITECTURE EN COUCHES
════════════════════════════════════════════════════════════════════════════════

COUCHE 1: API (FastAPI)
─────────────────────────
Fichier: app/api/routes.py

Endpoints:
  POST /api/v1/search
       ↓
       Reçoit: image_url ou text_query
       Retourne: Liste de produits similaires
       
  POST /api/v1/index-product
       ↓
       Reçoit: Données produit
       Action: Indexe le produit
       
  GET /api/v1/health
       ↓
       Vérifie l'état des services
       
  GET /api/v1/collections
       ↓
       Retourne les stats de la collection


COUCHE 2: SERVICES (Métier)
────────────────────────────
Fichiers: app/services/*.py

SearchService (orchestrateur principal)
├── search_by_image_url()
│   └── Coordonne les autres services
├── search_by_text()
│   └── Idem mais pour texte
├── index_product()
│   └── Index un produit
└── index_batch()
    └── Index plusieurs produits

EmbeddingService (IA)
├── embed_image()
│   └── Génère vecteur depuis image
├── embed_text()
│   └── Génère vecteur depuis texte
└── embed_image_from_url()
    └── Télécharge et traite l'image

QdrantService (Base de données)
├── upsert_product()
│   └── Ajoute/met à jour produit
├── search()
│   └── Recherche similaires
├── delete_product()
│   └── Supprime produit
└── health_check()
    └── Vérifie connexion

CacheService (Redis)
├── get()
│   └── Récupère du cache
├── set()
│   └── Stocke en cache
├── delete()
│   └── Supprime du cache
└── health_check()
    └── Vérifie connexion


COUCHE 3: CONFIGURATION
───────────────────────
Fichiers: app/config.py, app/dependencies.py

Config: Settings Pydantic
├── Chargement variables .env
├── Validation settings
└── Paramètres par défaut

Dependencies: Injection dépendances
├── get_search_service()
│   └── Retourne instance SearchService
├── get_embedding_service()
│   └── Retourne instance EmbeddingService
├── get_qdrant_service()
│   └── Retourne instance QdrantService
└── get_cache_service()
    └── Retourne instance CacheService


COUCHE 4: MODÈLES DE DONNÉES
─────────────────────────────
Fichiers: app/models/schemas.py

SearchRequest
├── image_url
├── text_query
├── top_k
├── category_filter
├── price_min
└── price_max

SearchResult
├── product_id
├── name
├── similarity_score
├── price
└── ...

SearchResponse
├── query_type
├── results[]
└── execution_time_ms

════════════════════════════════════════════════════════════════════════════════

3️⃣ FLUX DE DONNÉES - RECHERCHE PAR IMAGE
════════════════════════════════════════════════════════════════════════════════

UTILISATEUR ENVOIE:
┌─────────────────────────────────────────┐
│ POST /api/v1/search                     │
│ {                                       │
│   "image_url": "https://..../image.jpg",│
│   "top_k": 10,                          │
│   "category_filter": "clothing"         │
│ }                                       │
└─────────────────────────────────────────┘
         ↓
ÉTAPE 1: API reçoit la requête
         ↓
ÉTAPE 2: SearchService.search_by_image_url()
         ↓
ÉTAPE 3: Vérifier le cache Redis
         ├─→ ✅ TROUVÉ? Retourner le résultat en cache
         └─→ ❌ NON? Continuer...
         ↓
ÉTAPE 4: EmbeddingService.embed_image_from_url()
         ├─→ Télécharger l'image depuis URL
         ├─→ Redimensionner et normaliser
         ├─→ Passer au modèle CLIP
         ├─→ Traiter avec GPU/CPU
         └─→ Obtenir vecteur 512-dimensional
         ↓
ÉTAPE 5: QdrantService.search()
         ├─→ Envoyer vecteur à Qdrant
         ├─→ Recherche vectorielle (distance cosinus)
         ├─→ Appliquer filtres (catégorie, prix)
         └─→ Récupérer les top 10 résultats similaires
         ↓
ÉTAPE 6: SearchService._filter_and_format_results()
         ├─→ Filtrer par catégorie si demandé
         ├─→ Filtrer par prix si demandé
         ├─→ Formater les résultats
         └─→ Ajouter scores de similitude
         ↓
ÉTAPE 7: CacheService.set()
         ├─→ Stocker le résultat en Redis
         └─→ TTL par défaut: 3600 secondes (1 heure)
         ↓
ÉTAPE 8: Retourner la réponse
         ↓
RÉPONSE JSON:
┌─────────────────────────────────────────────┐
│ {                                           │
│   "query_type": "image",                    │
│   "top_k": 10,                              │
│   "total_results": 5,                       │
│   "results": [                              │
│     {                                       │
│       "product_id": "prod_001",             │
│       "name": "Red Shirt",                  │
│       "similarity_score": 0.95,             │
│       "price": 29.99,                       │
│       "category": "clothing"                │
│     },                                      │
│     ...                                     │
│   ],                                        │
│   "execution_time_ms": 245.5                │
│ }                                           │
└─────────────────────────────────────────────┘

════════════════════════════════════════════════════════════════════════════════

4️⃣ SERVICES INDIVIDUELS - EXPLICATION DÉTAILLÉE
════════════════════════════════════════════════════════════════════════════════

🤖 SERVICE 1: EmbeddingService (CLIP)
─────────────────────────────────────

QU'EST-CE QUE C'EST?
- Modèle IA préentraîné par OpenAI
- Comprend les images ET le texte
- Convertit en vecteurs numériques
- Les images/textes similaires ont des vecteurs proches

FONCTIONNEMENT:

Image Input:
  ↓
┌─────────────────────────┐
│ PIL (Charger image)     │
│ • Télécharger depuis URL│
│ • Convertir en RGB      │
│ • Redimensionner        │
└─────────────────────────┘
  ↓
┌─────────────────────────┐
│ CLIP Processor          │
│ • Normaliser pixel      │
│ • Préparer pour modèle  │
└─────────────────────────┘
  ↓
┌─────────────────────────┐
│ CLIP Model (GPU/CPU)    │
│ • Traiter image         │
│ • Extraire features     │
│ • 2048 → 512 dims      │
└─────────────────────────┘
  ↓
Normalization L2
  ↓
OUTPUT: Vecteur [0.12, -0.34, ..., 0.89]  (512 nombres)


EXEMPLE AVEC TEXTE:

"red cotton shirt"
  ↓
┌──────────────────────────┐
│ CLIP Tokenizer           │
│ • Convertir texte en IDs │
│ • Ajouter padding        │
└──────────────────────────┘
  ↓
┌──────────────────────────┐
│ CLIP Model Text Encoder  │
│ • Traiter tokens         │
│ • Extraire sémantique    │
│ • 2048 → 512 dims        │
└──────────────────────────┘
  ↓
Normalization L2
  ↓
OUTPUT: Vecteur similaire au premier!

ASTUCE: Un vecteur d'image et un vecteur de texte
        similaires auront une distance cosinus proche!


📦 SERVICE 2: QdrantService (Base Vectorielle)
──────────────────────────────────────────────

QU'EST-CE QUE C'EST?
- Base de données pour vecteurs (embeddings)
- Optimisée pour recherche rapide par similitude
- Utilise distance cosinus (angle entre vecteurs)

STRUCTURE:

Collection: "products"
├── Vector1 (prod_001) → [0.12, -0.34, ...]
├── Vector2 (prod_002) → [0.11, -0.35, ...]
├── Vector3 (prod_003) → [0.45, 0.67, ...]
└── Vector4 (prod_004) → [0.13, -0.33, ...]

RECHERCHE:

Query Vector: [0.12, -0.34, ...] (nouvelle image)
  ↓
Qdrant calcule distance avec tous les vecteurs
  ↓
Distance = 1 - (QueryVector · StoredVector) / (||Query|| * ||Stored||)
  ↓
Résultats triés par similarité:
  prod_001: 0.98 (très similaire!)
  prod_002: 0.95 (similaire)
  prod_004: 0.92 (un peu similaire)
  prod_003: 0.25 (pas similaire)

OPTIMISATION:
- Index HNSW (Hierarchical Navigable Small World)
- Recherche en O(log n) au lieu de O(n)
- Millions de produits en millisecondes


💾 SERVICE 3: CacheService (Redis)
──────────────────────────────────

QU'EST-CE QUE C'EST?
- Stockage en mémoire ultra-rapide
- Cache des résultats de recherche
- TTL (Time To Live) configurable

FONCTIONNEMENT:

Première recherche "red shirt":
  ↓
  ┌─────────────────────────────┐
  │ Cache MISS                  │
  ├─────────────────────────────┤
  │ 1. Calculer embedding       │
  │ 2. Chercher dans Qdrant     │
  │ 3. Formater résultats       │
  │ 4. Stocker en Redis         │
  └─────────────────────────────┘
  ↓
  Temps: 250ms

Deuxième recherche "red shirt" (1 heure plus tard):
  ↓
  ┌─────────────────────────────┐
  │ Cache HIT ✅                │
  ├─────────────────────────────┤
  │ 1. Récupérer de Redis       │
  │ 2. Retourner directement    │
  └─────────────────────────────┘
  ↓
  Temps: 30ms (8x plus rapide!)

CLÉS DE CACHE:

search:md5("red shirt")     → Résultats texte
search:md5("image_url")     → Résultats image

TTL Défaut: 3600 secondes (1 heure)


🎯 SERVICE 4: SearchService (Orchestrateur)
──────────────────────────────────────────

QU'EST-CE QUE C'EST?
- Combine tous les services
- Logique métier principale
- Gère les filtres et résultats

MÉTHODES PRINCIPALES:

search_by_image_url(image_url, top_k, filters)
├── Vérifier cache
├── Embedding de l'image (EmbeddingService)
├── Recherche (QdrantService)
├── Appliquer filtres
├── Cacher le résultat (CacheService)
└── Retourner réponse

search_by_text(query, top_k, filters)
├── Vérifier cache
├── Embedding du texte (EmbeddingService)
├── Recherche (QdrantService)
├── Appliquer filtres
├── Cacher le résultat (CacheService)
└── Retourner réponse

index_product(product_data)
├── Télécharger et analyser image
├── Générer embedding (EmbeddingService)
├── Sauvegarder en Qdrant (QdrantService)
└── Retourner succès

FILTRAGE:

Top_k = 10 résultats

résultats bruts de Qdrant: [10 produits]
  ↓
Filtrer par catégorie "clothing"?
  → [8 produits]
  ↓
Filtrer par prix min 20?
  → [7 produits]
  ↓
Filtrer par prix max 100?
  → [6 produits]
  ↓
Résultats finaux: 6 produits

════════════════════════════════════════════════════════════════════════════════

5️⃣ TECHNOLOGIES UTILISÉES
════════════════════════════════════════════════════════════════════════════════

FRAMEWORK:
├── FastAPI      - Framework API REST moderne
├── Uvicorn      - Serveur ASGI (async)
└── Pydantic     - Validation données

IA & ML:
├── transformers - Modèles CLIP d'OpenAI
├── torch        - PyTorch (calcul tenseur)
├── torchvision  - Vision utilities
├── PIL/Pillow   - Traitement images
└── numpy        - Calculs numériques

VECTORIAL DATABASE:
└── Qdrant       - Recherche vecteurs haute performance

CACHE:
└── Redis        - Cache en mémoire

INFRASTRUCTURE:
├── Docker       - Containerisation
├── Docker Compose - Orchestration locale
└── Python 3.11+ - Runtime

════════════════════════════════════════════════════════════════════════════════

6️⃣ EXEMPLE D'EXÉCUTION COMPLÈTE
════════════════════════════════════════════════════════════════════════════════

SCÉNARIO: Utilisateur recherche des t-shirts rouges

ÉTAPE 1: Démarrage (docker-compose up -d)
─────────────────────────────────────────
✓ FastAPI démarre sur port 8000
✓ Qdrant se lance sur port 6333
✓ Redis se lance sur port 6379
✓ Modèle CLIP se télécharge (500MB)
⏳ Attendre 1-2 minutes

ÉTAPE 2: Indexation produits
────────────────────────────
POST /api/v1/index-product
{
  "id": "prod_001",
  "name": "Red Cotton T-Shirt",
  "image_url": "https://example.com/red_shirt.jpg",
  "category": "clothing",
  "price": 29.99
}

  ↓
  Service récupère l'image
  ↓
  CLIP génère embedding: [0.12, -0.34, ..., 0.89]
  ↓
  Qdrant stocke: prod_001 → embedding
  ↓
  Réponse: {"status": "success"}

ÉTAPE 3: Utilisateur envoie sa recherche
───────────────────────────────────────
POST /api/v1/search
{
  "image_url": "https://example.com/user_shirt.jpg",
  "top_k": 10,
  "category_filter": "clothing",
  "price_max": 50
}

  ↓
  [T0] API reçoit requête
  
  ↓
  [T1] Vérifier cache Redis
       Clé: "search:abc123def456"
       → PAS EN CACHE
  
  ↓
  [T2] EmbeddingService.embed_image_from_url()
       • Télécharger image: 50ms
       • CLIP processing: 150ms
       • Résultat: [0.11, -0.35, ...]
       Subtotal: 200ms
  
  ↓
  [T3] QdrantService.search()
       • Envoyer vecteur à Qdrant
       • Recherche par similarité: 10ms
       • Résultats: [
           prod_001: 0.98,
           prod_002: 0.95,
           prod_003: 0.92,
           prod_004: 0.88,
           ...
         ]
       Subtotal: 10ms
  
  ↓
  [T4] Appliquer filtres
       • Filtrer category="clothing": 5 produits
       • Filtrer price<50: 4 produits
       Subtotal: 1ms
  
  ↓
  [T5] CacheService.set()
       • Stocker en Redis pour 1 heure
       Subtotal: 1ms
  
  ↓
  [T6] Formater et retourner réponse
       Total time: 212ms
  
  ↓
RÉPONSE:
{
  "query_type": "image",
  "top_k": 10,
  "total_results": 4,
  "results": [
    {
      "product_id": "prod_001",
      "name": "Red Cotton T-Shirt",
      "similarity_score": 0.98,
      "price": 29.99,
      "category": "clothing"
    },
    {
      "product_id": "prod_002",
      "name": "Red Polo Shirt",
      "similarity_score": 0.95,
      "price": 39.99,
      "category": "clothing"
    },
    ...
  ],
  "execution_time_ms": 212.3
}

ÉTAPE 4: Deuxième recherche (même image)
─────────────────────────────────────────
POST /api/v1/search
{
  "image_url": "https://example.com/user_shirt.jpg",
  ...
}

  ↓
  [T0] API reçoit requête
  
  ↓
  [T1] Vérifier cache Redis
       Clé: "search:abc123def456"
       → ✅ TROUVÉ EN CACHE!
  
  ↓
  [T2] Retourner le résultat du cache
       Total time: 5ms
  
  ↓
RÉPONSE: (identique mais 40x plus rapide!)

════════════════════════════════════════════════════════════════════════════════

📊 PERFORMANCE RÉSUMÉE
════════════════════════════════════════════════════════════════════════════════

Opération                 | Sans Cache | Avec Cache
─────────────────────────────────────────────────────
Image download            | 50ms       | -
CLIP embedding            | 150ms      | -
Qdrant search             | 10ms       | -
Filtering & formatting    | 2ms        | -
────────────────────────────────────────────────
TOTAL (1ère recherche)    | 212ms      | -
────────────────────────────────────────────────
Cache lookup              | -          | 5ms
TOTAL (2e recherche)      | -          | 5ms
────────────────────────────────────────────────
SPEED UP                  | 1x         | 42x !!!

════════════════════════════════════════════════════════════════════════════════

Voilà! C'est le fonctionnement complet! 🚀

Des questions sur une partie spécifique?
