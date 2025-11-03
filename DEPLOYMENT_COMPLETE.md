# 🚀 Guide de Déploiement Complet - Image Search API

## 📋 Sommaire

1. [Architecture & Infrastructure](#architecture--infrastructure)
2. [Configuration Azure](#configuration-azure)
3. [Déploiement Pas à Pas](#déploiement-pas-à-pas)
4. [Vérification & Tests](#vérification--tests)
5. [Troubleshooting](#troubleshooting)

---

## Architecture & Infrastructure

### Infrastructure créée

```
┌─────────────────────────────────────────────────────────────────┐
│                    Azure Web App                                 │
│  image-search-api-123.azurewebsites.net                         │
│  (Python 3.11 - FastAPI)                                         │
└────────────────┬────────────────┬────────────────┬───────────────┘
                 │                │                │
        ┌────────▼────┐  ┌───────▼────┐  ┌────────▼─────┐
        │  Qdrant      │  │  Redis     │  │   App Config │
        │  Cloud       │  │  Cache     │  │   Settings   │
        │              │  │            │  │              │
        │ (AWS)        │  │ (Azure)    │  │              │
        └──────────────┘  └────────────┘  └──────────────┘
```

### Ressources Azure créées

| Ressource | Nom | Statut |
|-----------|-----|--------|
| Resource Group | ia-image-search-rg | ✅ Créé |
| App Service Plan | image-search-plan | ✅ Créé |
| Web App | image-search-api-123 | ✅ Créé |
| Redis Cache | image-search-redis-123 | ✅ Créé |

### Services externes

| Service | Configuration | Statut |
|---------|--------------|--------|
| Qdrant Cloud | URL AWS US-East-1 | ✅ Configuré |
| Redis Cache | Port 6380 (SSL) | ✅ Configuré |

---

## Configuration Azure

### Paramètres d'application configurés

```powershell
# Web App Settings (Vérifiez via:)
az webapp config appsettings list -g ia-image-search-rg -n image-search-api-123 -o table
```

**Valeurs actuelles:**

| Clé | Valeur | Type |
|-----|--------|------|
| QDRANT_HOST | https://ac6b684e-fca8-4ea1-92f0-6797a1db0133.us-east-1-1.aws.cloud.qdrant.io | External |
| QDRANT_API_KEY | eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... | Credentials |
| REDIS_HOST | image-search-redis-123.redis.cache.windows.net | Azure |
| REDIS_PORT | 6380 | Configuration |
| REDIS_PASSWORD | ***REDACTED*** | Credentials |
| ENVIRONMENT | production | Environment |
| WEBSITES_PORT | 8000 | FastAPI |
| SCM_DO_BUILD_DURING_DEPLOYMENT | true | Build |

---

## Déploiement Pas à Pas

### Étape 1: Préparer le code

```bash
cd iafrimallv100

# Vérifier que tout est commité
git status

# Créer une branche de déploiement (optionnel)
git checkout -b deploy/prod
```

### Étape 2: Configurer le git local (première fois seulement)

```powershell
# Ajouter le remote Azure
git remote add azure https://gestion-admin@image-search-api-123.scm.azurewebsites.net/image-search-api-123.git

# Vérifier le remote
git remote -v
```

### Étape 3: Pousser le code vers Azure

```powershell
# Déployer la branche main
git push azure main

# Ou si vous êtes sur une autre branche
git push azure <votre-branche>:main
```

### Étape 4: Vérifier le déploiement

```powershell
# Voir les logs de déploiement
az webapp log tail -g ia-image-search-rg -n image-search-api-123

# Ou directement via Kudu
# https://image-search-api-123.scm.azurewebsites.net/api/logs/docker
```

### Étape 5: Tester l'API

```bash
# Health check
curl https://image-search-api-123.azurewebsites.net/health

# Documentation interactive
# Ouvrir: https://image-search-api-123.azurewebsites.net/docs

# Test panel
# Ouvrir: https://image-search-api-123.azurewebsites.net/test
```

---

## Vérification & Tests

### 1. Vérifier l'état du Web App

```powershell
# État général
az webapp show -g ia-image-search-rg -n image-search-api-123

# Vérifier que c'est en fonctionnement
$app = az webapp show -g ia-image-search-rg -n image-search-api-123 --query "state" -o tsv
Write-Host "État: $app"  # Doit être "Running"
```

### 2. Tester les endpoints API

```bash
# Endpoint de santé
curl https://image-search-api-123.azurewebsites.net/health

# Documentation Swagger
curl https://image-search-api-123.azurewebsites.net/docs

# Info API
curl https://image-search-api-123.azurewebsites.net/
```

### 3. Test avec le panneau de test

Accédez à: **https://image-search-api-123.azurewebsites.net/test**

**Sections disponibles:**
- 🖼️ Image Search (URL ou upload)
- 📝 Text Search
- ➕ Index Product
- 🏥 Health Check
- ⚙️ Configuration
- 📋 Raw Request/Response

### 4. Vérifier la connectivité Redis

```powershell
# Depuis votre machine locale (si redis-cli est installé)
redis-cli -h image-search-redis-123.redis.cache.windows.net `
  -p 6380 `
  -a "***REDACTED***" `
  --tls ping

# Résultat attendu: PONG
```

### 5. Vérifier les logs Azure

```powershell
# Logs applicatifs
az webapp log tail -g ia-image-search-rg -n image-search-api-123 --provider Application

# Logs Docker
az webapp log tail -g ia-image-search-rg -n image-search-api-123 --provider Docker
```

---

## Troubleshooting

### Erreur: "Git deployment failed"

```powershell
# Vérifier l'URL du remote
git remote -v

# Corriger si nécessaire
git remote set-url azure https://gestion-admin@image-search-api-123.scm.azurewebsites.net/image-search-api-123.git

# Réessayer
git push azure main
```

### Erreur: "Connection to Redis failed"

```powershell
# Vérifier que Redis est démarré
az redis show -g ia-image-search-rg -n image-search-redis-123

# Vérifier les paramètres d'application
az webapp config appsettings list -g ia-image-search-rg -n image-search-api-123

# Les credentials doivent être corrects
```

### Erreur: "Qdrant connection refused"

```powershell
# Vérifier les paramètres Qdrant
az webapp config appsettings show -g ia-image-search-rg -n image-search-api-123 --setting-names QDRANT_HOST,QDRANT_API_KEY

# Les valeurs doivent être:
# QDRANT_HOST: https://ac6b684e-fca8-4ea1-92f0-6797a1db0133.us-east-1-1.aws.cloud.qdrant.io
# QDRANT_API_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### L'API démarre mais revient au timeout

```powershell
# Vérifier les logs
az webapp log tail -g ia-image-search-rg -n image-search-api-123

# Augmenter le startup time
az webapp config set -g ia-image-search-rg -n image-search-api-123 --startup-command "gunicorn app.main:app --workers 1 --timeout 600"
```

### 500 Internal Server Error

```powershell
# Vérifier les logs détaillés
az webapp log tail -g ia-image-search-rg -n image-search-api-123

# Vérifier les variables d'environnement
az webapp config appsettings list -g ia-image-search-rg -n image-search-api-123 -o json | ConvertFrom-Json

# Vérifier que REDIS_PASSWORD est correct (sans espace)
```

---

## Commandes Utiles

### Gestion du Web App

```powershell
# Redémarrer
az webapp restart -g ia-image-search-rg -n image-search-api-123

# Arrêter
az webapp stop -g ia-image-search-rg -n image-search-api-123

# Démarrer
az webapp start -g ia-image-search-rg -n image-search-api-123

# Supprimer
az webapp delete -g ia-image-search-rg -n image-search-api-123
```

### Gestion des paramètres

```powershell
# Lister tous les paramètres
az webapp config appsettings list -g ia-image-search-rg -n image-search-api-123

# Ajouter/modifier un paramètre
az webapp config appsettings set -g ia-image-search-rg -n image-search-api-123 --settings KEY=VALUE

# Supprimer un paramètre
az webapp config appsettings delete -g ia-image-search-rg -n image-search-api-123 --setting-names KEY
```

### Gestion du cache Redis

```powershell
# Afficher les infos Redis
az redis show -g ia-image-search-rg -n image-search-redis-123

# Obtenir les clés d'accès
az redis list-keys -g ia-image-search-rg -n image-search-redis-123

# Regénérer les clés
az redis regenerate-keys -g ia-image-search-rg -n image-search-redis-123 --key-type Primary
```

---

## Checklist de déploiement final

- [ ] Web App créée: image-search-api-123
- [ ] Redis créé: image-search-redis-123
- [ ] Tous les paramètres d'application configurés
- [ ] Code poussé vers Azure via Git
- [ ] API démarre sans erreur (vérifier logs)
- [ ] Health check retourne 200
- [ ] Test panel accessible et fonctionnel
- [ ] Recherche par image fonctionne
- [ ] Recherche par texte fonctionne
- [ ] Cache Redis fonctionne
- [ ] Logs ne montrent pas d'erreur

---

## URLs de production

```
API: https://image-search-api-123.azurewebsites.net
Docs: https://image-search-api-123.azurewebsites.net/docs
Health: https://image-search-api-123.azurewebsites.net/health
Test: https://image-search-api-123.azurewebsites.net/test
```

---

**Statut**: ✅ Infrastructure prête pour déploiement  
**Date**: November 3, 2025  
**Version**: 1.0
