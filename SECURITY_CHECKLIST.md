# 🔐 SECURITY CHECKLIST - PRODUCTION

## Pre-Deployment Security Verification

### 1. Secrets & Keys Management ✅

#### Application Secrets
- [ ] `SECRET_KEY` is minimum 32 characters
- [ ] `SECRET_KEY` is NOT the default value
- [ ] `SECRET_KEY` is stored in secrets manager (not .env file)
- [ ] `API_KEY` is generated and unique
- [ ] `INDEXATION_API_KEY` is generated and unique
- [ ] All keys are rotated every 90 days

#### Database & Cache Credentials
- [ ] `QDRANT_API_KEY` is NOT default
- [ ] `REDIS_PASSWORD` is strong (16+ chars, mixed case, numbers, symbols)
- [ ] `REDIS_PASSWORD` is random and unique
- [ ] Credentials are in Azure Key Vault (not .env)
- [ ] No credentials in git history: `git log -S "password"`

#### Certificate & SSL
- [ ] SSL/TLS certificate is valid (not self-signed in prod)
- [ ] Certificate is from trusted CA
- [ ] Certificate expiration monitored (alert 30 days before)
- [ ] Private key is secured with 0600 permissions
- [ ] HSTS header is enabled (`Strict-Transport-Security`)

---

### 2. Configuration Hardening ✅

#### Debug & Logging
- [ ] `ENVIRONMENT=production` (NOT development)
- [ ] `DEBUG=false` (MUST be False)
- [ ] `LOG_LEVEL=WARNING` (NOT DEBUG)
- [ ] API docs disabled (docs_url=None)
- [ ] ReDoc disabled (redoc_url=None)
- [ ] OpenAPI schema disabled (openapi_url=None)
- [ ] Stack traces NOT exposed in error responses

#### CORS & Domains
- [ ] CORS origins are whitelist (NOT `["*"]`)
- [ ] `cors_allow_credentials=false`
- [ ] Only `["GET", "POST"]` methods allowed
- [ ] `Authorization` header is in allowed headers
- [ ] Content-Type validation enabled

#### Rate Limiting
- [ ] `RATE_LIMIT_ENABLED=true`
- [ ] Public search: 100 req/min
- [ ] Auth search: 1000 req/min
- [ ] Auth upload: 50 req/min
- [ ] Rate limit headers included in responses

#### File Upload Security
- [ ] `MAX_UPLOAD_SIZE_MB=50` (configured)
- [ ] Mime type validation enabled
- [ ] File extension whitelist configured
- [ ] Uploaded files stored outside web root
- [ ] Virus scanning enabled (optional)

---

### 3. Network Security ✅

#### Transport Security
- [ ] All connections use HTTPS (no HTTP)
- [ ] TLS 1.2+ enforced
- [ ] Weak ciphers disabled
- [ ] Certificate pinning considered (optional)

