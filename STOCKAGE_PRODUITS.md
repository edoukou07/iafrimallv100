╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║          💾 COMMENT LES PRODUITS SONT STOCKÉS DANS L'APPLICATION               ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

📚 TABLE DES MATIÈRES
════════════════════════════════════════════════════════════════════════════════
1. Vue d'ensemble du stockage
2. Structure d'un produit
3. Comment un produit est indexé
4. Où les données sont stockées
5. Comment les recherches retrouvent les produits
6. Exemple complet pas à pas

════════════════════════════════════════════════════════════════════════════════

1️⃣ VUE D'ENSEMBLE - OÙ VONT LES PRODUITS?
════════════════════════════════════════════════════════════════════════════════

L'application a 2 types de stockage:

┌─────────────────────────────────────────────────────────────────┐
│                       QDRANT (Base Vecteurs)                    │
├─────────────────────────────────────────────────────────────────┤
│  Ce qui y est stocké:                                           │
│  ✓ Le vecteur CLIP de chaque produit (512 nombres)              │
│  ✓ Les métadonnées du produit (nom, prix, catégorie, etc)      │
│  ✓ Structure optimisée pour recherche rapide                    │
│                                                                  │
│  Port: 6333                                                      │
│  Type: Base de données vectorielle                               │
│  Durée de vie: Persistante (survit aux redémarrages)            │
│  Format: Binary index HNSW                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    REDIS (Cache des Résultats)                  │
├─────────────────────────────────────────────────────────────────┤
│  Ce qui y est stocké:                                           │
│  ✓ Les résultats des recherches précédentes                     │
│  ✓ Format: Clé-Valeur JSON                                      │
│  ✓ TTL: 1 heure par défaut                                      │
│                                                                  │
│  Port: 6379                                                      │
│  Type: Stockage clé-valeur en RAM                                │
│  Durée de vie: Temporaire (expire après TTL)                    │
│  Format: JSON sérialisé                                         │
└─────────────────────────────────────────────────────────────────┘

════════════════════════════════════════════════════════════════════════════════

2️⃣ STRUCTURE D'UN PRODUIT - QUELLES DONNÉES?
════════════════════════════════════════════════════════════════════════════════

Chaque produit contient:

┌──────────────────────────────────────────────────────────────────┐
│  PRODUIT COMPLET (Modèle Pydantic)                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  id             : str        → "prod_001"                        │
│  name           : str        → "Red Shirt"                       │
│  description    : str        → "Beautiful red cotton shirt"      │
│  image_url      : str        → "https://example.com/shirt.jpg"   │
│  category       : str        → "clothing"                        │
│  price          : float      → 29.99                             │
│  attributes     : dict       → {"color": "red", "size": "M"}     │
│  embedding      : List[512]  → [0.12, -0.34, ..., 0.89]         │
│  created_at     : datetime   → 2024-11-02 10:30:00              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

EXEMPLE JSON COMPLET:

{
  "id": "prod_001",
  "name": "Red Shirt",
  "description": "Beautiful red cotton shirt",
  "image_url": "https://example.com/shirt.jpg",
  "category": "clothing",
  "price": 29.99,
  "attributes": {
    "color": "red",
    "size": "M",
    "material": "cotton",
    "stock": 15
  },
  "embedding": [0.12, -0.34, 0.56, ..., 0.89],  // 512 nombres
  "created_at": "2024-11-02T10:30:00"
}

════════════════════════════════════════════════════════════════════════════════

3️⃣ PROCESSUS D'INDEXATION - COMMENT UN PRODUIT EST STOCKÉ?
════════════════════════════════════════════════════════════════════════════════

Quand vous indexez un produit (POST /api/v1/index-product):

ÉTAPE 1: Réception de la requête
─────────────────────────────────

┌─────────────────────────────────────────────────────┐
│ POST /api/v1/index-product                          │
│ {                                                    │
│   "id": "prod_001",                                 │
│   "name": "Red Shirt",                              │
│   "description": "Beautiful red cotton shirt",      │
│   "image_url": "https://example.com/shirt.jpg",     │
│   "category": "clothing",                           │
│   "price": 29.99,                                   │
│   "attributes": {"color": "red", "size": "M"}       │
│ }                                                    │
└─────────────────────────────────────────────────────┘

           ↓

