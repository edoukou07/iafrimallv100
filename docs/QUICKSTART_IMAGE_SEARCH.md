# 🚀 Déploiement Image Search sur Azure - Guide Rapide

## ⏱️ Temps total: 10-15 minutes

## Prérequis

```powershell
# 1. Vérifier Azure CLI
az version

# 2. Vérifier Docker
docker --version

# 3. S'authentifier à Azure
az login
```

## Étape 1: Préparation Locale (2 min)

```powershell
cd c:\Users\hynco\Desktop\iaafrimall\iafrimallv100

# Test local rapide
python -m uvicorn app.main:app --reload &

# Dans un autre terminal
python test_image_search.py

# Si OK → Ctrl+C pour arrêter le serveur local
```

**Attendu:** Tous les tests passent ✅

## Étape 2: Configuration Azure (3 min)

Définir variables:

```powershell
$resourceGroup = "ia-image-search-rg"
$location = "eastus"
$containerApp = "image-search-api"
$acrName = "iafrimallacr"
$imageName = "image-search:latest"

# Créer resource group
az group create --name $resourceGroup --location $location
```

## Étape 3: Créer Azure Container Registry (2 min)

```powershell
# Créer ACR
az acr create `
  --resource-group $resourceGroup `
  --name $acrName `
  --sku Basic

# Activer admin user pour push
az acr update `
  --name $acrName `
  --admin-enabled true

# Récupérer credentials
$credentials = az acr credential show --name $acrName --query "passwords[0]"
$password = ($credentials | ConvertFrom-Json).value
$username = $acrName
$loginServer = "$acrName.azurecr.io"
```

## Étape 4: Build et Push Image Docker (4 min)

```powershell
# Build image localement
docker build -t $imageName .

# Tag pour ACR
docker tag $imageName "${loginServer}/${imageName}"

# Login to ACR
az acr login --name $acrName

# Push to Azure
docker push "${loginServer}/${imageName}"

# Vérifier
az acr repository list --name $acrName
```

**Attendu:** Image ~500MB uploadée vers ACR

## Étape 5: Créer Azure Container App (5 min)

```powershell
# Créer environment
$containerAppEnv = "image-search-env"

az containerapp env create `
  --name $containerAppEnv `
  --resource-group $resourceGroup `
  --location $location

# Déployer app
az containerapp create `
  --name $containerApp `
  --resource-group $resourceGroup `
  --environment $containerAppEnv `
  --image "${loginServer}/${imageName}" `
  --target-port 8000 `
  --ingress external `
  --min-replicas 0 `
  --max-replicas 10 `
  --cpu "0.5" `
  --memory "1Gi" `
  --registry-server $loginServer `
  --registry-username $username `
  --registry-password $password
```

## Étape 6: Récupérer URL de l'API (1 min)

```powershell
# Obtenir URL publique
$appUrl = az containerapp show `
  --name $containerApp `
  --resource-group $resourceGroup `
  --query "properties.configuration.ingress.fqdn" `
  -o tsv

Write-Host "API URL: https://$appUrl"

# Test API
curl "https://$appUrl/api/v1/health"
```

**Attendu:** Réponse JSON avec `"status": "running"`

## Étape 7: Tester Endpoints (3 min)

### Test 1: Health Check

```powershell
$baseUrl = "https://$appUrl"

# GET health
Invoke-RestMethod -Uri "$baseUrl/api/v1/health"
```

### Test 2: Image Embedding

```powershell
# Créer image test (rouge)
$imagePath = "test_image.jpg"

# Télécharger une image de test ou en créer une

# POST image embedding
$form = @{
    file = Get-Item $imagePath
}

Invoke-RestMethod -Uri "$baseUrl/api/v1/embed-image" `
    -Method Post `
    -Form $form
```

### Test 3: Index Produit avec Image

```powershell
$form = @{
    product_id = "dress_001"
    name = "Beautiful Red Dress"
    description = "Summer dress in red"
    image_file = Get-Item $imagePath
    metadata = '{"price": 49.99}'
}

Invoke-RestMethod -Uri "$baseUrl/api/v1/index-product-with-image" `
    -Method Post `
    -Form $form
```

### Test 4: Recherche par Image

```powershell
$form = @{
    file = Get-Item $imagePath
}

Invoke-RestMethod -Uri "$baseUrl/api/v1/search-image?limit=10" `
    -Method Post `
    -Form $form
```

## Monitoring

### Logs en temps réel

```powershell
az containerapp logs show `
  --name $containerApp `
  --resource-group $resourceGroup `
  --follow
```

### Statistiques

```powershell
az containerapp show `
  --name $containerApp `
  --resource-group $resourceGroup `
  --query "properties.{status: provisioningState, replicas: template.scale.maxReplicas}"
```

### Santé Container

```powershell
az containerapp logs show `
  --name $containerApp `
  --resource-group $resourceGroup `
  --container-name $containerApp
```

## 💰 Coûts Estimés

| Service | Coût/mois |
|---------|-----------|
| Container Apps (0.5 CPU, 1GB RAM) | $5-15* |
| Container Registry | Gratuit (Basic tier) |
| Stockage (50GB data) | $1 |
| **Total** | **$6-16/mois** |

*Dépend de l'utilisation (auto-scale à 0 quand inactif)

## Cleanup (Optionnel)

```powershell
# Supprimer tout
az group delete --name $resourceGroup --yes

# Vérification
az group list --query "[?name=='$resourceGroup']"
```

## Dépannage

### API Timeout

```powershell
# Vérifier replicas
az containerapp show --name $containerApp --resource-group $resourceGroup `
  --query "properties.template.scale.maxReplicas"

# Augmenter réplicas
az containerapp update --name $containerApp --resource-group $resourceGroup `
  --min-replicas 1 `
  --max-replicas 20
```

### Image Embedding Fail

```powershell
# Vérifier logs
az containerapp logs show --name $containerApp --resource-group $resourceGroup --follow

# Redémarrer
az containerapp restart --name $containerApp --resource-group $resourceGroup
```

### Accès denied ACR

```powershell
# Réactiver admin
az acr update --name $acrName --admin-enabled true

# Régénérer credentials
az acr credential renew --name $acrName --password-name password
```

## Prochaines Étapes

1. ✅ API image search opérationnelle
2. 🔄 Indexer vos produits réels avec images
3. 📊 Monitoring avec Application Insights
4. 🔒 Ajouter Azure AD authentication
5. 🚀 CI/CD pipeline GitHub Actions

## Support

Pour plus de détails, voir:
- 📖 `docs/IMAGE_SEARCH_PIPELINE.md`
- 📖 `docs/AZURE_CONTAINER_APPS_DEPLOYMENT.md`
- 📖 `docs/README.md`

---

**API live en ~15 min, coûts de $6-16/mois, auto-scaling à zéro!** 🎉
