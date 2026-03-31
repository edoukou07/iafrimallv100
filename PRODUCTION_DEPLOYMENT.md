# 🚀 PRODUCTION DEPLOYMENT GUIDE

## 📋 Pre-Deployment Checklist

### Security Configuration
- [ ] Generate unique `SECRET_KEY` (min 32 chars)
- [ ] Change `QDRANT_API_KEY` from default
- [ ] Set strong `REDIS_PASSWORD`
- [ ] Generate `API_KEY` for service-to-service auth
- [ ] Generate `INDEXATION_API_KEY` for Django backend
- [ ] Update `CORS_ORIGINS` with actual frontend domains
- [ ] Set `IMAGE_URL_WHITELIST` with trusted CDNs only

### Infrastructure Setup
- [ ] Database: Qdrant (managed service or self-hosted with TLS)
- [ ] Cache: Redis (Azure Cache for Redis or managed service)
- [ ] SSL/TLS certificates (mandatory)
- [ ] Domain name and DNS configuration
- [ ] Firewall rules configured
- [ ] Environment variables in secrets manager

### Monitoring & Logging
- [ ] Sentry/Error tracking configured (optional)
- [ ] Log aggregation setup (ELK, DataDog, etc.)
- [ ] Health check endpoints configured
- [ ] Alerting rules defined
- [ ] Backup strategy for Qdrant data

---

## 🐳 Docker Deployment

### 1. Load Production Configuration
```bash
# Copy production environment file
cp .env.prod .env

# Edit with actual production secrets
nano .env  # or your editor

# Verify all secrets are changed
grep "CHANGE-THIS" .env  # Should return nothing!
```

### 2. Build & Start Services
```bash
# Build image with production config
docker-compose -f docker-compose.prod.yml build --no-cache

# Start services (with health checks)
docker-compose -f docker-compose.prod.yml up -d

# Monitor startup
docker-compose -f docker-compose.prod.yml logs -f api
```

### 3. Verify Health
```bash
# Check all services healthy
docker-compose -f docker-compose.prod.yml ps

# Test API health endpoint
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/api/v1/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "Image Search API",
#   "version": "2.0.0",
#   "qdrant": {"connected": true},
#   "environment": "production"
# }
```

---

## ☁️ Azure Container Apps Deployment

### 1. Create Container Registry
```bash
az acr create --resource-group MyResourceGroup \
              --name mycontainerregistry \
              --sku Basic
```

### 2. Build & Push Image
```bash
# Build image
docker build -t mycontainerregistry.azurecr.io/image-search:prod .

# Login to ACR
az acr login --name mycontainerregistry

# Push image
docker push mycontainerregistry.azurecr.io/image-search:prod
```

### 3. Create Container App
```bash
az containerapp create \
  --name image-search-api \
  --resource-group MyResourceGroup \
  --environment MyEnvironment \
  --image mycontainerregistry.azurecr.io/image-search:prod \
  --env-vars \
    ENVIRONMENT=production \
    DEBUG=false \
    QDRANT_HOST=qdrant.example.com \
    REDIS_HOST=mycache.redis.cache.windows.net \
  --secrets \
    secret-key=@secretKeyValue \
    qdrant-key=@qdrantKeyValue \
    redis-password=@redisPasswordValue \
  --cpu 2.0 --memory 4.0Gi \
  --registry-login-server mycontainerregistry.azurecr.io \
  --registry-username myusername \
  --registry-password mypassword \
  --min-replicas 2 \
  --max-replicas 5 \
  --target-port 8000 \
  --ingress external \
  --transport http
```

---

## 🔐 Production Security Checklist

### Application Level
- [x] CORS whitelist configured
- [x] JWT authentication enabled
- [x] SSRF prevention (URL validation)
- [x] Rate limiting enabled
- [x] File upload size limited
- [x] Security headers set
- [x] Debug mode disabled
- [x] Exception details hidden
- [x] Logging level = WARNING

### Infrastructure Level
- [ ] SSL/TLS enforced (HTTPS only)
- [ ] API key rotation policy
- [ ] Secrets in key vault (not .env file)
- [ ] Network isolation (VPC, Security Groups)
- [ ] DDoS protection enabled
- [ ] WAF rules configured
- [ ] Backup & disaster recovery plan
- [ ] Regular security audits

### Monitoring
- [ ] Health checks every 30s
- [ ] Error alerts configured
- [ ] Performance metrics monitored
- [ ] Access logs archived
- [ ] Incident response plan ready

---

## 📈 Performance Tuning

### Qdrant Optimization
```yaml
# qdrant_config.yaml
storage:
  snapshots_path: /qdrant/snapshots
  wal_path: /qdrant/wal
  max_snapshot_recovery_attempts: 3

performance:
  max_search_batch_size: 10000
```

### Redis Optimization
```bash
# In docker-compose.prod.yml
redis-server \
  --maxmemory 2gb \
  --maxmemory-policy allkeys-lru \  # Evict least used keys
  --appendonly yes \                 # Persist to disk
  --appendfsync everysec             # Sync every second
```

### API Optimization
```python
# app/config.py
CACHE_TTL=7200              # 2 hour cache
RATE_LIMIT_PUBLIC_SEARCH=100  # 100 req/min
RATE_LIMIT_AUTH_SEARCH=1000   # 1000 req/min
```

---

## 🔄 Continuous Deployment

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy-prod.yml
name: Deploy to Production

on:
  push:
    branches: [prod]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Login to ACR
        run: |
          az acr login --name ${{ secrets.ACR_NAME }}
      
      - name: Build & Push
        run: |
          docker build -t ${{ secrets.ACR_NAME }}.azurecr.io/image-search:prod .
          docker push ${{ secrets.ACR_NAME }}.azurecr.io/image-search:prod
      
      - name: Deploy to Container Apps
        run: |
          az containerapp update \
            --name image-search-api \
            --resource-group ${{ secrets.RESOURCE_GROUP }} \
            --image ${{ secrets.ACR_NAME }}.azurecr.io/image-search:prod
```

---

## 🛠️ Troubleshooting

### API Health Check Failing
```bash
# Check logs
docker logs image-search-api-prod

# Verify secrets loaded
docker exec image-search-api-prod env | grep SECRET

# Check dependencies
docker-compose -f docker-compose.prod.yml ps
```

### Redis Connection Issues
```bash
# Test Redis connection
docker run --rm redis:7-alpine \
  redis-cli -h redis -p 6379 -a $REDIS_PASSWORD ping

# Check Redis memory
redis-cli -a $REDIS_PASSWORD INFO memory
```

### Qdrant Memory Issues
```bash
# Check Qdrant health
curl http://localhost:6333/health

# Monitor collection size
curl http://localhost:6333/collections/products

# Clear old snapshots if needed
curl -X DELETE http://localhost:6333/snapshots/old_snapshot_name
```

---

## 📞 Support & Escalation

For production issues:
1. Check logs: `docker-compose logs -f`
2. Verify configuration: `docker exec api env`
3. Test dependencies: health endpoints
4. Check monitoring dashboard
5. Contact DevOps team

---

## 📝 Deployment Record

| Environment | Status | Date | Version | Notes |
|------------|--------|------|---------|-------|
| Development | Active | - | 2.0.0 | - |
| Production | [Pending] | - | - | - |

**Last Updated:** March 31, 2026
**Maintained By:** DevOps Team
