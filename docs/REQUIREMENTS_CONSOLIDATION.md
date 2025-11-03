# 📦 Requirements Consolidation Guide

## ✅ Consolidation Complète

Tous les fichiers requirements ont été consolidés en **UN SEUL** fichier:

### Structure Finale

```
requirements.txt (PRINCIPAL - 47 lignes)
├── Core: FastAPI + Uvicorn + Gunicorn
├── Async: aiofiles + aiohttp
├── Images: Pillow + Pillow-SIMD
├── ML-Image: PyTorch 2.0.1 + Transformers (CLIP)
├── ML-Text: scikit-learn (TF-IDF fallback)
└── Vector DB: Qdrant

ANCIENS FICHIERS (déprécié, conservés pour référence):
├── requirements-image-search.txt (DÉPRÉCIÉ)
├── requirements-ultra-light.txt (DÉPRÉCIÉ)
└── requirements-alt.txt (DÉPRÉCIÉ)
```

## 📊 Comparaison

| Aspect | requirements-ultra-light.txt | requirements-image-search.txt | requirements.txt (NEW) |
|--------|------------------------------|-------------------------------|------------------------|
| **Inclut TF-IDF** | ✅ Oui | ❌ Non | ✅ Oui |
| **Inclut CLIP** | ❌ Non | ✅ Oui | ✅ Oui (prioritaire) |
| **PyTorch** | ❌ Non | ✅ 2.0.1 | ✅ 2.0.1 |
| **Taille** | ~50MB | ~800MB-1GB | ~800MB-1GB |
| **Fallback** | ❌ Non | N/A | ✅ TF-IDF if needed |
| **Status** | DÉPRÉCIÉ | DÉPRÉCIÉ | ✅ ACTIF |

## 🎯 Ce qui est inclus

### Dépendances Core
```
fastapi==0.104.1          # Web framework
uvicorn==0.24.0           # ASGI server
gunicorn==21.2.0          # Production server
python-multipart==0.0.6   # File uploads
pydantic==2.5.2           # Data validation
pydantic-settings==2.1.0  # Settings management
```

### Async & Networking
```
aiofiles==23.2.1          # Async file I/O
aiohttp==3.9.1            # Async HTTP
httpx==0.25.2             # HTTP client
python-dotenv==1.0.0      # Environment variables
```

### Image Processing
```
pillow==10.1.0            # Image library
pillow-simd==9.2.0        # SIMD-accelerated Pillow
numpy==1.26.2             # Numerical computing
```

### Vector Database
```
qdrant-client==1.15.1     # Qdrant SDK (disk-based)
```

### Machine Learning: CLIP (PRIMARY)
```
torch==2.0.1              # PyTorch (optimized)
torchvision==0.15.2       # Vision utilities
transformers==4.32.1      # CLIP model loader
```

### Machine Learning: TF-IDF (FALLBACK)
```
scikit-learn==1.3.2       # TF-IDF vectorization
```

## 🚀 Usage

### Local Development

```bash
# Install
pip install -r requirements.txt

# Run server
python -m uvicorn app.main:app --reload

# Run tests
python test_image_search.py
```

### Docker Build

```dockerfile
# Dockerfile automatically uses requirements.txt
COPY requirements.txt requirements.txt
RUN pip install --user --no-cache-dir -r requirements.txt
```

### Azure Container Apps

```powershell
# Dockerfile will use consolidated requirements.txt
docker build -t image-search:latest .
docker push <registry>/image-search:latest
```

## 📋 Files Deprecation

### ⚠️ No Longer Needed

```
requirements-image-search.txt  →  Merged into requirements.txt
requirements-ultra-light.txt   →  TF-IDF included in requirements.txt
requirements-alt.txt           →  Not used (kept for reference)
```

### ✅ Can Be Deleted

If you want to clean up:

```bash
rm requirements-image-search.txt
rm requirements-ultra-light.txt
rm requirements-alt.txt
```

## 🔄 Migration Path

### If you were using...

**requirements-image-search.txt:**
```bash
# OLD
pip install -r requirements-image-search.txt

# NEW
pip install -r requirements.txt
```

**requirements-ultra-light.txt:**
```bash
# OLD (TF-IDF only)
pip install -r requirements-ultra-light.txt

# NEW (CLIP primary + TF-IDF fallback)
pip install -r requirements.txt
```

## 💾 Size Comparison

```
OLD Setup:
├─ requirements-image-search.txt: 20KB file → 800MB-1GB installed
├─ requirements-ultra-light.txt: 18KB file → 50MB installed
└─ requirements-alt.txt: 15KB file → ?

NEW Setup:
└─ requirements.txt: 47KB file → 800MB-1GB installed
   (includes both CLIP + TF-IDF fallback)
```

## 🎯 Architecture with Consolidated Requirements

```
requirements.txt
    ↓
Docker Build (multi-stage)
    ├─ Stage 1 (Builder): Compile all deps
    └─ Stage 2 (Runtime): Copy compiled packages
    ↓
Container Image (~500MB)
    ├─ FastAPI app
    ├─ CLIP Model (512-dim embeddings) ← PRIMARY
    ├─ TF-IDF Service (384-dim) ← FALLBACK
    ├─ Qdrant Vector DB
    └─ All dependencies included
    ↓
Azure Container Apps
    ├─ Auto-scale: 0-10 replicas
    ├─ CPU: 0.5 per replica
    ├─ Memory: 1GB per replica
    └─ Cost: $6-16/month
```

## ✨ Benefits of Consolidation

✅ **Single Source of Truth**: Une seule version des dépendances  
✅ **No Duplication**: Pas de maintenance multiple  
✅ **Clear Intent**: Tous les fichiers dans requirements.txt  
✅ **Fallback Support**: CLIP + TF-IDF dans un seul setup  
✅ **Simpler Dockerfile**: Utilise un seul fichier  
✅ **Easier Upgrades**: Mettre à jour une seule place  

## 🔍 Version Details

### PyTorch Selection

```
torch==2.0.1 (CHOSEN)
├─ Size: ~350MB
├─ Performance: Excellent
├─ Stability: Proven
└─ Reason: 200MB lighter than 2.1.1, same performance

vs

torch==2.1.1 (PREVIOUS)
├─ Size: ~550MB+
├─ Performance: Slightly better
├─ Reason: Avoided due to size + build timeouts
```

### CLIP Model

```
transformers==4.32.1
├─ Model: CLIP ViT-B/32
├─ Dimensions: 512-dim vectors
├─ Performance: ~100-200ms per image
├─ Download: Auto on first use (~350MB)
```

## 📚 Documentation

For detailed usage:
- 📖 `docs/IMAGE_SEARCH_PIPELINE.md` - Architecture & API
- 📖 `docs/QUICKSTART_IMAGE_SEARCH.md` - Deployment guide
- 📖 `IMPLEMENTATION_RECAP.md` - Complete overview

## ⚡ Next Steps

1. ✅ **Done**: Consolidated requirements.txt
2. ✅ **Done**: Updated Dockerfile
3. ⏭️ **Next**: Test locally with new requirements
4. ⏭️ **Next**: Deploy to Azure

```bash
# Test locally
python -m uvicorn app.main:app --reload

# Run tests
python test_image_search.py

# If all pass → Ready for Azure deployment!
```

---

**Single requirements.txt = Simpler, Faster, Better! 🚀**