ÉTAPE 2: Téléchargement de l'image
──────────────────────────────────

EmbeddingService.embed_image_from_url()
    ├─ Télécharger image depuis URL
    ├─ Convertir en PIL Image
    ├─ Redimensionner à 224x224
    └─ Normaliser les pixels

           ↓

ÉTAPE 3: Génération de l'embedding CLIP
───────────────────────────────────────

CLIP Processor
    ├─ Préparer l'image normalisée
    └─ Passer au modèle ViT-B-32

CLIP Model (GPU/CPU)
    ├─ Traitement neural
    ├─ Extraction des features (2048 dimensions)
    └─ Réduction à 512 dimensions

Normalization L2
    └─ Normaliser le vecteur pour distance cosinus

RÉSULTAT: embedding = [0.12, -0.34, 0.56, ..., 0.89]  (512 nombres)

           ↓

ÉTAPE 4: Stockage dans Qdrant
──────────────────────────────

QdrantService.upsert_product()
    │
    ├─ Créer PointStruct:
    │  {
    │    id: hash("prod_001") % 10^8 = 12345678  // ID numérique
    │    vector: [0.12, -0.34, ..., 0.89]       // Embedding
    │    payload: {                              // Métadonnées
    │      "product_id": "prod_001",
    │      "name": "Red Shirt",
    │      "description": "...",
    │      "image_url": "...",
    │      "category": "clothing",
    │      "price": 29.99,
    │      "attributes": {...}
    │    }
    │  }
    │
    └─ Envoyer à Qdrant.upsert()
       └─ Stocker dans collection "products"

           ↓

ÉTAPE 5: Confirmation de succès
────────────────────────────────

{"status": "success", "product_id": "prod_001"}

════════════════════════════════════════════════════════════════════════════════

4️⃣ STRUCTURE DE STOCKAGE DANS QDRANT
════════════════════════════════════════════════════════════════════════════════

COLLECTION "products" (dans Qdrant)
│
├─ POINT 1 (produit 1)
│  ├─ ID: 12345678
│  ├─ VECTOR: [0.12, -0.34, 0.56, ..., 0.89]  (512 dim)
│  └─ PAYLOAD (métadonnées):
│     ├─ product_id: "prod_001"
│     ├─ name: "Red Shirt"
│     ├─ price: 29.99
│     ├─ category: "clothing"
│     ├─ image_url: "https://..."
│     └─ attributes: {...}
│
├─ POINT 2 (produit 2)
│  ├─ ID: 87654321
│  ├─ VECTOR: [0.11, -0.35, 0.55, ..., 0.88]
│  └─ PAYLOAD: {...}
│
├─ POINT 3 (produit 3)
│  ├─ ID: 55555555
│  ├─ VECTOR: [0.45, 0.67, -0.12, ..., -0.34]
│  └─ PAYLOAD: {...}
│
└─ ...  (potentiellement des millions de produits)


INDEX HNSW (Hierarchical Navigable Small World)
└─ Structure optimisée pour recherche rapide O(log n)
   └─ Permet trouver les voisins proches en millisecondes

════════════════════════════════════════════════════════════════════════════════

5️⃣ COMMENT UNE RECHERCHE RETROUVE LES PRODUITS?
════════════════════════════════════════════════════════════════════════════════

Scénario: Utilisateur recherche "t-shirt rouge"

ÉTAPE 1: Convertir la recherche en vecteur
───────────────────────────────────────────

Text: "red shirt"
  ↓
EmbeddingService.embed_text()
  ↓
CLIP Text Encoder: "red shirt" → [0.11, -0.34, 0.54, ..., 0.88]
  ↓
query_vector (512 nombres)

           ↓

ÉTAPE 2: Calcul de similarité
──────────────────────────────

Pour chaque produit en base:
    distance = 1 - (query_vector · product_vector) / (||query|| * ||product||)

