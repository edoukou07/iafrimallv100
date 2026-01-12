# 🚀 Guide Interactif - Exécution Pas à Pas

**Ce guide vous aide à déployer sur Azure Container Apps étape par étape.**

---

## 📋 Avant de commencer

### ✅ Checklist pré-déploiement

- [ ] **Azure CLI installé** → `az --version` doit afficher une version
- [ ] **Docker installé** → `docker --version` doit fonctionner
- [ ] **Compte Azure actif** → `az login` ne doit pas échouer
- [ ] **Abonnement Azure** → Vous devez avoir au moins $50 de crédit
- [ ] **Projet cloné** → Vous êtes dans le dossier `iafrimallv100`

```powershell
# Vérifier les prérequis
Write-Host "🔍 Vérification des prérequis..."
az --version | Select-Object -First 1
docker --version
az account show --query "name"
```

---

## 🎯 ÉTAPE 1: Se connecter à Azure

**Durée estimée:** 2 minutes  
**Objectif:** Authentifier votre compte Azure

### Commande:

```powershell
# Se connecter à Azure
az login

# Cela ouvrira un navigateur pour vous authentifier
# Une fois fait, vous verrez votre compte dans PowerShell
```

### ✅ Vérification:

```powershell
# Vérifier que vous êtes connecté
$ACCOUNT = az account show
Write-Host "Connecté en tant que:" $ACCOUNT.user.name
Write-Host "Abonnement:" $ACCOUNT.name

# Devrait afficher votre compte et abonnement
```

### ❌ Si ça échoue:

```powershell
# Réessayer avec login interactif
az login --use-device-code

# Ou vérifier les comptes disponibles
az account list --output table
```

---

## 🎯 ÉTAPE 2: Définir les variables

**Durée estimée:** 2 minutes  
**Objectif:** Configurer les noms des ressources

### Variables à copier-coller:

```powershell
# ===== CONFIGURATION À PERSONNALISER =====

# 1. Choisir un nom de registre UNIQUE (lowercase, 5-50 chars)
$REGISTRY_NAME = "imagesearch$(Get-Random -Minimum 10000 -Maximum 99999)"

# 2. Choisir une région Azure (voir les options disponibles)
$LOCATION = "eastus"  # Options: eastus, westus2, northeurope, canadacentral

# 3. Définir le groupe de ressources
$RESOURCE_GROUP = "image-search-rg"

# 4. Autres variables
$CONTAINER_APP_ENV = "image-search-env"
$API_APP_NAME = "image-search-api"
$WORKER_1_NAME = "image-search-worker-1"
$WORKER_2_NAME = "image-search-worker-2"
$QDRANT_NAME = "image-search-qdrant"
$REDIS_NAME = "image-search-redis"

# 5. Clé Qdrant sécurisée
$QDRANT_API_KEY = "qdrant-key-$(Get-Random -Minimum 100000 -Maximum 999999)"

# ===== FIN DE LA CONFIGURATION =====

# Afficher les variables configurées
Write-Host "✅ Variables configurées:"
Write-Host "  Registry: $REGISTRY_NAME"
Write-Host "  Location: $LOCATION"
Write-Host "  Resource Group: $RESOURCE_GROUP"
Write-Host "  Qdrant API Key: $QDRANT_API_KEY"
```

### ✅ Vérification:

```powershell
# Vérifier que les variables sont définies
Write-Host "Registre: $REGISTRY_NAME"
Write-Host "Région: $LOCATION"

# Les deux doivent afficher les valeurs définies ci-dessus
```

---

## 🎯 ÉTAPE 3: Créer le groupe de ressources

**Durée estimée:** 1 minute  
**Objectif:** Créer un conteneur logique pour toutes les ressources

### Commande:

```powershell
Write-Host "📦 Création du groupe de ressources: $RESOURCE_GROUP"

az group create `
  --name $RESOURCE_GROUP `
  --location $LOCATION

Write-Host "✅ Groupe créé!"
```

### ✅ Vérification:

```powershell
# Vérifier que le groupe existe
az group show `
  --name $RESOURCE_GROUP `
  --query "{Name: name, Location: location}" `
  --output table

# Devrait afficher votre groupe de ressources
```

### ❌ Si ça échoue:

```powershell
# Vérifier les régions disponibles
az containerapp location list --output table

