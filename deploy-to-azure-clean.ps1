# ============================================================================
# SCRIPT DE DEPLOIEMENT AZURE - IMAGE SEARCH API
# ============================================================================
# 
# Usage: ./deploy-to-azure-clean.ps1 -AppName "image-search-api-123"
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
    [string]$QdrantUrl = "",
    
    [Parameter(Mandatory = $false)]
    [string]$QdrantApiKey = ""
)

# ============================================================================
# FONCTIONS COULEURS
# ============================================================================

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-InfoMsg {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-WarnMsg {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

# ============================================================================
# VERIFICATIONS PREALABLES
# ============================================================================

Write-InfoMsg "===================================================================="
Write-InfoMsg "Verification des prerequis..."
Write-InfoMsg "===================================================================="

try {
    $azVersion = az --version 2>$null | Select-Object -First 1
    Write-Success "Azure CLI trouve: $azVersion"
}
catch {
    Write-ErrorMsg "Azure CLI non trouve. Installez-le: https://aka.ms/azure-cli"
    exit 1
}

try {
    $account = az account show 2>$null | ConvertFrom-Json
    Write-Success "Connecte a Azure: $($account.user.name)"
}
catch {
    Write-WarnMsg "Pas connecte a Azure. Execution de az login..."
    az login
}

try {
    $gitVersion = git --version
    Write-Success "Git trouve: $gitVersion"
}
catch {
    Write-ErrorMsg "Git non trouve. Installez-le: https://git-scm.com/"
    exit 1
}

# ============================================================================
# ETAPE 1: GROUPE DE RESSOURCES
# ============================================================================

Write-InfoMsg "===================================================================="
Write-InfoMsg "Creation/Verification du groupe de ressources: $ResourceGroup"
Write-InfoMsg "===================================================================="

$rg = az group show --name $ResourceGroup 2>$null
if (-not $rg) {
    Write-InfoMsg "Creation du groupe de ressources..."
    az group create --name $ResourceGroup --location $Location | Out-Null
    Write-Success "Groupe de ressources cree!"
}
else {
    Write-Success "Groupe de ressources existe deja!"
}

# ============================================================================
# ETAPE 2: APP SERVICE PLAN
# ============================================================================

Write-InfoMsg "===================================================================="
Write-InfoMsg "Creation/Verification du plan App Service: $Plan (B1)"
Write-InfoMsg "===================================================================="

$existingPlan = az appservice plan show --name $Plan --resource-group $ResourceGroup 2>$null
if (-not $existingPlan) {
    Write-InfoMsg "Creation du plan B1..."
    az appservice plan create --name $Plan `
        --resource-group $ResourceGroup `
        --sku B1 `
        --is-linux | Out-Null
    Write-Success "Plan App Service cree! Cout: USD 13.20/mois"
}
else {
    Write-Success "Plan App Service existe deja!"
}

# ============================================================================
# ETAPE 3: WEB APP
# ============================================================================

Write-InfoMsg "===================================================================="
Write-InfoMsg "Creation/Verification de l'App Service: $AppName"
Write-InfoMsg "===================================================================="

$existingApp = az webapp show --name $AppName --resource-group $ResourceGroup 2>$null
if (-not $existingApp) {
    Write-InfoMsg "Creation de l'application..."
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

Write-InfoMsg "===================================================================="
Write-InfoMsg "Creation/Verification d'Azure Cache for Redis"
Write-InfoMsg "===================================================================="

$existingRedis = az redis show --name $RedisName --resource-group $ResourceGroup 2>$null
if (-not $existingRedis) {
    Write-WarnMsg "Creation de Redis... (cela peut prendre 5-10 minutes)"
    az redis create --resource-group $ResourceGroup `
        --name $RedisName `
        --location $Location `
        --sku basic `
        --vm-size c0 `
        --enable-non-ssl-port true | Out-Null
    Write-Success "Azure Cache Redis cree! Cout: USD 15.30/mois"
}
else {
    Write-Success "Azure Cache Redis existe deja!"
}

$redis = az redis show --name $RedisName --resource-group $ResourceGroup | ConvertFrom-Json
$redisHost = $redis.hostName
$redisPort = $redis.port

$redisKeys = az redis list-keys --name $RedisName --resource-group $ResourceGroup | ConvertFrom-Json
$redisPassword = $redisKeys.primaryKey

Write-Success "Redis Host: $redisHost"
Write-Success "Redis Port: $redisPort"

# ============================================================================
# ETAPE 5: CONFIGURATION VARIABLES
# ============================================================================

Write-InfoMsg "===================================================================="
Write-InfoMsg "Configuration des variables d'environnement"
Write-InfoMsg "===================================================================="

if ($QdrantUrl -and $QdrantApiKey) {
    Write-InfoMsg "Configuration avec Qdrant Cloud..."
    
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
    Write-WarnMsg "Qdrant URL ou API Key manquante!"
    Write-InfoMsg "Vous devrez les ajouter manuellement:"
    Write-InfoMsg "1. Aller sur: https://cloud.qdrant.io"
    Write-InfoMsg "2. Creer un cluster gratuit"
    Write-InfoMsg "3. Copier l'URL et la cle API"
    Write-InfoMsg "4. Executer cette commande avec vos valeurs:"
    Write-Host "   az webapp config appsettings set -g image-search-rg -n $AppName --settings QDRANT_HOST=YourURL QDRANT_API_KEY=YourKey REDIS_HOST=$redisHost REDIS_PASSWORD=$redisPassword" -ForegroundColor Yellow
}

# ============================================================================
# ETAPE 6: CONFIGURATION STARTUP
# ============================================================================

Write-InfoMsg "===================================================================="
Write-InfoMsg "Configuration du startup command"
Write-InfoMsg "===================================================================="

az webapp config set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --startup-file "startup.sh" | Out-Null

Write-Success "Startup command configure!"

# ============================================================================
# ETAPE 7: CONFIGURATION GIT
# ============================================================================

Write-InfoMsg "===================================================================="
Write-InfoMsg "Configuration du deploiement Git"
Write-InfoMsg "===================================================================="

$gitUrl = az webapp deployment source config-local-git `
    --resource-group $ResourceGroup `
    --name $AppName | ConvertFrom-Json | Select-Object -ExpandProperty url

Write-Success "URL Git de deploiement:"
Write-Host $gitUrl -ForegroundColor Cyan

Write-InfoMsg "Ajout du remote Azure a votre repository Git..."
git remote remove azure 2>$null
git remote add azure $gitUrl

Write-Success "Remote Git azure ajoute!"

# ============================================================================
# ETAPE 8: DEPLOIEMENT
# ============================================================================

Write-InfoMsg "===================================================================="
Write-InfoMsg "Deploiement du code..."
Write-InfoMsg "===================================================================="

Write-InfoMsg "Initialisation Git (si necessaire)..."
if (-not (git status 2>$null)) {
    git init
    git add .
    git commit -m "Initial commit for Azure deployment"
}

Write-InfoMsg "Push vers Azure (cela peut prendre quelques minutes)..."
git push azure (git rev-parse --abbrev-ref HEAD):main

Write-Success "Code deploye!"

# ============================================================================
# ETAPE 9: VERIFICATION
# ============================================================================

Write-InfoMsg "===================================================================="
Write-InfoMsg "Verification du deploiement..."
Write-InfoMsg "===================================================================="

Write-WarnMsg "Attendre 2-3 minutes pour que l'app demarre..."
Start-Sleep -Seconds 3

Write-InfoMsg "Affichage des 20 dernieres lignes de log..."
Write-Host "--------------------------------------------------------------------" -ForegroundColor Gray

$logs = az webapp log tail --name $AppName --resource-group $ResourceGroup --lines 20
Write-Host $logs

# ============================================================================
# RESUME FINAL
# ============================================================================

$appUrl = "https://$AppName.azurewebsites.net"

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "DEPLOIEMENT COMPLETE AVEC SUCCES!" -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Green

Write-Host ""
Write-Success "URL de votre API:"
Write-Host $appUrl -ForegroundColor Cyan

Write-Success "Documentation interactive Swagger:"
Write-Host "$appUrl/docs" -ForegroundColor Cyan

Write-Success "Health check:"
Write-Host "$appUrl/api/v1/health" -ForegroundColor Cyan

Write-Host ""
Write-Success "Couts estimes:"
Write-Host "  - App Service B1: USD 13.20/mois" -ForegroundColor White
Write-Host "  - Redis Basic: USD 15.30/mois" -ForegroundColor White
Write-Host "  - Qdrant Cloud: USD 0.00/mois (gratuit)" -ForegroundColor White
Write-Host "  -------- TOTAL --------" -ForegroundColor White
Write-Host "  - Environ USD 31/mois" -ForegroundColor Yellow

Write-Host ""
Write-InfoMsg "Commandes utiles:"
Write-Host "  Voir les logs:" -ForegroundColor White
Write-Host "  az webapp log tail --name $AppName --resource-group $ResourceGroup --follow" -ForegroundColor Gray
Write-Host ""
Write-Host "  Redemarrer l'app:" -ForegroundColor White
Write-Host "  az webapp restart --name $AppName --resource-group $ResourceGroup" -ForegroundColor Gray
Write-Host ""
Write-Host "  Voir les variables:" -ForegroundColor White
Write-Host "  az webapp config appsettings list --name $AppName --resource-group $ResourceGroup" -ForegroundColor Gray

Write-Host ""
Write-WarnMsg "A faire maintenant:"
Write-Host "  1. Creer un cluster Qdrant sur https://cloud.qdrant.io" -ForegroundColor White
Write-Host "  2. Copier l'URL et la cle API" -ForegroundColor White
Write-Host "  3. Mettre a jour les variables d'environnement avec Qdrant" -ForegroundColor White
Write-Host "  4. Attendre 2-3 minutes (telechargement du modele CLIP)" -ForegroundColor White
Write-Host "  5. Tester: curl $appUrl/api/v1/health" -ForegroundColor White

Write-Host ""
Write-Success "Bon deploiement!"
Write-Host ""
