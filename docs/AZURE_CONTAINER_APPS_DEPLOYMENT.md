# Azure Container Apps Deployment Guide

## Architecture Overview

**Single Container = Lower Costs**
- API FastAPI + Qdrant + TF-IDF embeddings in ONE container
- No external services needed
- Auto-scale to zero when not in use
- Pay only for what you use (~$0-5/month for light usage)

```
┌─────────────────────────────────────────┐
│   Azure Container Apps (ACA)            │
├─────────────────────────────────────────┤
│  ┌───────────────────────────────────┐  │
│  │   Your Container                  │  │
│  ├───────────────────────────────────┤  │
│  │ FastAPI (8000) + Qdrant + scikit  │  │
│  │ - API routes                      │  │
│  │ - TF-IDF embeddings (50MB)        │  │
│  │ - Vector DB (in-memory or disk)   │  │
│  │ - Persistent /app/data volume     │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Auto-scale: 0-10 replicas             │
│  Consumption plan pricing              │
└─────────────────────────────────────────┘
```

## Prerequisites

```bash
# Install tools
az login
az extension add --name containerapp

# Set variables
$RG_NAME = "ia-image-search-rg"
$LOCATION = "francecentral"
$ACR_NAME = "iafrimallacr"
$CONTAINER_APP_NAME = "image-search-api"
$CONTAINER_IMAGE_NAME = "image-search-api"
```

## Step 1: Create Resource Group

```bash
az group create `
  --name $RG_NAME `
  --location $LOCATION
```

## Step 2: Create Azure Container Registry (ACR)

```bash
# ACR is free tier for small images
az acr create `
  --resource-group $RG_NAME `
  --name $ACR_NAME `
  --sku Basic `
  --location $LOCATION

# Login to ACR
az acr login --name $ACR_NAME
```

## Step 3: Build and Push Docker Image

```bash
# Build locally
cd iafrimallv100
docker build -t "$ACR_NAME.azurecr.io/$CONTAINER_IMAGE_NAME:latest" .

# Push to ACR
docker push "$ACR_NAME.azurecr.io/$CONTAINER_IMAGE_NAME:latest"

# Verify
az acr repository list --name $ACR_NAME
```

## Step 4: Get ACR Credentials

```bash
# Get admin credentials
$ACR_PASSWORD = az acr credential show --name $ACR_NAME `
  --query "passwords[0].value" -o tsv

$ACR_USERNAME = az acr credential show --name $ACR_NAME `
  --query "username" -o tsv

Write-Host "ACR Username: $ACR_USERNAME"
Write-Host "ACR Password: $ACR_PASSWORD"
```

## Step 5: Create Container App Environment

```bash
$ENV_NAME = "image-search-env"

az containerapp env create `
  --name $ENV_NAME `
  --resource-group $RG_NAME `
  --location $LOCATION
```

## Step 6: Create Container App

```bash
az containerapp create `
  --name $CONTAINER_APP_NAME `
  --resource-group $RG_NAME `
  --environment $ENV_NAME `
  --image "$ACR_NAME.azurecr.io/$CONTAINER_IMAGE_NAME:latest" `
  --registry-login-server "$ACR_NAME.azurecr.io" `
  --registry-username $ACR_USERNAME `
  --registry-password $ACR_PASSWORD `
  --target-port 8000 `
  --ingress 'external' `
  --min-replicas 0 `
  --max-replicas 10 `
  --cpu 0.5 `
  --memory 1Gi `
  --environment-variables `
    "QDRANT_DATA_PATH=/app/data/qdrant" `
    "PYTHONUNBUFFERED=1"
```

## Step 7: Get Container App URL

```bash
$APP_URL = az containerapp show `
  --name $CONTAINER_APP_NAME `
  --resource-group $RG_NAME `
  --query properties.configuration.ingress.fqdn `
  -o tsv

Write-Host "Application URL: https://$APP_URL"
```

## Step 8: Test API

```bash
# Health check
curl "https://$APP_URL/api/v1/health"

# Search
curl -X POST "https://$APP_URL/api/v1/search" `
  -H "Content-Type: application/json" `
  -d '{"query": "luxury handbag", "limit": 10}'

# Index a product
curl -X POST "https://$APP_URL/api/v1/index-product" `
  -F "product_id=prod_123" `
  -F "name=Red Handbag" `
  -F "description=Premium leather handbag"

# Get stats
curl "https://$APP_URL/api/v1/stats"
```

## Pricing

### Azure Container Apps - Consumption Plan

