# 🚀 Guide: Activer l'Indexation Asynchrone Complète

## Situation Actuelle

```
✅ Implémentation backend:
   - API endpoint: Prêt (0.52s response)
   - Image persistence: Prêt
   - Worker code: Prêt
   
❌ Dépendances manquantes sur Azure:
   - Redis: N'est pas lancé
   - Worker: N'est pas lancé
```

---

## Option 1: Via Docker Compose (Recommandé)

### Sur le serveur Azure:

```bash
# 1. SSH sur le serveur
ssh user@52.143.186.136

# 2. Aller au répertoire
cd /path/to/iafrimallv100

# 3. Vérifier que Redis est dans docker-compose.yml
cat docker-compose.yml | grep -A 10 redis

# 4. Lancer Redis
docker compose up -d redis

# 5. Vérifier que Redis tourne
docker logs redis
# Résultat attendu: "Ready to accept connections"

# 6. Tester la connexion
docker compose exec redis redis-cli ping
# Résultat attendu: PONG
```

---

## Option 2: Lancer Redis Standalone (Alternative)

```bash
# Lancer Redis en background
docker run -d --name redis-async -p 6379:6379 redis:7-alpine

# Vérifier
docker logs redis-async
redis-cli -h localhost ping
```

---

## Étape 2: Lancer le Worker

### Méthode 1: En Background (Recommandé)

```bash
# SSH sur Azure
ssh user@52.143.186.136
cd /path/to/iafrimallv100

# Lancer le worker en background avec logs
nohup python -m app.workers.image_indexer_worker \
  --worker-id w1 \
  --redis-url redis://localhost:6379/0 \
  > worker.log 2>&1 &

# Vérifier que c'est lancé
ps aux | grep image_indexer_worker

# Voir les logs en temps réel
tail -f worker.log
```

### Méthode 2: Avec Docker

```bash
# Créer un Dockerfile pour le worker (optionnel)
docker run -d --name worker-async \
  --link redis:redis \
  -e REDIS_URL=redis://redis:6379/0 \
  -v /path/to/iafrimallv100:/app \
  python:3.11 \
  bash -c "cd /app && python -m app.workers.image_indexer_worker --worker-id w1"

# Logs
docker logs -f worker-async
```

### Méthode 3: Avec PM2 (Production)

```bash
# Installer PM2
npm install -g pm2

# Créer ecosystem.config.js
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'image-indexer-worker',
    script: 'python',
    args: '-m app.workers.image_indexer_worker --worker-id w1',
    instances: 1,
    exec_mode: 'fork',
    env: {
      REDIS_URL: 'redis://localhost:6379/0'
    }
  }]
};
EOF

# Démarrer
pm2 start ecosystem.config.js
pm2 logs
pm2 save

# Auto-start au démarrage
pm2 startup
```

---

## Étape 3: Vérifier que Tout Fonctionne

### Test 1: Redis Accessible

```bash
redis-cli -h localhost
> ping
PONG
> info server
# Vérifier que Redis est actif
```

### Test 2: Worker Actif

```bash
# Sur Azure
ps aux | grep image_indexer_worker
# Devrait voir: python -m app.workers.image_indexer_worker --worker-id w1

# Vérifier les logs
tail -20 worker.log
# Devrait voir: "Worker w1 started", "Polling queue"
```

### Test 3: Test Async Local

```bash
# Sur votre machine locale
python test_async_real.py

# Résultat attendu:
# Status: queued        (redis disponible!)
# Vérification 1/30... [queued]
# Vérification 2/30... [completed] ✅
```

---

## Variables d'Environnement Importantes

```bash
# À définir sur le serveur Azure:

# Redis
export REDIS_URL=redis://localhost:6379/0

# Logging
export LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR

# Worker
export WORKER_POLL_INTERVAL=1  # Secondes entre les vérifications
export WORKER_BATCH_SIZE=1     # Nombre de tâches par batch
export TASK_TIMEOUT=300        # Timeout en secondes
```

---

## Configuration Docker Compose Complète

Si Redis n'est pas dans votre `docker-compose.yml`, ajoutez:

```yaml
services:
  api:
    # ... existing config ...
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  redis_data:
```

---

## Troubleshooting

### Problem: "Cannot connect to Redis"
```
Solution:
1. Vérifier que Redis tourne: docker ps | grep redis
2. Vérifier le port: netstat -an | grep 6379
3. Vérifier la URL: REDIS_URL devrait être correcte
```

### Problem: "Worker doesn't process jobs"
```
Solution:
1. Vérifier les logs: tail -f worker.log
2. Vérifier que Redis fonctionne: redis-cli ping
3. Relancer le worker: kill <PID> && python -m ...
```

### Problem: "Job stays 'queued' forever"
```
Solution:
1. Vérifier que le worker est lancé: ps aux | grep image_indexer
2. Vérifier les erreurs: tail -f worker.log
3. Vérifier Redis: docker logs redis
4. Relancer le worker avec --poll-interval 1
```

---

## Commandes Utiles

```bash
# Voir tous les processus Python
ps aux | grep python

# Voir les logs du worker
tail -f worker.log

# Tuer un processus
kill -9 <PID>

# Vérifier les ports
netstat -an | grep LISTEN

# Voir les jobs en Redis
redis-cli
> KEYS *
> GET job:*
> LPOP queue:image-indexing
```

---

## Résumé: 3 Commandes pour Démarrer

```bash
# 1. Lancer Redis
docker compose up -d redis

# 2. Attendre que Redis soit prêt
sleep 3

# 3. Lancer le worker
python -m app.workers.image_indexer_worker --worker-id w1 &

# 4. Tester
python test_async_real.py
```

Après ça, l'indexation asynchrone devrait être 100% fonctionnelle! 🎉
