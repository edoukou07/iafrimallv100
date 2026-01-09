# Script PowerShell simplifié pour déployer sur la VM Ubuntu
# Usage: .\deploy-to-vm-simple.ps1

$ErrorActionPreference = "Stop"

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Déploiement Image Search API sur VM Ubuntu               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Paramètres
$resourceGroup = "image-search-vm-rg"
$vmName = "image-search-vm"
$deployPath = "/opt/image-search-api"
$user = "azureuser"

# Étape 1: Récupérer l'IP
Write-Host "📍 Récupération de l'IP publique..." -ForegroundColor Yellow
try {
    Start-Sleep -Seconds 5  # Petit délai si la VM vient de démarrer
    $vmIpInfo = az vm list-ip-addresses --resource-group $resourceGroup --name $vmName --output json | ConvertFrom-Json
    
    if ($vmIpInfo.Count -eq 0 -or $null -eq $vmIpInfo[0].virtualMachines[0].ipAddresses[0]) {
        Write-Host "⚠️  IP non encore assignée. Attente..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        $vmIpInfo = az vm list-ip-addresses --resource-group $resourceGroup --name $vmName --output json | ConvertFrom-Json
    }
    
    $ip = $vmIpInfo[0].virtualMachines[0].ipAddresses[0].publicIpAddress
    Write-Host "✅ IP Publique: $ip" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur lors de la récupération de l'IP" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host ""

# Étape 2: Vérifier la clé SSH
Write-Host "🔑 Vérification de la clé SSH..." -ForegroundColor Yellow
$sshKey = "$HOME\.ssh\id_rsa"
if (-not (Test-Path $sshKey)) {
    Write-Host "⚠️  Clé SSH non trouvée à $sshKey" -ForegroundColor Yellow
    Write-Host "    Les clés SSH sont générées par Azure lors de la création de la VM" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Solution: Utilisez 'az ssh vm' pour se connecter:" -ForegroundColor Yellow
    Write-Host "  az ssh vm -g $resourceGroup -n $vmName" -ForegroundColor White
} else {
    Write-Host "✅ Clé SSH trouvée" -ForegroundColor Green
}

Write-Host ""

# Étape 3: Copier les fichiers
Write-Host "📤 Copie des fichiers vers la VM..." -ForegroundColor Yellow

$filesToCopy = @(
    "docker-compose-vm.yml",
    "Dockerfile", 
    "requirements.txt",
    "setup-vm.sh"
)

foreach ($file in $filesToCopy) {
    if (Test-Path $file) {
        Write-Host "  📄 Copie de $file..." -ForegroundColor Gray
        
        if ($file -eq "setup-vm.sh") {
            # Copier dans /tmp pour exécution
            scp -i $sshKey -q $file "${user}@${ip}:/tmp/" 2>$null
        } else {
            # Copier dans le répertoire de l'app (sera créé)
            scp -i $sshKey -q $file "${user}@${ip}:/tmp/" 2>$null
        }
        Write-Host "    ✓ $file copié" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ $file non trouvé (ignoré)" -ForegroundColor Yellow
    }
}

# Copier le répertoire app
if (Test-Path "app") {
    Write-Host "  📁 Copie du répertoire app..." -ForegroundColor Gray
    scp -i $sshKey -r -q app "${user}@${ip}:/tmp/" 2>$null
    Write-Host "    ✓ app copié" -ForegroundColor Gray
}

if (Test-Path "data") {
    Write-Host "  📁 Copie du répertoire data..." -ForegroundColor Gray
    scp -i $sshKey -r -q data "${user}@${ip}:/tmp/" 2>$null
    Write-Host "    ✓ data copié" -ForegroundColor Gray
}

Write-Host "✅ Fichiers copiés" -ForegroundColor Green
Write-Host ""

# Étape 4: Instructions finales
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ✅ PROCHAINES ÉTAPES - EXÉCUTER SUR LA VM                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "1️⃣  Connexion SSH:" -ForegroundColor White
Write-Host "    ssh -i ~/.ssh/id_rsa azureuser@$ip" -ForegroundColor Yellow
Write-Host ""

Write-Host "2️⃣  Setup initial (installer Docker):" -ForegroundColor White
Write-Host "    sudo bash /tmp/setup-vm.sh" -ForegroundColor Yellow
Write-Host ""

Write-Host "3️⃣  Créer le répertoire de travail:" -ForegroundColor White
Write-Host "    sudo mkdir -p /opt/image-search-api && sudo chown azureuser:azureuser /opt/image-search-api" -ForegroundColor Yellow
Write-Host ""

Write-Host "4️⃣  Déplacer les fichiers:" -ForegroundColor White
Write-Host "    cd /opt/image-search-api" -ForegroundColor Yellow
Write-Host "    mv /tmp/docker-compose-vm.yml /tmp/Dockerfile /tmp/requirements.txt /tmp/app /tmp/data ./" -ForegroundColor Yellow
Write-Host ""

Write-Host "5️⃣  Démarrer les services:" -ForegroundColor White
Write-Host "    docker-compose -f docker-compose-vm.yml up -d" -ForegroundColor Yellow
Write-Host ""

Write-Host "6️⃣  Attendre ~2-3 min et vérifier:" -ForegroundColor White
Write-Host "    docker ps" -ForegroundColor Yellow
Write-Host "    curl http://localhost:8000/api/v1/health" -ForegroundColor Yellow
Write-Host ""

Write-Host "📊 Accès depuis votre machine (après démarrage):" -ForegroundColor Cyan
Write-Host "   API:        http://$ip:8000" -ForegroundColor White
Write-Host "   Swagger:    http://$ip:8000/docs" -ForegroundColor White
Write-Host "   Health:     http://$ip:8000/api/v1/health" -ForegroundColor White
Write-Host ""

Write-Host "💰 Coûts mensuels: ~\$40-45 (vs \$95-120 avec Container Apps)" -ForegroundColor Green
Write-Host ""

Write-Host "📖 Guide complet: DEPLOY_VM_GUIDE.md" -ForegroundColor Cyan