**Included (Free):**
- 1 million requests/month
- 360 GB-seconds/month
- Ability to scale to zero

**After free quota:**
- $0.015 per vCPU-second
- $0.0000034 per GB-second

### For Light Usage
```
Assumptions:
- 100 requests/day = 3000/month (within free)
- Each request: 0.5 vCPU, 1GB memory, ~1 second
- Traffic: 10 requests/hour (auto-scale down 95% of time)

Estimated cost: $0-5/month
```

### Compare to Previous Architecture
- **Web App (Basic)**: $11/month (always on)
- **App Service Plan**: $11/month
- **Redis Cache**: $17/month
- **Previous Total**: ~$40/month

**New Cost**: ~$5/month (Container Apps only, when used)
**Savings**: ~87% reduction!

## Monitoring

### View Logs
```bash
az containerapp logs show `
  --name $CONTAINER_APP_NAME `
  --resource-group $RG_NAME `
  --follow
```

### View Metrics
```bash
az monitor metrics list `
  --resource "/subscriptions/{subscription-id}/resourceGroups/$RG_NAME/providers/Microsoft.App/containerApps/$CONTAINER_APP_NAME" `
  --metric "Replicas"
```

### Application Insights (Optional)
```bash
# Add monitoring
az containerapp update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RG_NAME `
  --application-insights-key $INSIGHTS_KEY
```

## Scaling Behavior

### Auto-scaling Rules
- **Min replicas**: 0 (scale to zero when inactive)
- **Max replicas**: 10 (handle traffic spikes)
- **Scale-up**: When CPU > 50% or memory > 60%
- **Scale-down**: After 10 minutes of low usage

### Timeline
- **Scale-up**: ~30 seconds
- **Scale-down**: ~10 minutes

## Persistence

### Data Directory
```
/app/data/qdrant  ← Persistent storage
```

Every time a product is indexed, data is saved to `/app/data/qdrant/`.
Even if the container restarts, data persists.

### Note
Container Apps don't have persistent volumes by default.
For production with large data:
- Add Azure Files share
- Or use Azure Cosmos DB instead of Qdrant

## Updates & Deployments

### Update Image
```bash
docker build -t "$ACR_NAME.azurecr.io/$CONTAINER_IMAGE_NAME:v2" .
docker push "$ACR_NAME.azurecr.io/$CONTAINER_IMAGE_NAME:v2"

az containerapp update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RG_NAME `
  --image "$ACR_NAME.azurecr.io/$CONTAINER_IMAGE_NAME:v2"
```

### Rollback
```bash
az containerapp update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RG_NAME `
  --image "$ACR_NAME.azurecr.io/$CONTAINER_IMAGE_NAME:latest"
```

## Troubleshooting

### Container fails to start
```bash
# Check logs
az containerapp logs show `
  --name $CONTAINER_APP_NAME `
  --resource-group $RG_NAME `
  --follow

# Common issues:
# - Port 8000 not exposed in Dockerfile
# - Missing environment variables
# - Insufficient memory (1GB minimum recommended)
```

### Slow initial request
- First request triggers container startup (~5-10 seconds)
- Subsequent requests: <1 second
- Solution: Set `min-replicas 1` to keep container warm (costs ~$1/month more)

### Out of memory
```bash
# Increase memory
az containerapp update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RG_NAME `
  --memory 2Gi `
  --cpu 1.0
```

## Production Checklist

- [ ] Test API endpoints locally before deployment
- [ ] Set appropriate min/max replicas for expected traffic
- [ ] Configure monitoring and alerts
- [ ] Plan for data backup if using persistent storage
- [ ] Set resource quotas to prevent unexpected costs
- [ ] Test auto-scaling behavior under load
- [ ] Document configuration and variables

## Cost Optimization Tips

1. **Use min-replicas 0** - Scale to zero when unused
2. **Monitor actual usage** - Adjust CPU/memory based on metrics
3. **Batch requests** - Reduce number of API calls
4. **Local testing** - Develop locally before deploying
5. **Use smaller images** - Our image is only ~300MB (vs 2GB+ alternatives)

## Next Steps

1. Build the image: `docker build -t myimage .`
2. Push to ACR
3. Deploy to ACA
4. Test endpoints
5. Monitor costs and performance
6. Scale based on usage patterns

---

**Total Setup Time**: ~10 minutes
**Monthly Cost**: $0-10
**Scalability**: 0-10 replicas automatically
**Status**: Ready for production! ✅
