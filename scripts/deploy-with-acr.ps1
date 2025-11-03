# Deploy using Azure Container Registry (ACR)
# This avoids the slow build on Azure Web App

# Step 1: Create ACR (if not exists)
$acrName = "iafrimallacr"
$rgName = "ia-image-search-rg"
$location = "francecentral"

Write-Host "1️⃣ Creating Azure Container Registry..."
az acr create -g $rgName -n $acrName --sku Basic --location $location

# Step 2: Build image locally
Write-Host "2️⃣ Building Docker image locally..."
cd C:\Users\hynco\Desktop\iaafrimall\iafrimallv100
docker build -t $acrName`.azurecr.io/image-search-api:latest .

# Step 3: Login to ACR
Write-Host "3️⃣ Logging in to ACR..."
az acr login --name $acrName

# Step 4: Push image to ACR
Write-Host "4️⃣ Pushing image to ACR..."
docker push $acrName`.azurecr.io/image-search-api:latest

# Step 5: Create or update Web App to use ACR image
Write-Host "5️⃣ Configuring Web App for ACR..."
az webapp config container set -g $rgName -n image-search-api-123 `
  --docker-custom-image-name $acrName`.azurecr.io/image-search-api:latest `
  --docker-registry-server-url https://$acrName`.azurecr.io `
  --docker-registry-server-user (az acr credential show -n $acrName -o tsv --query username) `
  --docker-registry-server-password (az acr credential show -n $acrName -o tsv --query "passwords[0].value")

Write-Host "✅ Deployment complete! Check https://image-search-api-123.azurewebsites.net"