#### SSRF Prevention
- [ ] Image URL whitelist configured (`IMAGE_URL_WHITELIST`)
- [ ] Private IP ranges blocked (127.0.0.1, 192.168.x.x)
- [ ] AWS metadata service blocked (169.254.169.254)
- [ ] GCP metadata service blocked (metadata.google.internal)
- [ ] File protocol blocked (file://, ftp://)
- [ ] Data URLs blocked (data://)

#### DDoS Protection
- [ ] Rate limiting enabled and tested
- [ ] Request size limit enforced (50MB)
- [ ] Timeout values configured (30s)
- [ ] Connection pooling limits set
- [ ] WAF rules deployed (if using)

#### Network Isolation
- [ ] API in private subnet (not public)
- [ ] Security groups configured (port 8000 only)
- [ ] Redis not exposed to internet
- [ ] Qdrant not exposed to internet (internal only)
- [ ] VPN or bastion host for admin access

---

### 4. Database Security ✅

#### Qdrant
- [ ] API key is strong (min 32 chars)
- [ ] SSL/TLS enabled for remote connections
- [ ] Collection backup on schedule
- [ ] Read replicas configured (if possible)
- [ ] Query timeout limits set (60s)
- [ ] Snapshot recovery tested

#### Redis
- [ ] Password authentication enabled
- [ ] No `requirepass` left empty
- [ ] SSL/TLS enabled for remote
- [ ] Eviction policy set (allkeys-lru)
- [ ] Memory limits configured (2GB)
- [ ] Persistence enabled (append-only)
- [ ] Keys are not stored unencrypted

---

### 5. Authentication & Authorization ✅

#### JWT Security
- [ ] JWT tokens have expiration (24 hours)
- [ ] `access_token_expire_hours` is reasonable
- [ ] Token refresh mechanism implemented
- [ ] Revocation list (blacklist) considered
- [ ] Tokens signed with HS256 or RS256
- [ ] Invalid tokens return 401 (not 500)

#### API Key Security
- [ ] API keys are long (min 32 chars)
- [ ] API keys are random (cryptographically secure)
- [ ] API keys are rotated regularly
- [ ] Keys validation on every request
- [ ] Rate limiting per API key
- [ ] Suspicious key activity monitored

#### Protected Routes
- [ ] All sensitive routes require authentication
- [ ] Public routes identified and documented
- [ ] Search endpoints have rate limiting
- [ ] Upload endpoints require API key
- [ ] Admin endpoints extra protected

---

### 6. Input Validation & Sanitization ✅

#### File Upload
- [ ] File size validated before processing
- [ ] Mime type checked (server-side)
- [ ] File extension whitelist enforced
- [ ] Filename sanitized (no path traversal)
- [ ] Virus scan performed (optional)
- [ ] Files stored with random names

#### Query Parameters
- [ ] URL parameters validated
- [ ] Query length limits enforced
- [ ] SQL injection impossible (using ORM)
- [ ] Search terms sanitized
- [ ] Limits: `top_k` max 100
- [ ] Score threshold: 0.0 to 1.0

#### JSON Request Body
- [ ] Schema validation with Pydantic
- [ ] Max body size enforced (50MB)
- [ ] Content-Type must be application/json
- [ ] No XXE vulnerabilities possible
- [ ] Nested objects limited in depth

---

### 7. Error Handling & Logging ✅

#### Exception Handling
- [ ] Generic 500 error in production
- [ ] Stack traces NOT exposed
- [ ] Error IDs generated for tracking
- [ ] Errors logged with full context (internal)
- [ ] Sensitive data NOT logged
- [ ] Exception rate monitored

#### Logging Security
- [ ] PII data NOT logged (passwords, tokens, IPs of users)
- [ ] Query data logged at DEBUG level only
- [ ] API requests logged with anonymized IP
- [ ] Failed auth attempts logged
- [ ] Logs stored securely (not world-readable)
- [ ] Log retention policy set (90 days)

#### Monitoring & Alerting
- [ ] Health check endpoints monitored
- [ ] Error rate threshold: alert if > 1%
- [ ] Response time monitored (p95 < 300ms)
- [ ] Failed auth attempts: alert if > 10/min
- [ ] Rate limit triggers logged
- [ ] Critical errors trigger PagerDuty

---

### 8. Security Headers ✅

#### Response Headers Verified
- [ ] `Strict-Transport-Security: max-age=31536000`
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options: DENY`
- [ ] `X-XSS-Protection: 1; mode=block`
- [ ] `Content-Security-Policy: default-src 'self'`
- [ ] `Referrer-Policy: strict-origin-when-cross-origin`
- [ ] `Cache-Control: no-store, no-cache`

Test with:
```bash
curl -I https://api.yourdomain.com/api/v1/health | grep "Strict-Transport-Security"
```

---

### 9. Dependency & Vulnerability Management ✅

#### Dependencies
- [ ] All packages locked (requirements.txt with versions)
- [ ] No beta/alpha versions in production
- [ ] Security audit run: `pip-audit -r requirements.txt`
- [ ] Known vulnerabilities checked (CVE databases)
- [ ] Dependencies updated monthly

#### Container Security
- [ ] Base image: `python:3.11-slim` (minimal)
- [ ] No `USER root` in Dockerfile
- [ ] No secrets in Docker image
- [ ] Image scanned for vulnerabilities
- [ ] Image built with `security_opt: no-new-privileges`

---

### 10. Compliance & Legal ✅

#### Data Protection
- [ ] GDPR compliance confirmed (if EU data)
- [ ] Data retention policy: 30 days cache
- [ ] PII data logging disabled
- [ ] User consent for data processing
- [ ] Right to be forgotten implemented

#### Audit Trail
- [ ] All API access logged
- [ ] Authentication attempts logged
- [ ] Configuration changes logged
- [ ] Backup & restore tested
- [ ] Audit logs immutable

#### Documentation
- [ ] Security policy documented
- [ ] Incident response plan exists
- [ ] Privacy policy published
- [ ] Terms of service updated
- [ ] Contact info for security issues

---

### 11. Testing & Validation ✅

#### Security Testing
- [ ] Penetration test scheduled (quarterly)
- [ ] OWASP Top 10 scan performed
- [ ] Rate limiting tested under load
- [ ] SSRF protection tested
- [ ] Authentication bypass tests
- [ ] SQL injection tests

#### Functional Testing
- [ ] Health endpoints return 200
- [ ] Rate limits enforce correctly
- [ ] CORS whitelist works
- [ ] Auth tokens validated
- [ ] Error responses generic (no details)

```bash
# Test health endpoint
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.yourdomain.com/api/v1/health

# Test rate limiting
for i in {1..101}; do
  curl -s https://api.yourdomain.com/api/v1/search
done
# Should return 429 after 100 requests

# Test CORS
curl -H "Origin: https://evil.com" \
  -H "Access-Control-Request-Method: POST" \
  https://api.yourdomain.com/api/v1/search
# Should return 403 or no CORS header
```

---

### 12. Post-Deployment Verification ✅

#### First 24 Hours
- [ ] Monitor error rate (should be < 0.1%)
- [ ] Monitor response times (p95 < 300ms)
- [ ] Check health endpoint every 5 min
- [ ] Monitor memory usage
- [ ] Verify rate limits working
- [ ] Confirm CORS whitelist enforced

#### First Week
- [ ] Load test performed (100 concurrent)
- [ ] Backup/restore tested
- [ ] Incident response tested
- [ ] Monitoring alerts tested
- [ ] Team trained on operations

---

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Security Lead | _______________ | ______ | _______________ |
| DevOps Lead | _______________ | ______ | _______________ |
| Product Owner | _______________ | ______ | _______________ |

---

**Last Updated:** March 31, 2026  
**Valid Until:** June 30, 2026  
**Next Review:** Every 2 weeks
