# 🚀 Guide de Déploiement Azure Container Apps

**Version:** 1.0  
**Date:** January 2026  
**Plateforme:** Azure Container Apps + Redis + Qdrant

---

## 📑 Table des Matières

1. [Prérequis](#prérequis)
2. [Vue d'ensemble](#vue-densemble)
3. [Configuration initiale](#configuration-initiale)
4. [Déploiement étape par étape](#déploiement-étape-par-étape)
5. [Tests et Monitoring](#tests-et-monitoring)
6. [💰 Réduction des Coûts](#-réduction-des-coûts)
7. [Troubleshooting](#troubleshooting)

---

## ✅ Prérequis

### Logiciels requis

```powershell
# 1. Azure CLI
# Windows: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows
# macOS: brew install azure-cli
# Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Vérifier l'installation
az --version  # Doit afficher la version (>= 2.50)

# 2. Docker
# Windows: https://www.docker.com/products/docker-desktop
# Vérifier: docker --version

# 3. PowerShell 5.1+ (pour Windows)
$PSVersionTable.PSVersion
```

### Compte Azure

- ✅ Compte Azure avec abonnement actif
- ✅ Accès à créer des ressources (rôle "Contributor" minimum)
- ✅ Quota de CPU/RAM disponible

```powershell
# Vérifier l'accès Azure
az login

# Voir les abonnements
az account list --output table

# Choisir un abonnement (si plusieurs)
az account set --subscription "Subscription ID"
```

---

## 🏗️ Vue d'ensemble

### Architecture déployée

```
┌─────────────────────────────────────────────┐
│           Internet Utilisateurs             │
└────────────────┬────────────────────────────┘
                 │ HTTPS
                 ▼
     ┌──────────────────────────┐
     │  API FastAPI Container   │ (Port 8000)
     │  - Ingress: PUBLIC       │
     │  - CPU: 1.0              │
     │  - RAM: 2.0 Gi           │
     └──────────┬───────────────┘
                │
    ┌───────────┼────────────┐
    │           │            │
    ▼           ▼            ▼
┌─────────┐ ┌────────┐ ┌──────────┐
│ Qdrant  │ │ Redis  │ │  Workers │
│ Vector  │ │ Cache  │ │ (x2)     │
│ DB      │ │        │ │ Process  │
└─────────┘ └────────┘ │ Images   │
                        └──────────┘
   Internal Network (image-search-net)
```

### Services déployés

| Service | Type | CPU | RAM | Coût |
|---------|------|-----|-----|------|
| **API** | Container App | 1.0 | 2.0 Gi | $10-12 |
| **Worker-1** | Container App | 0.5 | 1.0 Gi | $2-3 |
| **Worker-2** | Container App | 0.5 | 1.0 Gi | $2-3 |
| **Qdrant** | Container App | 0.5 | 1.0 Gi | $2-3 |
| **Redis** | Azure Cache | Basic 250MB | - | $5-7 |
| **Total mensuel** | | | | **$21-28** |

---

## 🔧 Configuration initiale

### Étape 1: Définir les variables d'environnement

```powershell
# ===== À MODIFIER SELON VOS BESOINS =====

# Noms des ressources (doivent être uniques globalement)
$RESOURCE_GROUP = "image-search-rg"
$REGISTRY_NAME = "imagesearchreg$(Get-Random -Minimum 100 -Maximum 999)"  # Unique
$LOCATION = "eastus"  # Ou autre région (westus2, northeurope, etc.)

# Container Apps
$CONTAINER_APP_ENV = "image-search-env"
$API_APP_NAME = "image-search-api"
$WORKER_1_NAME = "image-search-worker-1"
$WORKER_2_NAME = "image-search-worker-2"
$QDRANT_NAME = "image-search-qdrant"

# Redis
$REDIS_NAME = "image-search-redis"

# Clés et tokens
$QDRANT_API_KEY = "qdrant-secure-key-$(New-Guid | ForEach-Object { $_.ToString().Replace('-','').Substring(0,16) })"

# ===== Optionnel =====
# Définir si vous utiliser un registre existant
$USE_EXISTING_REGISTRY = $false
```

### Étape 2: Vérifier les quotas Azure

```powershell
# Afficher les quotas
az vm usage list --location $LOCATION --output table

# Vérifier la région est disponible pour Container Apps
az containerapp location list --output table | Select-Object -Property Name

# Vérifier le SKU Redis
az redis create --help | grep "sku"
```

---

## 📦 Déploiement étape par étape

### Étape 3: Créer le groupe de ressources

```powershell
Write-Host "✅ Création du groupe de ressources: $RESOURCE_GROUP"

az group create `
  --name $RESOURCE_GROUP `
  --location $LOCATION `
  --output table

Write-Host "✅ Groupe de ressources créé avec succès"
```

### Étape 4: Créer Azure Container Registry

```powershell
Write-Host "✅ Création du registre de conteneurs: $REGISTRY_NAME"

az acr create `
  --resource-group $RESOURCE_GROUP `
  --name $REGISTRY_NAME `
  --sku Basic `
  --output table

# Activer l'accès admin
az acr update `
  --name $REGISTRY_NAME `
  --admin-enabled true

# Récupérer les credentials
$LOGIN_SERVER = $(az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)
$ADMIN_USER = $(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query username --output tsv)
$ADMIN_PASSWORD = $(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv)

Write-Host "✅ Registre créé"
Write-Host "   URL: $LOGIN_SERVER"
Write-Host "   Username: $ADMIN_USER"
```

### Étape 5: Builder et pousser l'image Docker

```powershell
Write-Host "✅ Building Docker image..."

# Se connecter au registre
az acr login --name $REGISTRY_NAME

# Builder l'image
docker build -t image-search-api:latest .

# Tagger l'image
docker tag image-search-api:latest "$LOGIN_SERVER/image-search-api:latest"

# Pousser vers Azure
Write-Host "Pushing to $LOGIN_SERVER..."
docker push "$LOGIN_SERVER/image-search-api:latest"

# Vérifier
$IMAGE_COUNT = $(az acr repository list --name $REGISTRY_NAME --query "length(@)" --output tsv)
Write-Host "✅ Image poussée avec succès. Total images: $IMAGE_COUNT"
```

### Étape 6: Créer l'Environnement Container Apps

```powershell
Write-Host "✅ Création de l'environnement Container Apps (prend ~5-10 min)..."

az containerapp env create `
  --name $CONTAINER_APP_ENV `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION

Write-Host "✅ Environnement créé avec succès"
```

### Étape 7: Déployer Azure Cache for Redis

```powershell
Write-Host "✅ Déploiement d'Azure Cache for Redis..."

az redis create `
  --resource-group $RESOURCE_GROUP `
  --name $REDIS_NAME `
  --location $LOCATION `
  --sku Basic `
  --capacity 0 `  # 250 MB
  --minimum-tls-version 1.2 `
  --enable-non-ssl-port false `
  --output table

# Récupérer les credentials
$REDIS_HOST = $(az redis show --name $REDIS_NAME --resource-group $RESOURCE_GROUP --query hostName --output tsv)
$REDIS_KEY = $(az redis list-keys --name $REDIS_NAME --resource-group $RESOURCE_GROUP --query primaryKey --output tsv)

# Format de la connexion Redis
$REDIS_URL = "redis://:$REDIS_KEY@$REDIS_HOST`:6380?ssl=True"

Write-Host "✅ Redis déployé avec succès"
Write-Host "   Host: $REDIS_HOST"
Write-Host "   Port: 6380 (SSL)"
```

### Étape 8: Déployer Qdrant

```powershell
Write-Host "✅ Déploiement de Qdrant Vector Database..."

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
  --transport tcp `
  --output table

Write-Host "✅ Qdrant déployé avec succès"
Write-Host "   Accès: Internal uniquement (image-search-qdrant:6333)"
```

### Étape 9: Déployer l'API FastAPI

```powershell
Write-Host "✅ Déploiement de l'API FastAPI..."

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
  --max-replicas 3 `
  --output table

# Récupérer l'URL publique
$API_URL = $(az containerapp show --name $API_APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv)

Write-Host "✅ API déployée avec succès"
Write-Host "   URL: https://$API_URL"
Write-Host "   Docs: https://$API_URL/docs"
```

### Étape 10: Déployer les Workers

```powershell
Write-Host "✅ Déploiement des Workers..."

# Worker 1
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
  --args "python" "-m" "app.workers.image_indexer_worker" "--worker-id" "worker-1" `
  --output table

# Worker 2
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
  --args "python" "-m" "app.workers.image_indexer_worker" "--worker-id" "worker-2" `
  --output table

Write-Host "✅ Workers déployés avec succès"
```

---

## ✅ Tests et Monitoring

### Étape 11: Vérifier le déploiement

```powershell
Write-Host "✅ Vérification du déploiement..."

# Récupérer l'URL API
$API_URL = $(az containerapp show --name $API_APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv)
$API_URL_FULL = "https://$API_URL"

# 1. Vérifier la santé
Write-Host "1️⃣  Health check..."
$health = curl -s -X GET "$API_URL_FULL/api/v1/health" | ConvertFrom-Json
Write-Host "   Status: $($health.status)"
Write-Host "   Qdrant: $($health.qdrant_connected)"
Write-Host "   Redis: $($health.redis_connected)"

# 2. Tester une recherche
Write-Host "2️⃣  Test recherche par texte..."
$search = curl -s -X POST "$API_URL_FULL/api/v1/search" `
  -H "Content-Type: application/json" `
  -d '{"text_query": "red shirt", "top_k": 3}' | ConvertFrom-Json

Write-Host "   Requête: $($search.query)"
Write-Host "   Résultats: $($search.count)"

# 3. Accéder à la documentation
Write-Host "3️⃣  Documentation interactive disponible à:"
Write-Host "   $API_URL_FULL/docs"

Write-Host "✅ Déploiement réussi!"
```

### Étape 12: Voir les logs

```powershell
# Logs de l'API (en temps réel)
Write-Host "📋 Logs API (Ctrl+C pour arrêter):"
az containerapp logs show `
  --name $API_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --follow

# Logs des workers
az containerapp logs show `
  --name $WORKER_1_NAME `
  --resource-group $RESOURCE_GROUP `
  --tail 50

# Logs de Qdrant
az containerapp logs show `
  --name $QDRANT_NAME `
  --resource-group $RESOURCE_GROUP `
  --tail 50
```

### Étape 13: Monitoring

```powershell
# Voir le statut de toutes les apps
Write-Host "📊 Statut des Container Apps:"
az containerapp list `
  --resource-group $RESOURCE_GROUP `
  --query "[].{Name: name, Status: properties.runningStatus, CPU: properties.template.containers[0].resources.cpu, Memory: properties.template.containers[0].resources.memory}" `
  --output table

# Voir les révisions
Write-Host "📜 Révisions de l'API:"
az containerapp revision list `
  --name $API_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "[].{Revision: name, Created: properties.createdTime, Status: properties.provisioningState}" `
  --output table
```

---

## 🔄 Operations courantes

### Mettre à jour l'image (après modifications du code)

```powershell
# 1. Rebuild et push
docker build -t image-search-api:v2 .
docker tag image-search-api:v2 "$LOGIN_SERVER/image-search-api:v2"
docker push "$LOGIN_SERVER/image-search-api:v2"

# 2. Mettre à jour l'API
az containerapp update `
  --name $API_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --image "$LOGIN_SERVER/image-search-api:v2"

Write-Host "✅ Mise à jour déployée"
```

### Augmenter les ressources

```powershell
# Augmenter CPU et RAM de l'API
az containerapp update `
  --name $API_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --cpu 2.0 `
  --memory 4.0Gi

Write-Host "✅ Ressources augmentées"
```

### Configurer le scaling automatique

```powershell
# Autoscaling basé sur HTTP
az containerapp update `
  --name $API_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --min-replicas 1 `
  --max-replicas 5 `
  --scale-rule-type http `
  --scale-rule-http-concurrency 100

Write-Host "✅ Autoscaling configuré"
```

### Voir les variables d'environnement

```powershell
az containerapp show `
  --name $API_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --query properties.template.containers[0].env `
  --output table
```

---

## 💰 Réduction des Coûts

### Stratégies principales

#### **1. Configuration ÉCONOMIQUE (Développement/Test)**

**Coût: ~$12-15/mois** (75% moins cher)

```powershell
# API: Minimal
az containerapp create `
  --name $API_APP_NAME `
  --cpu 0.25 `
  --memory 0.5Gi `
  --min-replicas 1 `
  --max-replicas 2

# Workers: 1 seul worker au lieu de 2
az containerapp create `
  --name $WORKER_1_NAME `
  --cpu 0.25 `
  --memory 0.5Gi

# Redis: Tier Free (à la place de Basic)
# ⚠️ Note: Azure Cache Free n'existe plus
# Alternative: Utiliser un conteneur Redis à la place

# Qdrant: Réduire
az containerapp create `
  --name $QDRANT_NAME `
  --cpu 0.25 `
  --memory 0.5Gi
```

| Composant | CPU | RAM | Coût/mois |
|-----------|-----|-----|-----------|
| API | 0.25 | 0.5Gi | $2 |
| Worker | 0.25 | 0.5Gi | $1.50 |
| Qdrant | 0.25 | 0.5Gi | $1.50 |
| Redis (container) | 0.25 | 0.5Gi | $1.50 |
| **TOTAL** | | | **~$6-8/mois** |

---

#### **2. Configuration PRODUCTION (Recommandée - Current)**

**Coût: ~$48/mois**

Voir le déploiement étape par étape ci-dessus.

---

#### **3. Configuration ÉCONOMIQUE PRODUCTION**

**Coût: ~$25-30/mois** (40% moins cher que current)

```powershell
# API: Réduit
$API_APP_CPU = 0.75
$API_APP_MEMORY = 1.5Gi
$API_MIN_REPLICAS = 1
$API_MAX_REPLICAS = 2  # Au lieu de 3

# Worker: 1 seul worker au lieu de 2
# Redis: Basic toujours (mais peut passer à Free si volume faible)
$REDIS_SKU = "Basic"
$REDIS_CAPACITY = 0

# Qdrant: Réduit
$QDRANT_CPU = 0.25
$QDRANT_MEMORY = 0.5Gi
```

| Composant | Changement | Économie |
|-----------|-----------|----------|
| API | 1.0→0.75 CPU, 2.0→1.5 RAM | -30% |
| Workers | 2→1 worker | -50% |
| Qdrant | Ressources réduites | -50% |
| Redis | Inchangé | - |
| **Économie totale** | | **-40%** |

---

### Tactiques avancées de réduction

#### **A. Remplacer Redis Cloud par Redis Container**

Au lieu d'utiliser Azure Cache for Redis ($8/mois):

```powershell
# Créer Redis comme Container App
az containerapp create `
  --name image-search-redis-container `
  --environment $CONTAINER_APP_ENV `
  --image redis:7-alpine `
  --cpu 0.25 `
  --memory 0.5Gi `
  --environment-variables APPENDONLY=yes `
  --ingress internal `
  --target-port 6379

# Coût: $1.50/mois (au lieu de $8/mois)
# ⚠️ Données perdues en cas de crash (ajouter persistance via volume)
```

**Économie: $6.50/mois**

---

#### **B. Réduire le nombre de workers pendant les heures creuses**

```powershell
# Peak hours: 2 workers
az containerapp update `
  --name $WORKER_1_NAME `
  --cpu 0.5 `
  --memory 1.0Gi

# Off-peak: Arrêter temporairement le Worker 2
az containerapp delete `
  --name $WORKER_2_NAME `
  --resource-group $RESOURCE_GROUP

# Vous pouvez la recréer quand nécessaire
```

**Économie: $3-5/mois**

---

#### **C. Utiliser Azure Functions à la place des Workers**

**Pour le traitement asynchrone d'images:**

```powershell
# Au lieu d'avoir 2 workers CPU toujours allumés
# Utiliser une Azure Function avec Timer trigger
# Coût: $0.20 par million d'exécutions (très bon marché!)

# 1 million d'exécutions = $0.20 (vs $96 pour 2 workers 24/7)
```

**Économie potentielle: $90/mois** (si traffic élevé)

---

#### **D. Qdrant: Réduire ou supprimer**

Si vous n'avez pas besoin de recherche vectorielle instantanée:

```powershell
# Option 1: Pas de Qdrant, utiliser PostgreSQL avec pgvector
# Coût: ~$5-10/mois (vs $8/mois pour Qdrant)

# Option 2: Indexation batch la nuit
# Garder Qdrant mais le scale à 0 pendant les heures creuses
az containerapp update `
  --name $QDRANT_NAME `
  --cpu 0.25 `
  --memory 0.5Gi `
  --min-replicas 0  # Scale à 0 pendant la nuit

# Économie: $2-3/mois
```

---

#### **E. Utiliser Azure Static Web App (Free tier) pour l'API simple**

Si votre API est simple (sans recherche vectorielle):

```powershell
# Au lieu de Container Apps ($10+/mois):
# Déployer sur Static Web App ($10-50/mois mais avec Free tier inclus)

# Coût: FREE (jusqu'à 1GB stockage, fonction Azure incluses)
```

---

### 🎯 Configurations optimales par cas d'usage

#### **Cas 1: POC/Développement (Minimal)**

```powershell
# Budget: $5-8/mois

# Configuration:
# - 1 API légère (0.25 CPU, 0.5GB)
# - 1 Worker (0.25 CPU, 0.5GB) 
# - 1 Qdrant (0.25 CPU, 0.5GB)
# - Redis: Local/Container (0.25 CPU, 0.5GB)

# Scripts:
$ENVIRONMENT_TYPE = "dev"
$API_CPU = 0.25
$API_MEMORY = 0.5Gi
$WORKER_COUNT = 1
$QDRANT_CPU = 0.25
$QDRANT_MEMORY = 0.5Gi
$USE_AZURE_REDIS = $false  # Container Redis
```

#### **Cas 2: Staging (Équilibré)**

```powershell
# Budget: $15-20/mois

$ENVIRONMENT_TYPE = "staging"
$API_CPU = 0.5
$API_MEMORY = 1.0Gi
$API_MIN_REPLICAS = 1
$API_MAX_REPLICAS = 2
$WORKER_COUNT = 1
$QDRANT_CPU = 0.5
$QDRANT_MEMORY = 1.0Gi
$USE_AZURE_REDIS = $true
```

#### **Cas 3: Production (Recommandé)**

```powershell
# Budget: $45-50/mois

$ENVIRONMENT_TYPE = "production"
$API_CPU = 1.0
$API_MEMORY = 2.0Gi
$API_MIN_REPLICAS = 1
$API_MAX_REPLICAS = 3
$WORKER_COUNT = 2
$QDRANT_CPU = 0.5
$QDRANT_MEMORY = 1.0Gi
$USE_AZURE_REDIS = $true
```

#### **Cas 4: Production Économique**

```powershell
# Budget: $25-30/mois (+40% performance vs Case 1)

$ENVIRONMENT_TYPE = "production-light"
$API_CPU = 0.75
$API_MEMORY = 1.5Gi
$API_MIN_REPLICAS = 1
$API_MAX_REPLICAS = 2
$WORKER_COUNT = 1
$QDRANT_CPU = 0.25
$QDRANT_MEMORY = 0.5Gi
$USE_AZURE_REDIS = $true
```

---

### 💡 Astuces supplémentaires

#### **1. Utiliser les Reserved Instances (1 an)**

```powershell
# Économie: ~30% sur les coûts

# Exemple:
# Pay-as-you-go: 1 CPU = $100/mois
# Reserved (1 year): 1 CPU = $70/mois
# Économie: $30/mois
```

#### **2. Réduire la taille du modèle CLIP**

Le modèle CLIP de base pèse ~500MB. Modèles plus légers:

```python
# Au lieu de: openai/clip-vit-base-patch32 (512-dim)
# Utiliser: openai/clip-vit-small-patch32 (384-dim, 30% plus léger)

# Dans config.py:
MODEL_NAME = "openai/clip-vit-small-patch32"

# Économie: -100MB disque, démarrage plus rapide
```

#### **3. Cleanup des images Docker non utilisées**

```powershell
# Supprimer les anciennes images dans ACR
az acr repository delete --name $REGISTRY_NAME --repository image-search-api --tags "v1" "v2"

# Économie: ~$2/mois (stockage ACR)
```

#### **4. Scaling intelligent**

```powershell
# Configurer le scaling pour réduire pendant les heures creuses
az containerapp update `
  --name $API_APP_NAME `
  --min-replicas 1 `
  --max-replicas 3 `
  --scale-rule-type http `
  --scale-rule-http-concurrency 50  # Trigger scale-up plus tard

# Économie: ~5-10% (moins de replicas inutiles)
```

#### **5. Monitoring des coûts**

```powershell
# Voir les coûts réels
az costmanagement query --metric BlendedCost --granularity Daily `
  --interval-from 2024-01-01 --interval-to 2024-01-31 `
  --timescale MonthToDate

# Ou utiliser le Portal Azure > Cost Management + Billing
```

---

### 📊 Résumé des coûts par configuration

| Configuration | API | Workers | Qdrant | Redis | **TOTAL/mois** |
|---------------|-----|---------|--------|-------|---|
| **Dev** | 0.25c | 0.25c | 0.25c | 0.25c | **$6-8** |
| **Staging** | 0.5c | 0.25c | 0.5c | Cloud | **$15-20** |
| **Production-Light** | 0.75c | 0.25c | 0.25c | Cloud | **$25-30** |
| **Production** | 1.0c | 0.5c | 0.5c | Cloud | **$45-50** |
| **Production+ (3 workers)** | 1.0c | 0.75c | 0.5c | Cloud | **$60-70** |

---

### ⚡ Déploiement avec configuration de coûts

```powershell
# Exemple: Déployer en mode "Production-Light"

$ENVIRONMENT_TYPE = "production-light"

if ($ENVIRONMENT_TYPE -eq "production-light") {
    $API_CPU = 0.75
    $API_MEMORY = 1.5Gi
    $API_MAX_REPLICAS = 2
    $WORKER_COUNT = 1
    $QDRANT_CPU = 0.25
    Write-Host "💰 Configuration: Production Économique (~$25-30/mois)"
}

# Ensuite utiliser les variables dans les deployments
```

---

## 🆘 Troubleshooting

### L'API ne démarre pas

```powershell
# 1. Vérifier les logs
az containerapp logs show --name $API_APP_NAME --resource-group $RESOURCE_GROUP --follow

# 2. Vérifier l'image Docker est correcte
docker run --rm -it "$LOGIN_SERVER/image-search-api:latest" python app/main.py

# 3. Vérifier que l'image contient tous les fichiers
docker run --rm -it "$LOGIN_SERVER/image-search-api:latest" ls -la /app

# 4. Reconstruire l'image
docker build --no-cache -t image-search-api:latest .
docker tag image-search-api:latest "$LOGIN_SERVER/image-search-api:latest"
docker push "$LOGIN_SERVER/image-search-api:latest"
```

### Erreur de connexion Redis

```powershell
# 1. Vérifier le statut Redis
az redis show --name $REDIS_NAME --resource-group $RESOURCE_GROUP

# 2. Vérifier les logs API
az containerapp logs show --name $API_APP_NAME --resource-group $RESOURCE_GROUP

# 3. Vérifier la URL Redis
Write-Host "Redis URL utilisée:"
Write-Host "redis://:$REDIS_KEY@$REDIS_HOST`:6380?ssl=True"

# 4. Vérifier les firewall rules
az redis firewall-rules list --name $REDIS_NAME --resource-group $RESOURCE_GROUP
```

### Erreur de connexion Qdrant

```powershell
# 1. Vérifier que Qdrant s'est démarré
az containerapp logs show --name $QDRANT_NAME --resource-group $RESOURCE_GROUP

# 2. Vérifier que l'API peut voir Qdrant
az containerapp logs show --name $API_APP_NAME --resource-group $RESOURCE_GROUP | Select-String "Qdrant"

# 3. Test de connexion depuis l'API
az containerapp exec --name $API_APP_NAME --resource-group $RESOURCE_GROUP --command "curl http://$QDRANT_NAME:6333/health"
```

### Les workers ne traitent pas les jobs

```powershell
# 1. Vérifier les logs des workers
az containerapp logs show --name $WORKER_1_NAME --resource-group $RESOURCE_GROUP --follow

# 2. Vérifier la connexion Redis
az containerapp logs show --name $WORKER_1_NAME --resource-group $RESOURCE_GROUP | Select-String "Redis"

# 3. Vérifier les jobs en attente
# (Dépend de votre implémentation Redis)
```

---

## 🧹 Cleanup (Supprimer les ressources)

### Option 1: Supprimer tout

```powershell
# ⚠️ ATTENTION: Cela supprimera TOUTES les ressources du groupe!

Write-Host "⚠️  Suppression du groupe de ressources: $RESOURCE_GROUP"
Write-Host "⚠️  Cela supprimera TOUTES les ressources créées!"

$confirm = Read-Host "Êtes-vous sûr? (yes/no)"

if ($confirm -eq "yes") {
    az group delete `
      --name $RESOURCE_GROUP `
      --yes `
      --no-wait
    
    Write-Host "✅ Suppression en cours..."
}
```

### Option 2: Supprimer seulement l'API

```powershell
# Garder Redis et Qdrant, supprimer seulement l'API
az containerapp delete `
  --name $API_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --yes

Write-Host "✅ API supprimée"
```

---

## 📊 Checklist Déploiement

- [ ] Azure CLI installé et `az login` exécuté
- [ ] Docker installé et fonctionnel
- [ ] Groupe de ressources créé
- [ ] Container Registry créé
- [ ] Image Docker poussée vers ACR
- [ ] Container App Environment créé
- [ ] Redis déployé et accessible
- [ ] Qdrant déployé et accessible
- [ ] API déployée et accessible publiquement
- [ ] Workers déployés
- [ ] Health check réussit
- [ ] Test de recherche réussit
- [ ] Logs visibles et accessibles
- [ ] Scaling configuré
- [ ] Variables d'env sécurisées

---

## 💰 Estimation des Coûts

### Calcul mensuel (730 heures)

```
API (1 CPU, 2GB RAM):      730h × $0.022/h  = $16/mois
Worker-1 (0.5 CPU, 1GB):   730h × $0.011/h  = $8/mois
Worker-2 (0.5 CPU, 1GB):   730h × $0.011/h  = $8/mois
Qdrant (0.5 CPU, 1GB):     730h × $0.011/h  = $8/mois
Redis (Basic 250MB):                         = $8/mois
─────────────────────────────────────────────────
TOTAL:                                        ≈ $48/mois
```

**Note:** Les pricing peuvent varier. Consultez [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)

---

## 📞 Support & Ressources

- [Documentation Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure CLI Docs](https://learn.microsoft.com/en-us/cli/azure/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Azure Cache for Redis](https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/)

---

**Besoin d'aide?** Consultez les logs avec `az containerapp logs show --name <app-name> --resource-group $RESOURCE_GROUP --follow`
