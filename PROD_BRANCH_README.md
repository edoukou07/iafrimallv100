# 🚀 PRODUCTION BRANCH - Image Search API v2.0.0

## Overview

This is the **production-ready branch** with all security hardening and production configurations applied.

**Status:** ✅ Ready for Deployment  
**Version:** 2.0.0  
**Security Level:** Production Grade  

---

## 📋 What's Included

### ✅ Security Hardening (from security-hardening branch)
```
✓ JWT Token Authentication
✓ CORS Whitelist (configurable)
✓ SSRF Prevention with URL Validator
✓ Rate Limiting per IP/User
✓ Security Headers (CSP, HSTS, etc.)
✓ Request Size Limiting
✓ File Upload Validation
✓ Production Error Handling
```

### ✅ Production Configuration
```
✓ .env.prod - Production environment template
✓ docker-compose.prod.yml - Production orchestration with resource limits
✓ nginx.conf.prod - Reverse proxy with security headers
✓ PRODUCTION_DEPLOYMENT.md - Complete deployment guide
✓ SECURITY_CHECKLIST.md - Pre-deployment verification
```

---

## 🔐 Pre-Deployment Requirements

### 1. Generate Secrets
```bash
# Generate SECRET_KEY (min 32 chars)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate API keys
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate Redis password (strong)
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

### 2. Update .env.prod
```bash
# Copy template
cp .env.prod .env

# Edit with actual secrets
nano .env

# Verify no defaults left
grep "CHANGE-THIS" .env  # Should return nothing!
```

### 3. Configuration Checklist
- [ ] ENVIRONMENT=production
- [ ] DEBUG=false
- [ ] SECRET_KEY changed (min 32 chars)
- [ ] QDRANT_API_KEY changed
- [ ] REDIS_PASSWORD set (strong password)
- [ ] CORS_ORIGINS updated with your domain
- [ ] IMAGE_URL_WHITELIST configured
- [ ] SSL certificates ready

---

## 🐳 Quick Start - Docker Deployment

### 1. Build & Start
```bash
# Load production environment
source .env  # or export values manually

# Build image
docker-compose -f docker-compose.prod.yml build --no-cache

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Monitor startup (wait 30s for health checks)
docker-compose -f docker-compose.prod.yml logs -f api
```

### 2. Verify Health
```bash
# Check services are running
docker-compose -f docker-compose.prod.yml ps

# Test API
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/v1/health

# Expected: {"status": "healthy", ...}
```

### 3. Run Security Checklist
See `SECURITY_CHECKLIST.md` for complete pre-flight validation.

---

## ☁️ Azure Container Apps Deployment

See `PRODUCTION_DEPLOYMENT.md` for detailed Azure instructions.

Quick commands:
```bash
# 1. Build & push image
docker build -t myregistry.azurecr.io/image-search:prod .
docker push myregistry.azurecr.io/image-search:prod

# 2. Create container app with secrets
az containerapp create \
  --name image-search-api \
  --environment MyEnvironment \
  --image myregistry.azurecr.io/image-search:prod \
  --secrets secret-key=VALUE api-key=VALUE \
  --env-vars ENVIRONMENT=production DEBUG=false \
  --min-replicas 2 --max-replicas 5

# 3. Monitor
az containerapp logs show --name image-search-api
```

---

## 📊 Branch Comparison

| Aspect | main | security-hardening | prod |
|--------|------|-------------------|------|
| Security Features | ❌ Basic | ✅ Full | ✅ Full |
| JWT Auth | ❌ No | ✅ Yes | ✅ Yes |
| Rate Limiting | ❌ No | ✅ Yes | ✅ Yes |
| SSRF Prevention | ❌ No | ✅ Yes | ✅ Yes |
| Production Config | ❌ No | ❌ No | ✅ Yes |
| Deployment Docs | ❌ No | ❌ No | ✅ Yes |
| Health Checks | ❌ Basic | ✅ Configured | ✅ Configured |
| Resource Limits | ❌ No | ❌ No | ✅ Yes |

---

## 🔍 File Structure

```
prod branch files:
├── .env.prod                      # Production env template
├── docker-compose.prod.yml        # Production orchestration
├── nginx.conf.prod               # Reverse proxy config
├── PRODUCTION_DEPLOYMENT.md      # Deployment guide
├── SECURITY_CHECKLIST.md         # Pre-flight checklist
└── app/security/                 # Security modules (from security-hardening)
    ├── validators.py             # SSRF prevention
    ├── jwt_handler.py            # JWT tokens
    ├── rate_limiter.py           # Rate limiting
    └── headers.py                # Security headers
```

---

## 🛡️ Security Verification

### Before Deployment
```bash
# 1. Run security checklist
# See: SECURITY_CHECKLIST.md

# 2. Check dependencies
pip-audit -r requirements.txt

