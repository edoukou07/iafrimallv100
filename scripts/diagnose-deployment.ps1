#!/usr/bin/env pwsh

Write-Host "🔍 Diagnostic Déploiement Azure - Image Search API" -ForegroundColor Cyan
Write-Host ""

# Variables
$resourceGroup = "ia-image-search-rg"
$appName = "image-search-api-123"

# 1. Vérifier la structure
Write-Host "1️⃣  Vérification de la structure du projet..." -ForegroundColor Yellow
$files = @(
    "app/main.py",
    "app/__init__.py",
    "app/config.py",
    "app/dependencies.py",
    "app/api/routes.py",
    "app/models/schemas.py",
    "requirements.txt",
    "Dockerfile"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file"
    } else {
        Write-Host "  ❌ MANQUANT: $file" -ForegroundColor Red
    }
}

Write-Host ""

# 2. Vérifier requirements.txt
Write-Host "2️⃣  Vérification des dépendances..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    $reqs = Get-Content requirements.txt | Measure-Object -Line
    Write-Host "  ✅ requirements.txt: $($reqs.Lines) lignes"
    
    # Vérifier les dépendances essentielles
    $content = Get-Content requirements.txt -Raw
    $essential = @("fastapi", "uvicorn", "pydantic", "qdrant-client", "redis", "transformers", "torch")
    
    foreach ($dep in $essential) {
        if ($content -match $dep) {
            Write-Host "    ✅ $dep"
        } else {
            Write-Host "    ⚠️  $dep non trouvé" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  ❌ requirements.txt MANQUANT" -ForegroundColor Red
}

Write-Host ""

# 3. Vérifier l'app/config.py
Write-Host "3️⃣  Vérification de la configuration..." -ForegroundColor Yellow
$configContent = Get-Content "app/config.py" -Raw
if ($configContent -match "get_settings") {
    Write-Host "  ✅ get_settings() trouvé"
} else {
    Write-Host "  ⚠️  get_settings() non trouvé" -ForegroundColor Yellow
}

if ($configContent -match "BaseSettings") {
    Write-Host "  ✅ Pydantic BaseSettings utilisé"
} else {
    Write-Host "  ⚠️  Utilise peut-être une ancienne version" -ForegroundColor Yellow
}

Write-Host ""

# 4. Vérifier les logs Azure
Write-Host "4️⃣  Vérification du statut du Web App..." -ForegroundColor Yellow
$appStatus = az webapp show -g $resourceGroup -n $appName --query "state" -o tsv
Write-Host "  État: $appStatus"

Write-Host ""

# 5. Récupérer les erreurs de déploiement
Write-Host "5️⃣  Derniers logs de déploiement..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Pour voir les logs détaillés, utilisez:" -ForegroundColor Cyan
Write-Host "  az webapp log tail -g $resourceGroup -n $appName"
Write-Host ""
Write-Host "Ou visitez:" -ForegroundColor Cyan
Write-Host "  https://$appName.scm.azurewebsites.net/DebugConsole"

Write-Host ""
Write-Host "✅ Diagnostic terminé" -ForegroundColor Green
