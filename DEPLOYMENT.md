# DEPLOYMENT.md - Guide de Déploiement

## 📋 Options de Déploiement

### 1. **Docker Compose Locale** (Développement)

#### Prérequis
- Docker Desktop installé
- 8GB+ RAM disponible
- Port 8000, 6333, 6379 disponibles

#### Installation

```bash
# 1. Cloner le projet
cd image-search-api

# 2. Copier et configurer .env
cp .env.example .env

# 3. Démarrer
docker-compose up -d

# 4. Attendre l'initialisation (1-2 min)
docker-compose logs -f api

# 5. Vérifier
curl http://localhost:8000/api/v1/health
```

#### Commandes Utiles

```bash
# Voir les logs
docker-compose logs -f

# Arrêter les services
docker-compose down

# Redémarrer
docker-compose restart

# Nettoyer les volumes
docker-compose down -v
```

---

### 2. **AWS ECS Fargate** (Recommandé pour Production)

#### Architecture
```
Load Balancer (ALB)
    ↓
ECS Fargate Task (API)
    ↓
EFS (Qdrant persistence)
ElastiCache (Redis)
```

#### Setup

```bash
# 1. Installer AWS CLI
pip install awscli

# 2. Configurer AWS credentials
aws configure

# 3. Créer ECR repository
aws ecr create-repository --repository-name image-search-api

# 4. Tagger et push l'image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag image-search-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/image-search-api:latest

docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/image-search-api:latest

# 5. Créer cluster ECS
aws ecs create-cluster --cluster-name search-api-cluster

# 6. Créer task definition (voir aws-ecs-task-definition.json)
aws ecs register-task-definition --cli-input-json file://aws-ecs-task-definition.json

# 7. Créer service
aws ecs create-service \
  --cluster search-api-cluster \
  --service-name image-search-api \
  --task-definition image-search-api:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration awsvpcConfiguration='{subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}'
```

#### Configuration RDS PostgreSQL (optionnel pour persister les métadonnées)

```bash
aws rds create-db-instance \
  --db-instance-identifier search-api-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --allocated-storage 20
```

---

### 3. **Kubernetes (K8s)** (Scalabilité maximale)

#### Prérequis
- Cluster K8s (EKS, GKE, ou local avec Minikube)
- kubectl configuré
- Helm (optionnel)

#### Fichiers de Configuration

**k8s/namespace.yaml**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: image-search
```

**k8s/deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: image-search-api
  namespace: image-search
spec:
  replicas: 3
  selector:
    matchLabels:
      app: image-search-api
  template:
    metadata:
      labels:
        app: image-search-api
    spec:
      containers:
      - name: api
        image: your-registry/image-search-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: QDRANT_HOST
          value: qdrant-service
        - name: REDIS_HOST
          value: redis-service
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

**k8s/service.yaml**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: image-search-api-service
  namespace: image-search
spec:
  type: LoadBalancer
  selector:
    app: image-search-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

#### Déploiement

```bash
# 1. Créer namespace
kubectl apply -f k8s/namespace.yaml

# 2. Déployer Qdrant (via Helm)
helm repo add qdrant https://qdrant.github.io/qdrant-helm
helm install qdrant qdrant/qdrant -n image-search

# 3. Déployer Redis
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install redis bitnami/redis -n image-search

# 4. Déployer l'API
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# 5. Vérifier le déploiement
kubectl get pods -n image-search
kubectl get svc -n image-search
```

---

### 4. **Google Cloud Run** (Serverless simple)

```bash
# 1. Configurer gcloud
gcloud auth login
gcloud config set project PROJECT_ID

# 2. Builder l'image
gcloud builds submit --tag gcr.io/PROJECT_ID/image-search-api

# 3. Déployer
gcloud run deploy image-search-api \
  --image gcr.io/PROJECT_ID/image-search-api \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --allow-unauthenticated \
  --set-env-vars QDRANT_HOST=qdrant-cloud-endpoint
```

---

### 5. **Heroku** (Prototypage rapide)

```bash
# 1. Installer Heroku CLI
curl https://cli.heroku.com/install.sh | sh

# 2. Se connecter
heroku login

# 3. Créer l'app
heroku create image-search-api

# 4. Ajouter les addons
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create redistogo:nano

# 5. Déployer
git push heroku main

# 6. Voir les logs
heroku logs --tail
```

---

## 🔧 Configuration Production

### Variables d'Environnement Critiques

```env
ENVIRONMENT=production
DEBUG=False

# Security
QDRANT_API_KEY=your-strong-key-here
REDIS_PASSWORD=your-strong-password-here

# Model
MODEL_NAME=openai/CLIP-ViT-L-14
EMBEDDING_DIM=768

# Performance
CACHE_TTL=7200
TOP_K=20

# Monitoring
LOG_LEVEL=INFO
```

### Certificats HTTPS

```bash
# Générer certificats auto-signés (dev)
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Production: Utiliser Let's Encrypt
certbot certonly --standalone -d api.example.com
```

### Monitoring et Logs

```bash
# Docker: Voir les métriques
docker stats image-search-api

# K8s: Monitoring
kubectl top pods -n image-search

# Logs
kubectl logs -f deployment/image-search-api -n image-search
```

---

## 📊 Benchmarks de Charge

### Test avec Apache Bench

```bash
# 100 requêtes, 10 concurrent
ab -n 100 -c 10 http://localhost:8000/api/v1/health

# Résultats attendus:
# Requests per second: 500+
# Time per request: 2-5ms
```

### Test de Charge avec Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def search(self):
        self.client.post("/api/v1/search", json={
            "text_query": "red shirt",
            "top_k": 10
        })
```

```bash
locust -f locustfile.py --host=http://localhost:8000
```

---

## 🚨 Troubleshooting Deployment

### Erreur: "Out of Memory"
```bash
# Augmenter allocation
# Docker: Modifier docker-compose.yml
# K8s: Augmenter resources.limits.memory
```

### Erreur: "Model not loading"
```bash
# Vérifier les logs
docker logs <container-id>

# Rebuilder avec cache clear
docker-compose build --no-cache
```

### Performance lente
```bash
# Analyser les bottlenecks
# 1. Vérifier Qdrant collection stats
# 2. Vérifier Redis hit rate
# 3. Profiler avec Python cProfile
```

---

## ✅ Checklist Pré-Production

- [ ] Toutes les variables d'env configurées
- [ ] API_KEY Qdrant changée
- [ ] Redis PASSWORD configuré
- [ ] HTTPS/SSL configuré
- [ ] Logs centralisés (ELK, Datadog, etc.)
- [ ] Monitoring en place (Prometheus, etc.)
- [ ] Backups configurés
- [ ] Rate limiting activé
- [ ] CORS configuré correctement
- [ ] Tests de charge réussis
- [ ] Disaster recovery plan

---

## 📞 Support

Pour questions ou problèmes :
- Consulter les logs : `docker-compose logs -f`
- Vérifier santé : `curl http://localhost:8000/api/v1/health`
- Accéder aux docs : `http://localhost:8000/docs`
