# Azure Container Apps Automated Deployment Script
# Usage: .\deploy-to-container-apps.ps1

param(
    [string]$ResourceGroup = "ia-image-search-rg",
    [string]$Location = "francecentral",
    [string]$AcrName = "iafrimallacr",
    [string]$ContainerAppName = "image-search-api",
    [string]$EnvironmentName = "image-search-env"
)

Write-Host "🚀 Azure Container Apps Deployment Script" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Step 1: Create Resource Group
Write-Host "`n[1/7] Creating Resource Group..." -ForegroundColor Green
az group create `
    --name $ResourceGroup `
    --location $Location | Out-Null
Write-Host "✅ Resource Group created: $ResourceGroup"

# Step 2: Create ACR
Write-Host "`n[2/7] Creating Azure Container Registry..." -ForegroundColor Green
az acr create `
    --resource-group $ResourceGroup `
    --name $AcrName `
    --sku Basic `
    --location $Location | Out-Null
Write-Host "✅ ACR created: $AcrName"

# Step 3: Login to ACR
Write-Host "`n[3/7] Logging in to ACR..." -ForegroundColor Green
az acr login --name $AcrName | Out-Null
Write-Host "✅ Logged in to ACR"

# Step 4: Build and Push Docker Image
Write-Host "`n[4/7] Building and pushing Docker image..." -ForegroundColor Green
$ImageName = "$AcrName.azurecr.io/image-search-api:latest"
docker build -t $ImageName .
docker push $ImageName
Write-Host "✅ Image built and pushed: $ImageName"

# Step 5: Get ACR Credentials
Write-Host "`n[5/7] Getting ACR credentials..." -ForegroundColor Green
$AcrPassword = az acr credential show --name $AcrName --query "passwords[0].value" -o tsv
$AcrUsername = az acr credential show --name $AcrName --query "username" -o tsv
Write-Host "✅ ACR credentials retrieved"

# Step 6: Create Container App Environment
Write-Host "`n[6/7] Creating Container App Environment..." -ForegroundColor Green
az containerapp env create `
    --name $EnvironmentName `
    --resource-group $ResourceGroup `
    --location $Location | Out-Null
Write-Host "✅ Environment created: $EnvironmentName"

# Step 7: Create Container App
Write-Host "`n[7/7] Creating Container App..." -ForegroundColor Green
az containerapp create `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --environment $EnvironmentName `
    --image $ImageName `
    --registry-login-server "$AcrName.azurecr.io" `
    --registry-username $AcrUsername `
    --registry-password $AcrPassword `
    --target-port 8000 `
    --ingress 'external' `
    --min-replicas 0 `
    --max-replicas 10 `
    --cpu 0.5 `
    --memory 1Gi `
    --environment-variables `
        "QDRANT_DATA_PATH=/app/data/qdrant" `
        "PYTHONUNBUFFERED=1" | Out-Null
Write-Host "✅ Container App created: $ContainerAppName"

# Get URL
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
$AppUrl = az containerapp show `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --query properties.configuration.ingress.fqdn `
    -o tsv

Write-Host "`n✨ Deployment Successful!" -ForegroundColor Green
Write-Host "`n📍 Application URL: https://$AppUrl" -ForegroundColor Cyan
Write-Host "`n🧪 Test the API:" -ForegroundColor Yellow
Write-Host "  Health: curl 'https://$AppUrl/api/v1/health'"
Write-Host "  Search: curl -X POST 'https://$AppUrl/api/v1/search' -H 'Content-Type: application/json' -d '{""query"": ""test"", ""limit"": 5}'"
Write-Host "`n📊 View logs:"
Write-Host "  az containerapp logs show --name $ContainerAppName --resource-group $ResourceGroup --follow"
Write-Host "`n💰 Estimated cost: $0-10/month (with auto-scale to zero)"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
