# Script PowerShell pour déployer sur la VM Ubuntu

param(
    [string]$ResourceGroup = "image-search-vm-rg",
    [string]$VMName = "image-search-vm"
)

Write-Host "🚀 Déploiement sur VM Ubuntu Standard_B2s" -ForegroundColor Cyan
Write-Host ""

# 1. Récupérer l'IP publique
Write-Host "📍 Récupération de l'IP publique..."
$publicIp = az vm list-ip-addresses --resource-group $ResourceGroup --name $VMName --output json | ConvertFrom-Json
$ip = $publicIp[0].virtualMachines[0].ipAddresses[0].publicIpAddress
$username = "azureuser"

Write-Host "✅ IP Publique: $ip" -ForegroundColor Green
Write-Host ""

# 2. Configurer les règles de sécurité (NSG)
Write-Host "🔒 Configuration du Network Security Group..."
$nsgName = "$VMName-nsg"
$nsgExists = az network nsg list --resource-group $ResourceGroup --query "[?name=='$nsgName'].name" -o tsv

if (-not $nsgExists) {
    Write-Host "Création du NSG..."
    az network nsg create --resource-group $ResourceGroup --name $nsgName
}

# Ajouter les règles pour les ports nécessaires
@(
    @{priority=100; name="allow-http"; port=80; protocol="Tcp"},
    @{priority=110; name="allow-https"; port=443; protocol="Tcp"},
    @{priority=120; name="allow-api"; port=8000; protocol="Tcp"},
    @{priority=130; name="allow-qdrant"; port=6333; protocol="Tcp"},
    @{priority=140; name="allow-redis"; port=6379; protocol="Tcp"}
) | ForEach-Object {
    Write-Host "  Ajout de la règle $_['name'] (port $_['port'])..."
    az network nsg rule create `
        --resource-group $ResourceGroup `
        --nsg-name $nsgName `
        --name $_.name `
        --priority $_.priority `
        --protocol $_.protocol `
        --destination-port-ranges $_.port `
        --access Allow `
        --direction Inbound 2>$null | Out-Null
}

Write-Host "✅ NSG configuré" -ForegroundColor Green
Write-Host ""

# 3. Passer le Network Security Group à la VM
$nicId = az vm show --resource-group $ResourceGroup --name $VMName --query "networkProfile.networkInterfaces[0].id" -o tsv
$nicName = $nicId.Split('/')[-1]

Write-Host "Attachement du NSG à l'interface réseau..."
az network nic update `
    --resource-group $ResourceGroup `
    --name $nicName `
    --network-security-group $nsgName 2>$null | Out-Null

Write-Host "✅ NSG attaché" -ForegroundColor Green
Write-Host ""

# 4. Préparer et copier les fichiers
Write-Host "📤 Préparation des fichiers de déploiement..."
$files = @(
    "Dockerfile",
    "docker-compose-vm.yml",
    "setup-vm.sh",
    "requirements.txt",
    "app"
)

# Vérifier les fichiers
$missingFiles = @()
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file trouvé"
    } else {
        Write-Host "  ✗ $file MANQUANT" -ForegroundColor Yellow
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "⚠️  Fichiers manquants: $($missingFiles -join ', ')" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔑 Clé SSH utilisée: ~/.ssh/id_rsa (générée par Azure)" -ForegroundColor Yellow
Write-Host ""

# 5. Instructions finales
Write-Host "╔════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                     🎯 PROCHAINES ÉTAPES                                   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "1️⃣  Connexion SSH à la VM :" -ForegroundColor Yellow
Write-Host "    ssh -i ~/.ssh/id_rsa azureuser@$ip" -ForegroundColor White
Write-Host ""
Write-Host "2️⃣  Sur la VM - Exécuter le setup initial :" -ForegroundColor Yellow
Write-Host "    cd /tmp"
Write-Host "    # [Copier setup-vm.sh et exécuter]"
Write-Host "    sudo bash setup-vm.sh" -ForegroundColor White
Write-Host ""
Write-Host "3️⃣  Sur la VM - Créer le répertoire de travail :" -ForegroundColor Yellow
Write-Host "    mkdir -p /opt/image-search-api" -ForegroundColor White
Write-Host ""
Write-Host "4️⃣  Sur la VM - Copier les fichiers de l'app :" -ForegroundColor Yellow
Write-Host "    # Depuis votre machine locale :"
Write-Host "    scp -r docker-compose-vm.yml Dockerfile app requirements.txt azureuser@$ip:/opt/image-search-api/" -ForegroundColor White
Write-Host ""
Write-Host "5️⃣  Sur la VM - Démarrer les services :" -ForegroundColor Yellow
Write-Host "    cd /opt/image-search-api"
Write-Host "    docker-compose -f docker-compose-vm.yml up -d" -ForegroundColor White
Write-Host ""
Write-Host "6️⃣  Vérifier la santé de l'API :" -ForegroundColor Yellow
Write-Host "    curl http://$ip:8000/api/v1/health" -ForegroundColor White
Write-Host ""
Write-Host "📊 COÛTS ESTIMÉS:" -ForegroundColor Cyan
Write-Host "  • VM Standard_B2s (compute): ~$30-40/mois" -ForegroundColor White
Write-Host "  • IP Publique statique:      ~$2-3/mois" -ForegroundColor White
Write-Host "  • Stockage (OS disk, data):  ~$5/mois" -ForegroundColor White
Write-Host "  ─────────────────────────────" -ForegroundColor White
Write-Host "  • TOTAL:                     ~$40-45/mois" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 URL d'accès (après déploiement):" -ForegroundColor Cyan
Write-Host "  http://$ip:8000" -ForegroundColor White
Write-Host "  http://$ip:8000/docs (Swagger UI)" -ForegroundColor White
Write-Host ""