# 3. Scan image for vulnerabilities
docker scan myregistry.azurecr.io/image-search:prod

# 4. Test SSRF protection
curl "https://api.yourdomain.com/api/v1/search-image?url=http://127.0.0.1:9200"
# Should return: 403 Forbidden

# 5. Test rate limiting
for i in {1..101}; do
  curl https://api.yourdomain.com/api/v1/search 2>/dev/null
done
# After 100: Should return 429 Too Many Requests

# 6. Verify CORS
curl -H "Origin: https://evil.com" https://api.yourdomain.com/
# Should NOT include CORS headers for unauthorized origin
```

### After Deployment
```bash
# 1. Monitor health
watch -n 5 'curl -s https://api.yourdomain.com/api/v1/health | jq'

# 2. Check logs
docker logs image-search-api-prod --tail 100 -f

# 3. Monitor metrics
# Connect to your monitoring dashboard (Datadog, New Relic, etc.)

# 4. Load test
# Don't do this in production without warning team!
# Use tool like: k6, locust, or Apache JMeter
```

---

## 📝 Configuration Reference

### Required Environment Variables
```env
ENVIRONMENT=production          # Must be 'production'
DEBUG=false                     # Must be False
SECRET_KEY=<generated>          # Min 32 chars, cryptographically secure
API_KEY=<generated>            # For service auth
QDRANT_API_KEY=<securely-stored>
REDIS_PASSWORD=<strong-password>
CORS_ORIGINS=["https://yourdomain.com"]
```

### Optional but Recommended
```env
IMAGE_URL_WHITELIST=["cdn.yourdomain.com"]
LOG_LEVEL=WARNING
RATE_LIMIT_ENABLED=true
```

See `.env.prod` for all options with descriptions.

---

## ⚠️ Critical Reminders

### DO
- ✅ Use secrets manager (Azure Key Vault, GitHub Secrets)
- ✅ Enable HTTPS only (not HTTP)
- ✅ Set strong passwords (16+ chars, mixed case, numbers, symbols)
- ✅ Rotate API keys every 90 days
- ✅ Monitor error rates and response times
- ✅ Test rate limiting before going live
- ✅ Run full security checklist
- ✅ Set up alerting for failures

### DON'T
- ❌ Commit .env file with real secrets
- ❌ Use default/example values in production
- ❌ Disable DEBUG mode check
- ❌ Allow HTTP connections
- ❌ Use weak passwords
- ❌ Skip CORS configuration
- ❌ Deploy without health checks
- ❌ Ignore security warnings

---

## 🚨 Troubleshooting

### API Won't Start
```bash
# Check configuration
docker-compose -f docker-compose.prod.yml logs api | head -50

# Verify secrets loaded
docker-compose -f docker-compose.prod.yml exec api env | grep SECRET

# Check dependencies
docker-compose -f docker-compose.prod.yml ps
```

### Health Check Failing
```bash
# Test directly
curl -v http://localhost:8000/api/v1/health

# Check JWT is initialized
docker logs image-search-api-prod 2>&1 | grep -i "security\|jwt"

# Verify Qdrant and Redis are healthy
docker-compose -f docker-compose.prod.yml logs qdrant
docker-compose -f docker-compose.prod.yml logs redis
```

### Rate Limiting Not Working
```bash
# Verify middleware loaded
docker logs image-search-api-prod | grep -i "rate"

# Check if headers present
curl -i http://localhost:8000/api/v1/search | grep "X-RateLimit"

# Look for rate limiter initialization
docker logs image-search-api-prod | grep -i "limiter"
```

---

## 📞 Support

For issues:
1. Check logs: `docker-compose logs -f`
2. See PRODUCTION_DEPLOYMENT.md § Troubleshooting
3. Run SECURITY_CHECKLIST.md validation
4. Contact: security-team@yourdomain.com

---

## 📊 Deployment Checklist

- [ ] All secrets generated and stored safely
- [ ] .env.prod updated with actual values
- [ ] No "CHANGE-THIS" values remain
- [ ] CORS origins configured
- [ ] SSL certificates ready
- [ ] Network security groups configured
- [ ] Monitoring and alerting set up
- [ ] Backup strategy defined
- [ ] Incident response plan ready
- [ ] Team trained on operations
- [ ] Security checklist signed off
- [ ] Load testing completed
- [ ] Health monitors configured

---

## 🔄 Related Branches

- **main** - Stable production code (before security hardening)
- **security-hardening** - Security features only (no production config)
- **prod** - This branch (complete production-ready)

---

## 📈 Performance Metrics

Target metrics for production:
- Response time p95: < 300ms
- Error rate: < 0.1%
- Availability: > 99.5%
- Rate limit violations: < 1% of valid traffic

Monitor these in your observability platform.

---

**Last Updated:** March 31, 2026  
**Maintained By:** DevOps Team  
**Ready for:** Production Deployment ✅
