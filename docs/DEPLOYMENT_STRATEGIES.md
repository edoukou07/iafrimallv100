# 🔧 Stratégie de Déploiement Alternative - Sans Docker

Azure App Service a du mal à construire l'image Docker avec PyTorch/Transformers (trop lourd).

## Solution: Déployer directement Python sur Azure

### Étape 1: Créer un fichier de startup

Créer `startup.txt` ou configurer la commande de démarrage via CLI:

```powershell
az webapp config set `
  -g ia-image-search-rg `
  -n image-search-api-123 `
  --startup-command "gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 600 --bind=0.0.0.0:8000"
```

### Étape 2: Créer un fichier requirements-azure.txt (lightweight)

Sans les dépendances lourdes pour le déploiement initial:

```
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
qdrant-client==2.6.4
redis==5.0.1
pydantic==2.5.2
pydantic-settings==2.1.0
aiofiles==23.2.1
python-dotenv==1.0.0
httpx==0.25.2
aiohttp==3.9.1
gunicorn==21.2.0
```

### Étape 3: Configurer Azure pour Python

```powershell
# Configurer runtime Python
az webapp config set `
  -g ia-image-search-rg `
  -n image-search-api-123 `
  --linux-fx-version "PYTHON|3.11"

# Ajouter les app settings
az webapp config appsettings set `
  -g ia-image-search-rg `
  -n image-search-api-123 `
  --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=false
```

### Étape 4: Créer un script de déploiement

```powershell
# Créer le ZIP
$files = @("app", "requirements.txt", ".deployment", ".env")
Compress-Archive -Path $files -DestinationPath deploy-python.zip -Force

# Déployer
az webapp deployment source config-zip `
  -g ia-image-search-rg `
  -n image-search-api-123 `
  --src deploy-python.zip
```

### Étape 5: Alternative - Utiliser Azure Container Registry + ACR

Si Docker reste nécessaire:

```powershell
# Créer un Azure Container Registry
az acr create `
  -g ia-image-search-rg `
  --name iafrimallregistry `
  --sku Basic

# Construire et pousser l'image
az acr build `
  -r iafrimallregistry `
  -t image-search-api:latest `
  .

# Configurer le Web App
az webapp create `
  -g ia-image-search-rg `
  -p image-search-plan `
  -n image-search-api-123 `
  -i iafrimallregistry.azurecr.io/image-search-api:latest
```

---

## Recommandation: Commençons par l'option Lightweight

Le problème vient de PyTorch (800MB+) + Transformers qui sont trop lourds pour le build Azure.

**Solution rapide:**
1. Réduire les dépendances pour le déploiement initial
2. Installer PyTorch seulement si nécessaire en runtime
3. Ou utiliser Azure Container Registry pour une meilleure gestion des images

Voulez-vous que j'implémente l'une de ces solutions?