# Choisir une région de la liste et relancer
```

---

## 🎯 ÉTAPE 4: Créer Azure Container Registry

**Durée estimée:** 3 minutes  
**Objectif:** Créer un registre pour stocker les images Docker

### Commande:

```powershell
Write-Host "🐳 Création du registre de conteneurs: $REGISTRY_NAME"

az acr create `
  --resource-group $RESOURCE_GROUP `
  --name $REGISTRY_NAME `
  --sku Basic `
  --output table

Write-Host "✅ Registre créé!"
```

### Récupérer les credentials:

```powershell
# Activer l'accès admin
az acr update `
  --name $REGISTRY_NAME `
  --admin-enabled true

# Récupérer les informations de connexion
$LOGIN_SERVER = $(az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)
$ADMIN_USER = $(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query username --output tsv)
$ADMIN_PASSWORD = $(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv)

Write-Host "✅ Credentials récupérés:"
Write-Host "  Serveur: $LOGIN_SERVER"
Write-Host "  Username: $ADMIN_USER"
Write-Host "  Password: (sécurisé)"
```

### ✅ Vérification:

```powershell
# Afficher les informations du registre
az acr show `
  --name $REGISTRY_NAME `
  --query "{Name: name, URL: loginServer}" `
  --output table
```

---

## 🎯 ÉTAPE 5: Builder et pousser l'image Docker

**Durée estimée:** 10-15 minutes (décharge du modèle CLIP)  
**Objectif:** Créer l'image Docker et la stocker dans Azure

### Commande 1: Se connecter au registre

```powershell
Write-Host "🔐 Connexion au registre ACR..."

az acr login --name $REGISTRY_NAME

Write-Host "✅ Connecté au registre!"
```

### Commande 2: Builder l'image

```powershell
Write-Host "🔨 Construction de l'image Docker..."
Write-Host "⏳ Cela peut prendre 5-10 minutes (téléchargement du modèle CLIP ~500MB)"

# Assurez-vous d'être dans le dossier du projet
cd "C:\Users\hynco\Desktop\iaafrimall\iafrimallv100"

# Builder l'image
docker build -t image-search-api:latest .

Write-Host "✅ Image construite!"
```

### Commande 3: Tagger l'image

```powershell
Write-Host "🏷️  Tagging de l'image..."

docker tag image-search-api:latest "$LOGIN_SERVER/image-search-api:latest"

Write-Host "✅ Image taggée!"
```

### Commande 4: Pousser vers Azure

```powershell
Write-Host "📤 Envoi de l'image vers Azure (peut prendre 3-5 min)..."

docker push "$LOGIN_SERVER/image-search-api:latest"

Write-Host "✅ Image poussée!"
```

### ✅ Vérification:

```powershell
# Vérifier que l'image est dans le registre
az acr repository list `
  --name $REGISTRY_NAME `
  --output table

# Devrait afficher: image-search-api
```

### ❌ Si ça échoue:

```powershell
# Vérifier que Docker fonctionne
docker ps

# Vérifier la connexion au registre
docker info | grep -i registry

# Réessayer l'authentification
az acr login --name $REGISTRY_NAME --expose-token
```

---

## 🎯 ÉTAPE 6: Créer l'Environnement Container Apps

**Durée estimée:** 5-10 minutes  
**Objectif:** Créer un environnement pour héberger les conteneurs

### Commande:

```powershell
Write-Host "🌍 Création de l'environnement Container Apps..."
Write-Host "⏳ Cela prend généralement 5-10 minutes..."

az containerapp env create `
  --name $CONTAINER_APP_ENV `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION

Write-Host "✅ Environnement créé!"
```

### ✅ Vérification:

```powershell
# Vérifier l'environnement
az containerapp env show `
  --name $CONTAINER_APP_ENV `
  --resource-group $RESOURCE_GROUP `
  --query "{Name: name, Status: properties.provisioningState}" `
  --output table

# Devrait montrer "Succeeded"
```

**💡 Note:** Cette étape peut prendre du temps. Prenez un café! ☕

---

## 🎯 ÉTAPE 7: Créer Azure Cache for Redis

**Durée estimée:** 5 minutes  
**Objectif:** Créer le service de cache

### Commande 1: Créer Redis

```powershell
Write-Host "🔴 Création d'Azure Cache for Redis..."

az redis create `
  --resource-group $RESOURCE_GROUP `
  --name $REDIS_NAME `
  --location $LOCATION `
  --sku Basic `
  --capacity 0 `
  --minimum-tls-version 1.2 `
  --enable-non-ssl-port false

