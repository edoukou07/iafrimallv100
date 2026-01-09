#!/usr/bin/env powershell

# Script PowerShell pour déployer sur la VM Ubuntu
# Usage: powershell -ExecutionPolicy Bypass -File deploy-to-vm-simple.ps1

$resourceGroup = "image-search-vm-rg"
$vmName = "image-search-vm"
$user = "azureuser"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " Image Search API - Deploiement sur VM Ubuntu       " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Etape 1: Recuperer l'IP
Write-Host "[*] Recuperation de l'IP publique..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

$vmIpInfo = az vm list-ip-addresses --resource-group $resourceGroup --name $vmName --output json | ConvertFrom-Json

if ($vmIpInfo.Count -eq 0) {
    Write-Host "[!] Erreur: VM non trouvee" -ForegroundColor Red
    exit 1
}

$ip = $vmIpInfo[0].virtualMachines[0].ipAddresses[0].publicIpAddress

if ([string]::IsNullOrEmpty($ip)) {
    Write-Host "[!] IP non encore assignee, attente..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    $vmIpInfo = az vm list-ip-addresses --resource-group $resourceGroup --name $vmName --output json | ConvertFrom-Json
    $ip = $vmIpInfo[0].virtualMachines[0].ipAddresses[0].publicIpAddress
}

Write-Host "[OK] IP Publique: $ip" -ForegroundColor Green
Write-Host ""

# Etape 2: Afficher les instructions
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " INSTRUCTIONS DE DEPLOIEMENT                         " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "ETAPE 1: Se connecter a la VM" -ForegroundColor White
Write-Host ""
Write-Host "  Option A - Avec SSH keys:"
Write-Host "    ssh -i ~/.ssh/id_rsa azureuser@$ip"
Write-Host ""
Write-Host "  Option B - Avec Azure CLI:"
Write-Host "    az ssh vm -g $resourceGroup -n $vmName"
Write-Host ""

Write-Host "ETAPE 2: Copier les fichiers" -ForegroundColor White
Write-Host ""
Write-Host "  Depuis VOTRE machine (pas la VM):"
Write-Host "    cd C:\Users\$env:USERNAME\Desktop\iaafrimall\iafrimallv100"
Write-Host ""
Write-Host "    scp -r docker-compose-vm.yml Dockerfile requirements.txt app data setup-vm.sh azureuser@$ip:/tmp/"
Write-Host ""

Write-Host "ETAPE 3: Executer le setup" -ForegroundColor White
Write-Host ""
Write-Host "  Sur la VM (apres SSH):"
Write-Host "    sudo bash /tmp/setup-vm.sh"
Write-Host ""

Write-Host "ETAPE 4: Preparer le repertoire" -ForegroundColor White
Write-Host ""
Write-Host "    mkdir -p /opt/image-search-api"
Write-Host "    cd /opt/image-search-api"
Write-Host "    cp /tmp/docker-compose-vm.yml /tmp/Dockerfile /tmp/requirements.txt ./"
Write-Host "    cp -r /tmp/app /tmp/data ./"
Write-Host ""

Write-Host "ETAPE 5: Demarrer les services" -ForegroundColor White
Write-Host ""
Write-Host "    docker-compose -f docker-compose-vm.yml up -d"
Write-Host "    docker-compose -f docker-compose-vm.yml logs -f"
Write-Host ""

Write-Host "ETAPE 6: Verifier l'API" -ForegroundColor White
Write-Host ""
Write-Host "  Depuis votre machine Windows:"
Write-Host "    curl http://$ip:8000/api/v1/health"
Write-Host ""

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " ACCES A L'APPLICATION                              " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  API:        http://$ip:8000" -ForegroundColor White
Write-Host "  Swagger:    http://$ip:8000/docs" -ForegroundColor White
Write-Host "  Health:     http://$ip:8000/api/v1/health" -ForegroundColor White
Write-Host ""

Write-Host "COUTS MENSUELS: ~40-45 EUR (vs 95-120 avec Container Apps)" -ForegroundColor Green
Write-Host ""

Write-Host "Pour plus de details, consultez: DEPLOY_VM_GUIDE.md" -ForegroundColor Cyan
