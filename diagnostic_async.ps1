# Diagnostic complet de l'état Async sur Azure
# À exécuter sur Azure via SSH

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "🔍 DIAGNOSTIC: État de l'Indexation Asynchrone" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan

Write-Host "`n1️⃣  État des conteneurs Docker" -ForegroundColor Yellow
docker ps --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}"

Write-Host "`n2️⃣  Chercher Redis" -ForegroundColor Yellow
docker ps -a | Select-String redis

Write-Host "`n3️⃣  Chercher les workers" -ForegroundColor Yellow
docker ps -a | Select-String worker

Write-Host "`n4️⃣  Configuration Redis dans docker-compose.yml" -ForegroundColor Yellow
Select-String -Path docker-compose.yml -Pattern "redis" -Context 0,10

Write-Host "`n5️⃣  Test de connexion Redis" -ForegroundColor Yellow
try {
    $result = docker exec $(docker ps -q --filter name=redis) redis-cli ping 2>&1
    Write-Host "Résultat: $result" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur: $_" -ForegroundColor Red
}

Write-Host "`n6️⃣  Logs API" -ForegroundColor Yellow
$apiContainer = docker ps -q --filter name=api
if ($apiContainer) {
    docker logs $apiContainer 2>&1 | Select-Object -Last 10
} else {
    Write-Host "❌ Conteneur API non trouvé" -ForegroundColor Red
}

Write-Host "`n7️⃣  Logs Redis" -ForegroundColor Yellow
$redisContainer = docker ps -q --filter name=redis
if ($redisContainer) {
    docker logs $redisContainer 2>&1 | Select-Object -Last 10
} else {
    Write-Host "❌ Conteneur Redis non trouvé" -ForegroundColor Red
}

Write-Host "`n8️⃣  Logs Worker 1" -ForegroundColor Yellow
$workerContainers = docker ps -q --filter name=worker
if ($workerContainers) {
    $worker1 = ($workerContainers | Select-Object -First 1)
    docker logs $worker1 2>&1 | Select-Object -Last 20
} else {
    Write-Host "❌ Aucun conteneur worker trouvé" -ForegroundColor Red
}

Write-Host "`n===============================================================================" -ForegroundColor Cyan
Write-Host "📋 RECOMMANDATIONS" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan

Write-Host @"
✓ Si Redis est unhealthy:
  docker logs $(docker ps -q --filter name=redis)

✓ Si Workers sont unhealthy:
  docker logs $(docker ps -q --filter name=worker | head -1)
  
✓ Redémarrer tout:
  docker compose down
  docker compose up -d
  
✓ Tester la connexion Redis:
  docker exec $(docker ps -q --filter name=redis) redis-cli ping
  
✓ Relancer le test async:
  python test_async_real.py
"@ -ForegroundColor Green
