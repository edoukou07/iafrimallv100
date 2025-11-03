# ============================================================================
# SCRIPT DE DÉPLOIEMENT AZURE - IMAGE SEARCH API
# ============================================================================
# 
# Usage: ./deploy-to-azure.ps1 -AppName "image-search-api-123"
#
# ============================================================================

param(
    [Parameter(Mandatory = $true)]
    [string]$AppName,
    
    [Parameter(Mandatory = $false)]
    [string]$ResourceGroup = "image-search-rg",
    
    [Parameter(Mandatory = $false)]
    [string]$Location = "eastus",
    
    [Parameter(Mandatory = $false)]
    [string]$Plan = "image-search-plan",
    
    [Parameter(Mandatory = $false)]
    [string]$RedisName = "image-search-redis-123",
    
    [Parameter(Mandatory = $false)]
    [string]$QdrantUrl = "https://ac6b684e-fca8-4ea1-92f0-6797a1db0133.us-east-1-1.aws.cloud.qdrant.io:6333",
    
    [Parameter(Mandatory = $false)]
    [string]$QdrantApiKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.8FsGYG2IrFUN8olrsdqDwdzrqJHivOQwPgyK2RMaIqI"
)

# ============================================================================
# COULEURS POUR AFFICHAGE
# ============================================================================

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-ErrorCustom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-InfoCustom {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-WarningCustom {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

# ============================================================================
# VERIFICATIONS PREALABLES
# ============================================================================

Write-InfoCustom "===================================================================="
Write-InfoCustom "Verification des prerequis..."
Write-InfoCustom "===================================================================="

# Verifier Azure CLI
try {
    $azVersion = az --version 2>$null | Select-Object -First 1
    Write-Success "Azure CLI trouve: $azVersion"
}
catch {
    Write-ErrorCustom "Azure CLI non trouve. Installez-le: https://aka.ms/azure-cli"
    exit 1
}

# Verifier connexion Azure
try {
    $account = az account show 2>$null | ConvertFrom-Json
    Write-Success "Connecte a Azure: $($account.user.name)"
}
catch {
    Write-WarningCustom "Pas connecte a Azure. Execution de 'az login'..."
    az login
}

# Verifier Git
try {
    $gitVersion = git --version
    Write-Success "Git trouve: $gitVersion"
}
catch {
    Write-ErrorCustom "Git non trouve. Installez-le: https://git-scm.com/"
    exit 1
}

# ============================================================================
# ETAPE 1: GROUPE DE RESSOURCES
# ============================================================================

Write-InfoCustom "===================================================================="
Write-InfoCustom "Creation/Verification du groupe de ressources: $ResourceGroup"
Write-InfoCustom "===================================================================="

$rg = az group show --name $ResourceGroup 2>$null
if (-not $rg) {
    Write-InfoCustom "Creation du groupe de ressources..."
    az group create --name $ResourceGroup --location $Location | Out-Null
    Write-Success "Groupe de ressources cree!"
}
else {
    Write-Success "Groupe de ressources existe deja!"
}

# ============================================================================
# ETAPE 2: APP SERVICE PLAN
# ============================================================================

Write-InfoCustom "===================================================================="
Write-InfoCustom "Creation/Verification du plan App Service: $Plan (B1)"
Write-InfoCustom "===================================================================="

$existingPlan = az appservice plan show --name $Plan --resource-group $ResourceGroup 2>$null
if (-not $existingPlan) {
    Write-InfoCustom "Creation du plan B1..."
    az appservice plan create --name $Plan `
        --resource-group $ResourceGroup `
        --sku B1 `
        --is-linux | Out-Null
    Write-Success "Plan App Service cree! (Cout: $13.20/mois)"
}
else {
    Write-Success "Plan App Service existe deja!"
}

# ============================================================================
# ETAPE 3: WEB APP
# ============================================================================

Write-InfoCustom "===================================================================="
Write-InfoCustom "Creation/Verification de l'App Service: $AppName"
Write-InfoCustom "===================================================================="

$existingApp = az webapp show --name $AppName --resource-group $ResourceGroup 2>$null
if (-not $existingApp) {
    Write-InfoCustom "Creation de l'application..."
    az webapp create --resource-group $ResourceGroup `
        --plan $Plan `
        --name $AppName `
        --runtime "PYTHON|3.11" `
        --deployment-local-git | Out-Null
    Write-Success "Application creee!"
}
else {
    Write-Success "Application existe deja!"
}

# ============================================================================
# ETAPE 4: REDIS
# ============================================================================

Write-InfoCustom "===================================================================="
Write-InfoCustom "Creation/Verification d'Azure Cache for Redis"
Write-InfoCustom "===================================================================="

$existingRedis = az redis show --name $RedisName --resource-group $ResourceGroup 2>$null
if (-not $existingRedis) {
    Write-WarningCustom "Creation de Redis... (cela peut prendre 5-10 minutes)"
    az redis create --resource-group $ResourceGroup `
        --name $RedisName `
        --location $Location `
        --sku basic `
        --vm-size c0 `
        --enable-non-ssl-port true | Out-Null
    Write-Success "Azure Cache Redis cree! (Cout: $15.30/mois)"
}
else {
    Write-Success "Azure Cache Redis existe deja!"
}

# Recuperer les details Redis
$redis = az redis show --name $RedisName --resource-group $ResourceGroup | ConvertFrom-Json
$redisHost = $redis.hostName
$redisPort = $redis.port

$redisKeys = az redis list-keys --name $RedisName --resource-group $ResourceGroup | ConvertFrom-Json
$redisPassword = $redisKeys.primaryKey

Write-Success "Redis Host: $redisHost"
Write-Success "Redis Port: $redisPort"

# ============================================================================
# ETAPE 5: CONFIGURATION VARIABLES D'ENVIRONNEMENT
# ============================================================================

Write-InfoCustom "===================================================================="
Write-InfoCustom "Configuration des variables d'environnement"
Write-InfoCustom "===================================================================="

# Si Qdrant URL fournie
if ($QdrantUrl -and $QdrantApiKey) {
    Write-InfoCustom "Configuration avec Qdrant Cloud..."
    
    az webapp config appsettings set `
        --resource-group $ResourceGroup `
        --name $AppName `
        --settings `
            QDRANT_HOST="$QdrantUrl" `
            QDRANT_API_KEY="$QdrantApiKey" `
            REDIS_HOST="$redisHost" `
            REDIS_PORT="$redisPort" `
            REDIS_PASSWORD="$redisPassword" `
            CACHE_TTL="3600" `
            ENVIRONMENT="production" `
            WEBSITES_PORT="8000" `
            SCM_DO_BUILD_DURING_DEPLOYMENT="true" | Out-Null
    
    Write-Success "Variables d'environnement configurees!"
}
else {
    Write-WarningCustom "Qdrant URL ou API Key manquante!"
    Write-InfoCustom "Vous devrez les ajouter manuellement:"
    Write-InfoCustom "  1. Aller sur: https://cloud.qdrant.io"
    Write-InfoCustom "  2. Creer un cluster gratuit"
    Write-InfoCustom "  3. Copier l'URL et la cle API"
    Write-InfoCustom "  4. Executer cette commande avec vos valeurs:"
    Write-Host "     az webapp config appsettings set -g image-search-rg -n <APP_NAME> --settings QDRANT_HOST='https://xxxxx-qdrant.io' QDRANT_API_KEY='your-api-key' REDIS_HOST='<REDIS_HOST>' REDIS_PORT='6379' REDIS_PASSWORD='<REDIS_PASSWORD>'" -ForegroundColor Yellow
}

# ============================================================================
# ETAPE 6: CONFIGURATION STARTUP
# ============================================================================

Write-InfoCustom "===================================================================="
Write-InfoCustom "Configuration du startup command"
Write-InfoCustom "===================================================================="

az webapp config set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --startup-file "startup.sh" | Out-Null

Write-Success "Startup command configure!"

# ============================================================================
# ETAPE 7: CONFIGURATION GIT
# ============================================================================

Write-InfoCustom "===================================================================="
Write-InfoCustom "Configuration du deploiement Git"
Write-InfoCustom "===================================================================="

$gitUrl = az webapp deployment source config-local-git `
    --resource-group $ResourceGroup `
    --name $AppName | ConvertFrom-Json | Select-Object -ExpandProperty url

Write-Success "URL Git de deploiement:"
Write-Host $gitUrl -ForegroundColor Cyan

# Ajouter remote
Write-InfoCustom "Ajout du remote Azure a votre repository Git..."
git remote remove azure 2>$null
git remote add azure $gitUrl

Write-Success "Remote Git 'azure' ajoute!"

# ============================================================================
# ETAPE 8: DEPLOIEMENT
# ============================================================================

Write-InfoCustom "===================================================================="
Write-InfoCustom "Deploiement du code..."
Write-InfoCustom "===================================================================="

Write-InfoCustom "Initialisation Git (si necessaire)..."
if (-not (git status 2>$null)) {
    git init
    git add .
    git commit -m "Initial commit for Azure deployment"
}

Write-InfoCustom "Push vers Azure (cela peut prendre quelques minutes)..."
git push azure (git rev-parse --abbrev-ref HEAD):main

Write-Success "Code deploye!"

# ============================================================================
# ETAPE 9: VERIFICATION
# ============================================================================

Write-InfoCustom "===================================================================="
Write-InfoCustom "Verification du deploiement..."
Write-InfoCustom "===================================================================="

Write-WarningCustom "Attendre 2-3 minutes pour que l'app demarre..."
Start-Sleep -Seconds 3

Write-InfoCustom "Affichage des 20 dernieres lignes de log..."
Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor Gray

$logs = az webapp log tail --name $AppName --resource-group $ResourceGroup --lines 20
Write-Host $logs

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================

$appUrl = "https://$AppName.azurewebsites.net"

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "DEPLOIEMENT COMPLETE AVEC SUCCES!" -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Green

Write-Host ""
Write-Success "URL de votre API:"
Write-Host $appUrl -ForegroundColor Cyan

Write-Success "Documentation interactive (Swagger):"
Write-Host "$appUrl/docs" -ForegroundColor Cyan

Write-Success "Health check:"
Write-Host "$appUrl/api/v1/health" -ForegroundColor Cyan

Write-Host ""
Write-Success "Couts estimes:"
Write-Host "  - App Service B1: 13.20/mois" -ForegroundColor White
Write-Host "  - Redis Basic: 15.30/mois" -ForegroundColor White
Write-Host "  - Qdrant Cloud: 0.00/mois (gratuit)" -ForegroundColor White
Write-Host "  ────────────────────────────────" -ForegroundColor White
Write-Host "  - TOTAL: ~31/mois" -ForegroundColor Yellow

Write-Host ""
Write-InfoCustom "Commandes utiles:"
Write-Host "  Voir les logs:" -ForegroundColor White
Write-Host "  az webapp log tail --name $AppName --resource-group $ResourceGroup --follow" -ForegroundColor Gray
Write-Host ""
Write-Host "  Redemarrer l'app:" -ForegroundColor White
Write-Host "  az webapp restart --name $AppName --resource-group $ResourceGroup" -ForegroundColor Gray
Write-Host ""
Write-Host "  Voir les variables:" -ForegroundColor White
Write-Host "  az webapp config appsettings list --name $AppName --resource-group $ResourceGroup" -ForegroundColor Gray

Write-Host ""
Write-WarningCustom "A faire maintenant:"
Write-Host "  1. [ ] Creer un cluster Qdrant sur https://cloud.qdrant.io" -ForegroundColor White
Write-Host "  2. [ ] Copier l'URL et la cle API" -ForegroundColor White
Write-Host "  3. [ ] Mettre a jour les variables d'environnement:" -ForegroundColor White

$cmdExample = "az webapp config appsettings set -g $ResourceGroup -n $AppName --settings QDRANT_HOST=`'https://xxxxx-qdrant.io`' QDRANT_API_KEY=`'your-api-key`' REDIS_HOST=`'<REDIS_HOST>`' REDIS_PORT=`'6379`' REDIS_PASSWORD=`'<REDIS_PASSWORD>`'"
Write-Host "     $cmdExample" -ForegroundColor Gray
Write-Host "  4. [ ] Attendre 2-3 minutes (telechargement du modele CLIP)" -ForegroundColor White
Write-Host "  5. [ ] Tester: curl $appUrl/api/v1/health" -ForegroundColor White

Write-Host ""
Write-Success "Bon deploiement!"
Write-Host ""