Write-Host "✅ Redis créé!"
```

### Commande 2: Récupérer les credentials

```powershell
Write-Host "🔑 Récupération des credentials Redis..."

$REDIS_HOST = $(az redis show --name $REDIS_NAME --resource-group $RESOURCE_GROUP --query hostName --output tsv)
$REDIS_KEY = $(az redis list-keys --name $REDIS_NAME --resource-group $RESOURCE_GROUP --query primaryKey --output tsv)
$REDIS_URL = "redis://:$REDIS_KEY@$REDIS_HOST`:6380?ssl=True"

Write-Host "✅ Credentials Redis:"
Write-Host "  Host: $REDIS_HOST"
Write-Host "  Port: 6380 (SSL)"
```

### ✅ Vérification:

```powershell
# Vérifier que Redis existe
az redis show `
  --name $REDIS_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "{Name: name, Status: hostName}" `
  --output table
```

---

## 🎯 ÉTAPE 8: Créer Qdrant (Vector Database)

**Durée estimée:** 3 minutes  
**Objectif:** Déployer la base de données vectorielle

### Commande:

```powershell
Write-Host "🟦 Déploiement de Qdrant..."

az containerapp create `
  --name $QDRANT_NAME `
  --resource-group $RESOURCE_GROUP `
  --environment $CONTAINER_APP_ENV `
  --image qdrant/qdrant:latest `
  --cpu 0.5 `
  --memory 1.0Gi `
  --environment-variables `
    QDRANT_API_KEY="$QDRANT_API_KEY" `
  --ingress internal `
  --target-port 6333 `
  --transport tcp

Write-Host "✅ Qdrant déployé!"
```

### ✅ Vérification:

```powershell
# Vérifier que Qdrant est démarré
az containerapp show `
  --name $QDRANT_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "{Name: name, Status: properties.runningStatus}" `
  --output table

# Devrait afficher "Running"
```

---

## 🎯 ÉTAPE 9: Déployer l'API FastAPI

**Durée estimée:** 3-5 minutes  
**Objectif:** Déployer l'application principale

### Commande:

```powershell
Write-Host "🟢 Déploiement de l'API FastAPI..."

az containerapp create `
  --name $API_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --environment $CONTAINER_APP_ENV `
  --image "$LOGIN_SERVER/image-search-api:latest" `
  --registry-server $LOGIN_SERVER `
  --registry-username $ADMIN_USER `
  --registry-password $ADMIN_PASSWORD `
  --cpu 1.0 `
  --memory 2.0Gi `
  --environment-variables `
    ENVIRONMENT="production" `
    DEBUG="False" `
    LOG_LEVEL="INFO" `
    REDIS_URL="$REDIS_URL" `
    QDRANT_HOST="$QDRANT_NAME" `
    QDRANT_PORT="6333" `
    QDRANT_API_KEY="$QDRANT_API_KEY" `
  --ingress external `
  --target-port 8000 `
  --min-replicas 1 `
  --max-replicas 3

Write-Host "✅ API déployée!"
```

### Récupérer l'URL publique:

```powershell
$API_URL = $(az containerapp show --name $API_APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv)

Write-Host "🌐 URL de l'API:"
Write-Host "   https://$API_URL"
Write-Host "🔧 Documentation Swagger:"
Write-Host "   https://$API_URL/docs"
```

### ✅ Vérification:

```powershell
# Vérifier l'API
az containerapp show `
  --name $API_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "{Name: name, URL: properties.configuration.ingress.fqdn, Status: properties.runningStatus}" `
  --output table
```

---

## 🎯 ÉTAPE 10: Déployer les Workers

**Durée estimée:** 5-10 minutes  
**Objectif:** Déployer les processus de traitement d'images

### Déployer Worker 1:

```powershell
Write-Host "⚙️  Déploiement du Worker 1..."