Exemple:
    query_vector           = [0.11, -0.34, ...]
    prod_001_vector        = [0.12, -0.34, ...]
    prod_002_vector        = [0.45,  0.67, ...]
    prod_003_vector        = [0.11, -0.35, ...]

    prod_001: distance = 0.02  (TRÈS similaire! 0 = identique)
    prod_003: distance = 0.03  (très similaire)
    prod_002: distance = 0.85  (pas similaire)

           ↓

ÉTAPE 3: Tri par score
──────────────────────

Résultats triés (meilleurs en premier):

    1. prod_001: score = 0.98  ✅ T-shirt rouge! Match!
    2. prod_003: score = 0.97  ✅ T-shirt rose! Proche!
    3. prod_004: score = 0.92  ✅ Chemise rouge! Un peu similaire
    4. prod_002: score = 0.15  ❌ Chaussettes noires. Pas pertinent

           ↓

ÉTAPE 4: Appliquer filtres (optionnel)
───────────────────────────────────────

Si category_filter = "clothing":
    → Garder prod_001, prod_003, prod_004
    → Exclure prod_002

Si price_max = 50:
    → Garder ceux avec price <= 50
    → Exclure les trop chers

           ↓

ÉTAPE 5: Retourner top_k résultats
───────────────────────────────────

top_k = 10 (défaut)
Retourner les 10 meilleurs (ou moins si pas assez)

Réponse:
{
  "query_type": "text",
  "top_k": 10,
  "total_results": 3,
  "results": [
    {
      "product_id": "prod_001",
      "name": "Red Shirt",
      "price": 29.99,
      "category": "clothing",
      "similarity_score": 0.98
    },
    {
      "product_id": "prod_003",
      "name": "Rose T-Shirt",
      "price": 34.99,
      "category": "clothing",
      "similarity_score": 0.97
    },
    ...
  ]
}

════════════════════════════════════════════════════════════════════════════════

6️⃣ EXEMPLE COMPLET PAS À PAS
════════════════════════════════════════════════════════════════════════════════

SCÉNARIO COMPLET: Index 3 produits, puis recherche

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉTAPE 1: INDEX PRODUIT 1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

POST /api/v1/index-product
{
  "id": "prod_001",
  "name": "Red Shirt",
  "image_url": "https://example.com/red-shirt.jpg",
  "category": "clothing",
  "price": 29.99,
  ...
}

Processus:
├─ Télécharger image
├─ CLIP génère: [0.12, -0.34, 0.56, 0.78, ..., 0.89]  (512 nombres)
├─ Stocker dans Qdrant:
│  {
│    id: 12345678,
│    vector: [0.12, -0.34, ...],
│    payload: {product_id, name, price, ...}
│  }
└─ Réponse: {"status": "success"}

Qdrant contient maintenant:
┌──────────────────────┐
│ COLLECTION products  │
├──────────────────────┤
│ [0.12, -0.34, ...]  │ ← produit 1
└──────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉTAPE 2: INDEX PRODUIT 2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

POST /api/v1/index-product
{
  "id": "prod_002",
  "name": "Blue Shirt",
  "image_url": "https://example.com/blue-shirt.jpg",
  "category": "clothing",
  "price": 34.99,
  ...
}

Processus similaire:
└─ CLIP génère: [0.45, 0.67, -0.12, ..., -0.34]

Qdrant contient maintenant:
┌──────────────────────┐
│ COLLECTION products  │
├──────────────────────┤
│ [0.12, -0.34, ...]  │ ← produit 1 (RED)
│ [0.45, 0.67, ...]   │ ← produit 2 (BLUE)
└──────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉTAPE 3: INDEX PRODUIT 3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

POST /api/v1/index-product
{
  "id": "prod_003",
  "name": "Pink Shirt",
  "image_url": "https://example.com/pink-shirt.jpg",
  "category": "clothing",
  "price": 32.99,
  ...
}

Processus similaire:
└─ CLIP génère: [0.11, -0.35, 0.54, ..., 0.87]

Qdrant contient maintenant:
┌──────────────────────────────────────┐
│  COLLECTION "products" (3 produits)  │
├──────────────────────────────────────┤
│  [0.12, -0.34, ...]  ← produit 1 RED │
│  [0.45, 0.67, ...]   ← produit 2 BLU │
│  [0.11, -0.35, ...]  ← produit 3 PNK │
└──────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉTAPE 4: RECHERCHE "red shirt"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

