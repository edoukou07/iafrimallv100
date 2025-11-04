# 🔧 Étapes pour Diagnostiquer et Fixer les Workers sur Azure

## Situation Actuelle

D'après ta sortie `docker ps`:
```
- ✅ Redis: HEALTHY (4 minutes)
- ✅ API: HEALTHY (4 minutes)
- ❌ Worker 1: UNHEALTHY (4 minutes)
- ❌ Worker 2: UNHEALTHY (4 minutes)
- ✅ Qdrant: UP (4 minutes)
```

Les workers sont en conteneur mais "unhealthy" = le healthcheck échoue.

---

## 📋 Commandes à Exécuter sur Azure (via SSH)

### Étape 1: Voir les logs du Worker 1

```bash
docker logs $(docker ps -q --filter name=worker-1) 2>&1 | tail -50
```

**Cherche**: Erreurs, "Traceback", "Connection refused", "ModuleNotFoundError"

### Étape 2: Voir les logs du Worker 2

```bash
docker logs $(docker ps -q --filter name=worker-2) 2>&1 | tail -50
```

### Étape 3: Tester Redis depuis un Worker

```bash
# Se connecter au worker
docker exec -it $(docker ps -q --filter name=worker-1) bash

# À l'intérieur du worker:
redis-cli -h redis ping
# Devrait afficher: PONG
```

### Étape 4: Vérifier la Variable REDIS_URL

```bash
docker inspect $(docker ps -q --filter name=worker-1) \
  | grep -i REDIS
```

**Résultat attendu**:
```
"REDIS_URL=redis://redis:6379/0"
```

### Étape 5: Voir l'état des conteneurs

```bash
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Étape 6: Vérifier que Redis fonctionne

```bash
docker exec $(docker ps -q --filter name=redis) redis-cli ping
# Résultat: PONG
```

---

## 🐛 Problèmes Courants et Solutions

### Problème: "unhealthy" Workers

**Cause 1: Worker ne peut pas se connecter à Redis**
```bash
# Check dans les logs:
docker logs $(docker ps -q --filter name=worker-1) | grep -i redis
# Cherche: "Connection refused", "Cannot connect"

# Solution:
docker exec $(docker ps -q --filter name=worker-1) redis-cli -h redis ping
# Si ça fail, le problème est la résolution DNS "redis"
```

**Cause 2: Erreur d'import Python**
```bash
# Check dans les logs:
docker logs $(docker ps -q --filter name=worker-1) | grep -i "error\|traceback\|import"

# Solution:
docker exec $(docker ps -q --filter name=worker-1) python -c "
from app.workers.image_indexer_worker import AsyncImageIndexerWorker
print('✓ Imports OK')
"
```

**Cause 3: Healthcheck mal configuré**
```bash
# Voir la healthcheck config:
docker inspect $(docker ps -q --filter name=worker-1) \
  | grep -A 10 "Healthcheck"

# Relancer sans healthcheck:
docker compose up -d --no-deps --force-recreate worker1 worker2
```

---

## ✅ Solution Rapide: Redémarrer et Tester

```bash
# 1. Sur Azure, redémarrer les conteneurs
docker compose down
docker compose up -d

# 2. Attendre que tout soit prêt
sleep 5

# 3. Vérifier que Redis répond
docker exec $(docker ps -q --filter name=redis) redis-cli ping
# Devrait afficher: PONG

# 4. Vérifier qu'un worker peut se connecter à Redis
docker exec $(docker ps -q --filter name=worker-1) redis-cli -h redis ping
# Devrait afficher: PONG

# 5. Depuis votre machine locale, tester async
python test_async_real.py
# Devrait afficher: Status: queued → completed ✅
```

---

## 📊 Résultat Attendu Si Tout Fonctionne

### Status des conteneurs
```
NAMES                  STATUS
iafrimallv100-api      Up 2 minutes (healthy)
iafrimallv100-redis    Up 2 minutes (healthy)
iafrimallv100-worker1  Up 2 minutes (healthy)
iafrimallv100-worker2  Up 2 minutes (healthy)
iafrimallv100-qdrant   Up 2 minutes
```

### Test Async
```
Test: Indexation Asynchrone Complète
✓ Enqueued en 0.31s
  Job ID: job-dccc05e9cd6c
  Status: queued        ← ✅ KEY DIFFERENCE!
  
Vérification 1/30... [queued]
Vérification 2/30... [completed] ✅
✅ Job complété avec succès!
```

---

## 🔍 Diagnostic Complet (à exécuter sur Azure)

```bash
# Créer un script diagnostic complet
cat > /tmp/check_async.sh << 'EOF'
#!/bin/bash

echo "==============================================="
echo "DIAGNOSTIC: État Async Complet"
echo "==============================================="

echo ""
echo "1. État des conteneurs:"
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "2. Redis accessible?"
docker exec $(docker ps -q --filter name=redis) redis-cli ping

echo ""
echo "3. Worker 1 peut atteindre Redis?"
docker exec $(docker ps -q --filter name=worker-1) redis-cli -h redis ping

echo ""
echo "4. Logs Worker 1 (dernières 10 lignes):"
docker logs $(docker ps -q --filter name=worker-1) | tail -10

echo ""
echo "5. Logs API (erreurs Redis):"
docker logs $(docker ps -q --filter name=api) 2>&1 | grep -i redis | tail -5

echo ""
echo "==============================================="
EOF

chmod +x /tmp/check_async.sh
/tmp/check_async.sh
```

---

## 🎯 Résumé des Actions

**Sur Azure (SSH):**
1. Voir les logs du worker: `docker logs $(docker ps -q --filter name=worker-1) | tail -50`
2. Tester Redis: `docker exec $(docker ps -q --filter name=redis) redis-cli ping`
3. Si erreurs: Redémarrer: `docker compose down && docker compose up -d`
4. Attendre: `sleep 5`

**Localement (ta machine):**
1. Exécuter: `python test_async_real.py`
2. Vérifier: Status passe de "queued" → "completed"

Si toujours unhealthy après redémarrage, partage les logs du worker et on verra ce qui cloche!