az containerapp create `
  --name $WORKER_1_NAME `
  --resource-group $RESOURCE_GROUP `
  --environment $CONTAINER_APP_ENV `
  --image "$LOGIN_SERVER/image-search-api:latest" `
  --registry-server $LOGIN_SERVER `
  --registry-username $ADMIN_USER `
  --registry-password $ADMIN_PASSWORD `
  --cpu 0.5 `
  --memory 1.0Gi `
  --environment-variables `
    ENVIRONMENT="production" `
    DEBUG="False" `
    LOG_LEVEL="INFO" `
    REDIS_URL="$REDIS_URL" `
    QDRANT_HOST="$QDRANT_NAME" `
    QDRANT_PORT="6333" `
    QDRANT_API_KEY="$QDRANT_API_KEY" `
    WORKER_ID="worker-1" `
    WORKER_POLL_INTERVAL="1" `
  --ingress internal `
  --args "python" "-m" "app.workers.image_indexer_worker" "--worker-id" "worker-1"

Write-Host "✅ Worker 1 déployé!"
```

### Déployer Worker 2:

```powershell
Write-Host "⚙️  Déploiement du Worker 2..."

az containerapp create `
  --name $WORKER_2_NAME `
  --resource-group $RESOURCE_GROUP `
  --environment $CONTAINER_APP_ENV `
  --image "$LOGIN_SERVER/image-search-api:latest" `
  --registry-server $LOGIN_SERVER `
  --registry-username $ADMIN_USER `
  --registry-password $ADMIN_PASSWORD `
  --cpu 0.5 `
  --memory 1.0Gi `
  --environment-variables `
    ENVIRONMENT="production" `
    DEBUG="False" `
    LOG_LEVEL="INFO" `
    REDIS_URL="$REDIS_URL" `
    QDRANT_HOST="$QDRANT_NAME" `
    QDRANT_PORT="6333" `
    QDRANT_API_KEY="$QDRANT_API_KEY" `
    WORKER_ID="worker-2" `
    WORKER_POLL_INTERVAL="1" `
  --ingress internal `
  --args "python" "-m" "app.workers.image_indexer_worker" "--worker-id" "worker-2"

Write-Host "✅ Worker 2 déployé!"
```

### ✅ Vérification:

```powershell
# Vérifier les workers
az containerapp list `
  --resource-group $RESOURCE_GROUP `
  --query "[?contains(name, 'worker')].{Name: name, Status: properties.runningStatus}" `
  --output table

# Devrait afficher worker-1 et worker-2 comme "Running"
```

---

## 🎯 ÉTAPE 11: Tester le déploiement

**Durée estimée:** 5 minutes  
**Objectif:** Vérifier que tout fonctionne

### Test 1: Health Check

```powershell
Write-Host "🏥 Test du Health Check..."

$HEALTH = curl -s -X GET "https://$API_URL/api/v1/health" | ConvertFrom-Json

Write-Host "Status API: $($HEALTH.status)"
Write-Host "Qdrant: $($HEALTH.qdrant_connected)"
Write-Host "Redis: $($HEALTH.redis_connected)"

# Tous doivent être "true" ou "healthy"
```

### Test 2: Recherche par texte

```powershell
Write-Host "🔍 Test de recherche par texte..."

$RESULT = curl -s -X POST "https://$API_URL/api/v1/search" `
  -H "Content-Type: application/json" `
  -d '{
    "text_query": "shirt",
    "top_k": 3
  }' | ConvertFrom-Json

Write-Host "Query: $($RESULT.query)"
Write-Host "Résultats: $($RESULT.count)"

# Devrait retourner des résultats
```

### Test 3: Accéder à la documentation

```powershell
Write-Host "📖 Documentation Swagger disponible à:"
Write-Host "https://$API_URL/docs"

# Ouvrir dans le navigateur
Start-Process "https://$API_URL/docs"
```

---

## 🎯 ÉTAPE 12: Consulter les logs

**Durée estimée:** 2 minutes  
**Objectif:** Vérifier qu'il n'y a pas d'erreurs

### Voir les logs de l'API:

```powershell
Write-Host "📋 Affichage des logs API (dernières 50 lignes)..."

az containerapp logs show `
  --name $API_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --tail 50

# Appuyez sur Ctrl+C pour arrêter
```

### Voir les logs en temps réel (Live Stream):

```powershell
Write-Host "📡 Logs en temps réel (Ctrl+C pour arrêter)..."

az containerapp logs show `
  --name $API_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --follow
```

### Logs des workers:

```powershell
# Worker 1
az containerapp logs show `
  --name $WORKER_1_NAME `
  --resource-group $RESOURCE_GROUP `
  --tail 50

# Worker 2
az containerapp logs show `
  --name $WORKER_2_NAME `
  --resource-group $RESOURCE_GROUP `
  --tail 50
```