POST /api/v1/search
{
  "text_query": "red shirt",
  "top_k": 10
}

Processus:
├─ Vérifier cache Redis: "search:hash_de_red_shirt"
│  └─ Pas en cache! (première recherche)
│
├─ CLIP génère query_vector: [0.12, -0.34, 0.55, ..., 0.88]
│  (similaire à produit 1, moins similaire aux autres)
│
├─ Qdrant.search(query_vector, top_k=10):
│  ├─ Distance avec produit 1: 0.02 ✅ (très similaire!)
│  ├─ Distance avec produit 3: 0.03 ✅ (similaire)
│  └─ Distance avec produit 2: 0.85 ❌ (pas similaire)
│
├─ Tri par score:
│  1. prod_001: 0.98 (RED ← MATCH!)
│  2. prod_003: 0.97 (PINK - couleur proche)
│  3. prod_002: 0.15 (BLUE - ignoré)
│
├─ Stocker en Redis avec TTL 1h:
│  Clé: "search:hash_de_red_shirt"
│  Valeur: {résultats JSON}
│
└─ Retourner réponse

Réponse:
{
  "query_type": "text",
  "top_k": 10,
  "total_results": 2,
  "results": [
    {
      "product_id": "prod_001",
      "name": "Red Shirt",
      "price": 29.99,
      "similarity_score": 0.98  ← MEILLEUR MATCH
    },
    {
      "product_id": "prod_003",
      "name": "Pink Shirt",
      "price": 32.99,
      "similarity_score": 0.97
    }
  ],
  "execution_time_ms": 245.3
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉTAPE 5: DEUXIÈME RECHERCHE "red shirt" (5 MIN PLUS TARD)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

POST /api/v1/search
{
  "text_query": "red shirt",
  "top_k": 10
}

Processus:
├─ Vérifier cache Redis: "search:hash_de_red_shirt"
│  └─ ✅ TROUVÉ EN CACHE!
│
└─ Retourner le résultat du cache directement

Réponse: (identique mais INSTANT - 5ms au lieu de 245ms!)

════════════════════════════════════════════════════════════════════════════════

📊 RÉSUMÉ VISUEL DU STOCKAGE
════════════════════════════════════════════════════════════════════════════════

QDRANT (Base vecteurs)          REDIS (Cache)
│                               │
├─ Collection "products"         ├─ search:hash1 → résultats
│  ├─ Produit 1:                 ├─ search:hash2 → résultats
│  │  ├─ ID: 12345678            ├─ search:hash3 → résultats
│  │  ├─ Vector: [512 nombres]   └─ (TTL: 3600s)
│  │  └─ Payload: {metadata}
│  │
│  ├─ Produit 2:
│  │  ├─ ID: 87654321
│  │  ├─ Vector: [512 nombres]
│  │  └─ Payload: {metadata}
│  │
│  └─ ... (millions possible)
│
└─ Index HNSW (pour recherche rapide)

UTILITÉ:
─ Qdrant: Recherche par similitude vectorielle (lent la 1e fois)
─ Redis: Cache des résultats (rapide après)

════════════════════════════════════════════════════════════════════════════════

💡 POINTS CLÉS À RETENIR
════════════════════════════════════════════════════════════════════════════════

1. QDRANT stocke:
   ✓ Vecteur CLIP (512 nombres) → identifie le produit par apparence
   ✓ Métadonnées (nom, prix, catégorie, etc.) → affichage résultats

2. Format stocké:
   {
     id: hash(product_id),
     vector: [512 nombres],
     payload: {product_id, name, price, category, image_url, ...}
   }

3. Recherche par:
   ✓ Vectorielle → rapidité (index HNSW)
   ✓ Distance cosinus → qualité des résultats

4. Cache Redis:
   ✓ Mémorise les résultats
   ✓ Rend 2e recherche 40x plus rapide
   ✓ Expire après 1 heure

5. Persistance:
   ✓ Qdrant: Sur disque (les produits restent)
   ✓ Redis: En RAM (données temporaires)

════════════════════════════════════════════════════════════════════════════════

Des questions? 🚀
