# Quick Start Guide - API Recherche par Image CLIP + Qdrant

## ⚡ Démarrage en 5 minutes

### Prérequis
- Docker & Docker Compose installés
- Port 8000 disponible
- 4GB+ RAM libre

### Étapes

#### 1. Démarrer les services
```bash
cd image-search-api
docker-compose up -d
```

**Attendre 1-2 minutes** pour que le modèle CLIP se télécharge (500MB).

#### 2. Vérifier que tout fonctionne
```bash
curl http://localhost:8000/api/v1/health
```

**Réponse attendue:**
```json
{
  "status": "healthy",
  "qdrant_connected": true,
  "redis_connected": true,
  "model_loaded": true
}
```

#### 3. Indexer des produits (optionnel)
```bash
bash batch_import.sh
```

Ou manuellement:
```bash
curl -X POST "http://localhost:8000/api/v1/index-product" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "prod_001",
    "name": "Red T-Shirt",
    "description": "Beautiful red cotton t-shirt",
    "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500",
    "category": "clothing",
    "price": 29.99
  }'
```

#### 4. Effectuer une recherche

**Par image:**
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500",
    "top_k": 10
  }' | jq
```

**Par texte:**
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "text_query": "red cotton shirt",
    "top_k": 10
  }' | jq
```

---

## 📖 Utilisation Interactive

Ouvrez dans votre navigateur:
```
http://localhost:8000/docs
```

Vous verrez l'interface Swagger UI avec toutes les routes documentées.

---

## 🛠️ Commandes Utiles

```bash
# Voir les logs en temps réel
docker-compose logs -f api

# Voir la structure du projet
tree -L 2 -I '__pycache__'

# Vérifier l'état des services
docker-compose ps

# Arrêter les services
docker-compose down

# Redémarrer
docker-compose restart

# Nettoyer tout (attention!)
docker-compose down -v
```

---

## 📊 Exemple de Réponse Complète

```json
{
  "query_type": "image",
  "top_k": 10,
  "total_results": 1,
  "results": [
    {
      "product_id": "prod_001",
      "name": "Red T-Shirt",
      "description": "Beautiful red cotton t-shirt",
      "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500",
      "price": 29.99,
      "category": "clothing",
      "similarity_score": 0.9847
    }
  ],
  "execution_time_ms": 243.5
}
```

---

## 🔧 Configuration Basique

Modifier `.env` pour ajuster:

```env
# Modèle IA
MODEL_NAME=openai/CLIP-ViT-B-32

# Cache (en secondes)
CACHE_TTL=3600

# Nombre de résultats par défaut
TOP_K=10
```

---

## 📁 Structure du Projet

```
image-search-api/
├── app/
│   ├── main.py              # Application FastAPI
│   ├── api/routes.py        # Routes API
│   ├── services/            # Services métier
│   │   ├── embedding_service.py
│   │   ├── qdrant_service.py
│   │   ├── cache_service.py
│   │   └── search_service.py
│   └── models/schemas.py    # Schémas Pydantic
├── docker-compose.yml       # Configuration Docker
├── README.md               # Documentation complète
├── DEPLOYMENT.md           # Guide déploiement
└── client.py              # Client Python
```

---

## 💡 Prochaines Étapes

1. **Intégrer avec votre API e-commerce**: Voir `ecommerce_integration_example.py`
2. **Indexer vos vrais produits**: Utiliser l'endpoint `/api/v1/index-product`
3. **Configurer le déploiement**: Consulter `DEPLOYMENT.md`
4. **Optimiser**: Voir configuration dans `.env`

---

## ❓ FAQ

### Q: Pourquoi ça prend 1-2 min au démarrage?
**R:** Le modèle CLIP (500MB) se télécharge et charge en GPU/CPU lors du premier démarrage.

### Q: Comment augmenter la latence faible?
**R:** 
- Ajouter un GPU: `docker-compose up --gpus all`
- Utiliser un modèle plus léger
- Augmenter les ressources Redis

### Q: Comment tester avec mes propres images?
**R:** Mettre les URLs dans les requêtes ou utiliser le client Python (`client.py`)

### Q: Quel modèle CLIP choisir?
- **ViT-B-32** (défaut): Rapide, 512 dims
- **ViT-L-14**: Plus précis, 768 dims
- **ViT-bigG-14**: Haute précision, 1280 dims

---

## 🆘 Support et Documentation

- **API Docs**: http://localhost:8000/docs
- **README Complet**: `README.md`
- **Guide Déploiement**: `DEPLOYMENT.md`
- **Client Python**: `client.py`
- **Exemple Integration**: `ecommerce_integration_example.py`

---

Besoin d'aide? Vérifiez les logs:
```bash
docker-compose logs -f
```