---

## 📊 ÉTAPE 13: Vérifier le statut global

**Durée estimée:** 1 minute

### Voir tous les services:

```powershell
Write-Host "📊 Statut de tous les services:"

az containerapp list `
  --resource-group $RESOURCE_GROUP `
  --query "[].{Name: name, Status: properties.runningStatus, CPU: properties.template.containers[0].resources.cpu, Memory: properties.template.containers[0].resources.memory}" `
  --output table
```

### Récapitulatif du déploiement:

```powershell
Write-Host ""
Write-Host "════════════════════════════════════════════════════════"
Write-Host "✅ DÉPLOIEMENT RÉUSSI!"
Write-Host "════════════════════════════════════════════════════════"
Write-Host ""
Write-Host "🌐 ACCÈS À L'API:"
Write-Host "   https://$API_URL"
Write-Host ""
Write-Host "📖 DOCUMENTATION:"
Write-Host "   https://$API_URL/docs"
Write-Host ""
Write-Host "💾 INFORMATIONS IMPORTANTES:"
Write-Host "   Registre: $REGISTRY_NAME"
Write-Host "   Groupe: $RESOURCE_GROUP"
Write-Host "   Région: $LOCATION"
Write-Host "   Qdrant API Key: $QDRANT_API_KEY"
Write-Host ""
Write-Host "💰 COÛT ESTIMÉ: ~$48/mois"
Write-Host ""
Write-Host "════════════════════════════════════════════════════════"
```

---

## 🆘 Troubleshooting rapide

### ❌ "Image not found"

```powershell
# Vérifier que l'image a été poussée
az acr repository list --name $REGISTRY_NAME

# Relancer le push
docker push "$LOGIN_SERVER/image-search-api:latest"
```

### ❌ "Redis connection failed"

```powershell
# Attendre quelques minutes que Redis démarre
Start-Sleep -Seconds 60

# Vérifier les logs
az containerapp logs show --name $API_APP_NAME --resource-group $RESOURCE_GROUP
```

### ❌ "Qdrant connection failed"

```powershell
# Vérifier que Qdrant est Running
az containerapp show --name $QDRANT_NAME --resource-group $RESOURCE_GROUP --query properties.runningStatus

# Attendre quelques minutes
Start-Sleep -Seconds 60
```

### ❌ "Health check stuck"

```powershell
# Vérifier les logs détaillés
az containerapp logs show --name $API_APP_NAME --resource-group $RESOURCE_GROUP --follow

# Chercher les erreurs liées à CLIP ou Qdrant
```

---

## 🧹 Nettoyage (Si besoin de recommencer)

### Supprimer tout:

```powershell
Write-Host "⚠️  SUPPRESSION COMPLÈTE"
Write-Host "Cela supprimera TOUTES les ressources créées!"

$confirm = Read-Host "Êtes-vous sûr? (tapez 'yes')"

if ($confirm -eq "yes") {
    az group delete `
      --name $RESOURCE_GROUP `
      --yes `
      --no-wait
    
    Write-Host "✅ Suppression en cours..."
}
```

---

## 📝 Notes importantes

1. **La première exécution peut prendre 30-45 minutes** (téléchargement du modèle CLIP)
2. **Conservez les variables PowerShell** entre les étapes (ne pas fermer PowerShell)
3. **Vérifiez les logs** si quelque chose échoue
4. **L'API sera publiquement accessible** après quelques minutes

---

## 🎯 Résumé des étapes

```
1. ✅ Se connecter à Azure (2 min)
2. ✅ Définir les variables (2 min)
3. ✅ Créer le groupe de ressources (1 min)
4. ✅ Créer le registre Docker (3 min)
5. ✅ Builder et pousser l'image (10-15 min)
6. ✅ Créer l'environnement Container Apps (5-10 min)
7. ✅ Déployer Redis (5 min)
8. ✅ Déployer Qdrant (3 min)
9. ✅ Déployer l'API (3-5 min)
10. ✅ Déployer les Workers (5-10 min)
11. ✅ Tester le déploiement (5 min)
12. ✅ Consulter les logs (2 min)
13. ✅ Vérifier le statut global (1 min)

TOTAL: 45-60 minutes ⏱️
```

---

**Besoin d'aide?** Consultez les logs ou relancez une étape spécifique. 🆘
