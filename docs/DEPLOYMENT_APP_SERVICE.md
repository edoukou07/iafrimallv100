╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║     💰 ESTIMATION COMPLÈTE - AZURE APP SERVICE PLAN B1 (DÉMARRAGE)             ║
║              Image Search API - CLIP + Qdrant + Redis                         ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

📚 TABLE DES MATIÈRES
════════════════════════════════════════════════════════════════════════════════
1. Vue d'ensemble App Service Plan B1
2. Détail des coûts
3. Configuration recommandée
4. Exemple de facture complète
5. Procédure de déploiement pas à pas
6. Fichiers de configuration
7. Tests et validation
8. Scénarios de croissance

════════════════════════════════════════════════════════════════════════════════

1️⃣ VUE D'ENSEMBLE - AZURE APP SERVICE PLAN B1
════════════════════════════════════════════════════════════════════════════════

QU'EST-CE QUE C'EST?
───────────────────

Azure App Service = Plateforme managée pour déployer des applications web/API
Plan B1 = Tier "Basic" (entrée de gamme, bon pour démarrer)

SPÉCIFICATIONS DU PLAN B1:
─────────────────────────

Ressources:
├─ Processeur: 1 vCPU partagé (peut être limité)
├─ RAM: 1.75 GB
├─ Stockage: 10 GB
├─ Instances: 1 minimum
└─ FTP/SFTP: Inclus

Caractéristiques:
├─ Domaine personnalisé: Oui
├─ Certificat SSL: Gratuit (*.azurewebsites.net)
├─ Auto-scaling: NON (plan fixe)
├─ Déploiement continu: Oui (Git/GitHub)
├─ Monitoring: Basic (logs App Service)
└─ SLA: 99.95% (contrat de service)

COMPARAISON AVEC AUTRES PLANS:
──────────────────────────────

Plan        │ vCPU  │ RAM   │ Stockage │ Coût/mois │ Auto-scaling
════════════╪═══════╪═══════╪══════════╪═══════════╪═════════════
Free        │ Shared│ 1GB   │ 1GB      │ $0        │ Non
Shared      │ Shared│ 1GB   │ 1GB      │ $9-13     │ Non
B1 (Basic)  │ 1     │ 1.75GB│ 10GB     │ $13-18    │ Non ✅ CHOIX
B2 (Basic)  │ 2     │ 3.5GB │ 10GB     │ $27       │ Non
S1 (Std)    │ 1     │ 1.75GB│ 50GB     │ $55       │ Oui
════════════╧═══════╧═══════╧══════════╧═══════════╧═════════════

════════════════════════════════════════════════════════════════════════════════

2️⃣ DÉTAIL DES COÛTS - BREAKDOWN COMPLET
════════════════════════════════════════════════════════════════════════════════

COÛT 1: APP SERVICE PLAN B1
─────────────────────────────

Région: East US (moins cher)
┌─────────────────────────────────┐
│ App Service Plan B1             │
├─────────────────────────────────┤
│ Coût par heure: $0.018          │
│ Coût par jour: $0.432           │
│ Coût par mois: $13.20           │
└─────────────────────────────────┘

Calcul: $0.018/h × 730h (24h × 30.4j) = $13.20/mois

⚠️ Régions plus chères:
  └─ West Europe: +15% = $15.18/mois
  └─ France: +20% = $15.84/mois


COÛT 2: AZURE CACHE FOR REDIS
──────────────────────────────

Stockage des résultats recherche

Tier Basic (petit):
┌──────────────────────────────────────┐
│ Redis Cache (Basic, 250MB)           │
├──────────────────────────────────────┤
│ Coût par mois: $15.30                │
│ Bande passante: 256MB                │
│ Connexions simultanées: 256          │
│ Performance: 100 req/sec              │
└──────────────────────────────────────┘

Recommandation:
  • Petit dataset: 250MB = $15/mois
  • Dataset moyen: 1GB = $24/mois
  • Gros dataset: 6GB = $75/mois

Pour votre app: 250MB suffit largement!
(Cache TTL 1h = données effacées = pas besoin énorme)


COÛT 3: QDRANT CLOUD (Vector Database)
───────────────────────────────────────

Deux options:

OPTION A: Qdrant Cloud Managed (Facile)
┌────────────────────────────────────┐
│ Qdrant Cloud Free Tier             │
├────────────────────────────────────┤
│ Coût: $0 (GRATUIT!)                │
│ Storage: 30 GB                     │
│ Produits: ~500k (max)              │
│ Performance: Limitée               │
│ Haute disponibilité: Non           │
│                                    │
│ → PARFAIT pour démarrer!           │
└────────────────────────────────────┘

Upgrade si besoin:
  Paid tier: $99-299+/mois (selon données)


OPTION B: Qdrant Self-Hosted (Contrôle)
┌────────────────────────────────────┐
│ Azure Container Instance (Qdrant)  │
├────────────────────────────────────┤
│ Coût: $20-40/mois                  │
│ Storage: 100GB                     │
│ Performance: Bonne                 │
└────────────────────────────────────┘

⚠️ Complexité: Plus à gérer


RECOMMANDATION POUR DÉMARRER:
  ✅ Qdrant Cloud FREE Tier
  └─ $0/mois
  └─ Suffit pour tester
  └─ Upgrade facile plus tard


COÛT 4: STORAGE AZURE (si self-hosted Qdrant)
───────────────────────────────────────────────

Si vous hébergez Qdrant vous-même (optionnel):

Storage Account:
├─ 100GB données: $2.30/mois
├─ Transactions: ~$0.50/mois
└─ Total: $2.80/mois

⚠️ À ignorer si utilisation Qdrant Cloud


COÛT 5: DOMAIN & SSL
─────────────────────

Domaine personnalisé:
├─ Avec Qdrant Cloud: Inclus dans App Service
├─ SSL: Gratuit (*.azurewebsites.net fourni)
└─ Domaine perso (.com): $10-15/an (optionnel)


COÛT 6: MONITORING & LOGGING
──────────────────────────────

Application Insights:
├─ Gratuit tier: 5GB/mois
├─ Logs App Service: Gratuit (limité)
├─ Monitoring basique: $0
└─ Advanced monitoring: $2.99/GB (si dépassement)

Pour démarrer: $0


════════════════════════════════════════════════════════════════════════════════

3️⃣ CONFIGURATION RECOMMANDÉE - DÉMARRAGE
════════════════════════════════════════════════════════════════════════════════

ARCHITECTURE:
──────────────

┌─────────────────────────────────────────────────┐
│         Azure App Service (B1)                  │
│         Port 8000 - FastAPI                     │
│         ┌───────────────────────────────────┐   │
│         │ Image Search API                  │   │
│         │ - CLIP embeddings                 │   │
│         │ - Search orchestration            │   │
│         └───────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
         │
         ├─────────────────────┬────────────────┐
         │                     │                │
    ┌────▼────┐         ┌─────▼──┐      ┌──────▼──┐
    │ Qdrant  │         │ Redis  │      │  CDN    │
    │ Cloud   │         │ Azure  │      │(optionl)│
    │ FREE    │         │ Cache  │      │         │
    │ Tier    │         │ Basic  │      │  $19/mois
    │ $0      │         │ $15/mois       │         │
    └────────┘         └────────┘      └─────────┘


SERVICES SÉLECTIONNÉS:
──────────────────────

1. App Service Plan B1
   ├─ Pour: FastAPI application
   ├─ Coût: $13.20/mois
   └─ Région: East US

2. Azure Cache for Redis (Basic, 250MB)
   ├─ Pour: Cache résultats recherche
   ├─ Coût: $15.30/mois
   └─ TTL: 1 heure (auto-expire)

3. Qdrant Cloud Free
   ├─ Pour: Vector database
   ├─ Coût: $0/mois (GRATUIT!)
   ├─ Storage: 30GB (suffit pour 500k produits)
   └─ Capacité: Démarrage

4. Application Insights
   ├─ Pour: Monitoring
   ├─ Coût: $0 (free tier 5GB)
   └─ Logs: Automatiques


════════════════════════════════════════════════════════════════════════════════

4️⃣ EXEMPLE DE FACTURE MENSUELLE COMPLÈTE
════════════════════════════════════════════════════════════════════════════════

FACTURE AZURE - NOVEMBRE 2025
─────────────────────────────

Account: Image Search API - MVP
Region: East US
Period: Nov 1-30, 2025

┌──────────────────────────────────────────────────────┐
│ COMPUTE                                              │
├──────────────────────────────────────────────────────┤
│ App Service Plan B1                  $13.20 USD      │
│ Compute Hours: 730 (24h × 30.4j)                    │
│                                                      │
├──────────────────────────────────────────────────────┤
│ CACHING                                              │
├──────────────────────────────────────────────────────┤
│ Azure Cache for Redis (250MB, Basic) $15.30 USD      │
│ Cache Operations: ~1.2M (gratuit)                   │
│                                                      │
├──────────────────────────────────────────────────────┤
│ DATABASE                                             │
├──────────────────────────────────────────────────────┤
│ Qdrant Cloud Free Tier                 $0.00 USD    │
│ (Gratuit jusqu'à 30GB et 500k produits)             │
│                                                      │
├──────────────────────────────────────────────────────┤
│ MONITORING                                           │
├──────────────────────────────────────────────────────┤
│ Application Insights (free tier)       $0.00 USD    │
│ (Inclus: 5GB/mois)                                 │
│                                                      │
├──────────────────────────────────────────────────────┤
│ STORAGE (Qdrant Cloud)                 $0.00 USD    │
│ (Inclus dans subscription Cloud)                   │
│                                                      │
├──────────────────────────────────────────────────────┤
│                                  SUBTOTAL: $28.50    │
│                                                      │
│ Taxes (varies by region):      ~$2.85 (10%)         │
│                                                      │
│                                    TOTAL: ~$31.35 USD│
└──────────────────────────────────────────────────────┘


COÛTS ARRONDIS MENSUELS:
────────────────────────

App Service          = $13
Redis Cache          = $15
Qdrant Cloud         = $0 (gratuit!)
Monitoring           = $0 (gratuit!)
─────────────────────
SUBTOTAL             = $28
Taxes (10% exemple)  = $3
─────────────────────
TOTAL MENSUEL        = ~$31

✅ MOINS DE 35 DOLLARS PAR MOIS POUR DÉMARRER!


COÛTS PAR JOUR:
───────────────

$31/mois ÷ 30 jours = ~$1/jour

C'est moins qu'un café! ☕


════════════════════════════════════════════════════════════════════════════════

5️⃣ PROCÉDURE DE DÉPLOIEMENT - ÉTAPE PAR ÉTAPE
════════════════════════════════════════════════════════════════════════════════

⏱️ TEMPS TOTAL: ~45 minutes

PRÉREQUIS:
───────────
✓ Compte Azure (créer sur azure.microsoft.com)
✓ Azure CLI installé (az command)
✓ Git installé
✓ Compte GitHub (pour déploiement)


PHASE 1: PRÉPARATION AZURE (10 min)
────────────────────────────────────

1️⃣ Se connecter à Azure:

   az login

   → Ouvre navigateur, connectez-vous


2️⃣ Créer groupe de ressources:

   az group create --name myResourceGroup \
                   --location eastus

   Réponse attendue:
   {
     "id": "/subscriptions/.../resourceGroups/myResourceGroup",
     "location": "eastus",
     "managedBy": null,
     "name": "myResourceGroup",
     "properties": {
       "provisioningState": "Succeeded"
     },
     "tags": null
   }


3️⃣ Créer App Service Plan B1:

   az appservice plan create --name myAppServicePlan \
                             --resource-group myResourceGroup \
                             --sku B1 \
                             --is-linux

   Réponse attendue: Plan créé avec succès


PHASE 2: CRÉER L'APP SERVICE (10 min)
──────────────────────────────────────

4️⃣ Créer Web App Python:

   az webapp create --resource-group myResourceGroup \
                    --plan myAppServicePlan \
                    --name image-search-api \
                    --runtime "PYTHON|3.11"

   Notes:
   ├─ --name doit être unique (ex: image-search-api-12345)
   ├─ URL sera: https://image-search-api.azurewebsites.net
   └─ Runtime: Python 3.11 (mis à jour automatiquement)


5️⃣ Configurer les variables d'environnement:

   az webapp config appsettings set \
      --resource-group myResourceGroup \
      --name image-search-api \
      --settings \
         QDRANT_HOST="your-qdrant-cloud-url" \
         QDRANT_API_KEY="your-qdrant-api-key" \
         REDIS_HOST="your-redis-host.redis.cache.windows.net" \
         REDIS_PORT="6379" \
         REDIS_PASSWORD="your-redis-password" \
         ENVIRONMENT="production" \
         WEBSITES_PORT="8000"

   Où trouver ces valeurs:
   ├─ QDRANT_HOST: https://cloud.qdrant.io (après créer cluster)
   ├─ REDIS_HOST: Azure Portal > Cache pour Redis


6️⃣ Configurer deployment depuis GitHub:

   a) Préparer votre repo GitHub:
      git clone https://github.com/edoukou07/iafrimallv100.git
      cd iafrimallv100/image-search-api

   b) Créer fichier .gitignore (s'il n'existe pas):
      echo "venv/" >> .gitignore
      echo "__pycache__/" >> .gitignore
      echo ".env" >> .gitignore

   c) Créer fichier oryx.yml pour Python (pour App Service):
      [voir PHASE 3]


PHASE 3: CONFIGURER POUR APP SERVICE (10 min)
──────────────────────────────────────────────

7️⃣ Créer fichier oryx.yml:

   cat > oryx.yml <<EOF
   version: 1
   build:
     env:
       - name: PYTHON_VERSION
         value: "3.11"
       - name: PIP_CACHE_DIR
         value: "/tmp/.cache"
   EOF


8️⃣ Créer fichier requirements.txt (s'il n'existe pas):

   pip freeze > requirements.txt

   OU utilisez celui existant du projet (devrait être là)


9️⃣ Créer fichier startup.sh:

   cat > startup.sh <<'EOF'
   #!/bin/bash
   echo "Installing dependencies..."
   pip install -r requirements.txt
   
   echo "Starting FastAPI server..."
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   EOF

   chmod +x startup.sh


🔟 Configurer App Service pour exécuter startup.sh:

   az webapp config set \
      --resource-group myResourceGroup \
      --name image-search-api \
      --startup-file "startup.sh"


PHASE 4: DÉPLOIEMENT (15 min)
──────────────────────────────

1️⃣1️⃣ Initialiser déploiement Git dans App Service:

   # Option A: via Azure CLI (plus simple)
   az webapp deployment source config-zip \
      --resource-group myResourceGroup \
      --name image-search-api \
      --src project.zip

   # Option B: via Git (continuous deployment)
   az webapp deployment user set \
      --user-name deploy-user \
      --password MySecurePassword123!

   az webapp deployment source config-local-git \
      --resource-group myResourceGroup \
      --name image-search-api

   # Copier l'URL Git retournée


1️⃣2️⃣ Pusher le code:

   git remote add azure <url-from-previous-step>
   git push azure main

   Cela va:
   ├─ Déployer le code
   ├─ Installer les dépendances (pip install)
   ├─ Démarrer l'application
   └─ Prendre 2-5 minutes


1️⃣3️⃣ Vérifier le déploiement:

   # Voir les logs
   az webapp log tail --name image-search-api \
                      --resource-group myResourceGroup

   # Ou via Azure Portal > App Service > Log stream


PHASE 5: CONFIGURER REDIS AZURE (10 min)
─────────────────────────────────────────

1️⃣4️⃣ Créer Azure Cache for Redis:

   az redis create --resource-group myResourceGroup \
                   --name image-search-redis \
                   --location eastus \
                   --sku basic \
                   --vm-size c0

   Résultat: Redis créé
   ├─ Host: image-search-redis.redis.cache.windows.net
   ├─ Port: 6379
   └─ Password: Généré automatiquement


1️⃣5️⃣ Récupérer la clé d'accès Redis:

   az redis list-keys --resource-group myResourceGroup \
                      --name image-search-redis

   Copier la primaryKey


1️⃣6️⃣ Mettre à jour variables d'environnement avec Redis réel:

   az webapp config appsettings set \
      --resource-group myResourceGroup \
      --name image-search-api \
      --settings \
         REDIS_HOST="image-search-redis.redis.cache.windows.net" \
         REDIS_PASSWORD="<primaryKey-from-above>"


PHASE 6: CONFIGURER QDRANT CLOUD (5 min)
──────────────────────────────────────────

1️⃣7️⃣ S'inscrire à Qdrant Cloud:

   1. Aller sur https://cloud.qdrant.io
   2. Sign up (gratuit)
   3. Créer cluster gratuit
   4. Copier URL et API key


1️⃣8️⃣ Mettre à jour variables Qdrant:

   az webapp config appsettings set \
      --resource-group myResourceGroup \
      --name image-search-api \
      --settings \
         QDRANT_HOST="https://your-cluster.qdrant.io" \
         QDRANT_API_KEY="your-api-key"


PHASE 7: TESTS & VALIDATION (5 min)
────────────────────────────────────

1️⃣9️⃣ Tester l'API:

   # Health check
   curl https://image-search-api.azurewebsites.net/api/v1/health

   Réponse attendue:
   {
     "status": "healthy",
     "qdrant_connected": true,
     "redis_connected": true,
     "model_loaded": true
   }


2️⃣0️⃣ Tester indexation produit:

   curl -X POST https://image-search-api.azurewebsites.net/api/v1/index-product \
     -H "Content-Type: application/json" \
     -d '{
       "id": "prod_001",
       "name": "Test Product",
       "image_url": "https://example.com/image.jpg",
       "category": "test",
       "price": 29.99
     }'


2️⃣1️⃣ Tester recherche:

   curl -X POST https://image-search-api.azurewebsites.net/api/v1/search \
     -H "Content-Type: application/json" \
     -d '{
       "text_query": "red shirt",
       "top_k": 5
     }'


════════════════════════════════════════════════════════════════════════════════

6️⃣ FICHIERS DE CONFIGURATION NÉCESSAIRES
════════════════════════════════════════════════════════════════════════════════

FICHIER 1: .env (Local - NE PAS committer!)
──────────────────────────────────────────

Créer `.env` dans le dossier racine:

QDRANT_HOST=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
ENVIRONMENT=development
LOG_LEVEL=INFO


FICHIER 2: startup.sh (pour Azure App Service)
──────────────────────────────────────────────

#!/bin/bash
set -e

echo "Starting application setup..."

# Update pip
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Set environment
export PYTHONUNBUFFERED=1

# Run migrations if needed
python -m alembic upgrade head 2>/dev/null || true

# Start Uvicorn
echo "Starting FastAPI application..."
exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info


FICHIER 3: requirements.txt (à vérifier/compléter)
──────────────────────────────────────────────────

fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.2
pydantic-settings==2.1.0
python-dotenv==1.0.0
aiofiles==23.2.1
redis==5.0.1
qdrant-client==2.7.0
transformers==4.35.2
torch==2.1.1
torchvision==0.16.1
pillow==10.1.0
numpy==1.24.3
python-multipart==0.0.6
aiohttp==3.9.1


FICHIER 4: web.config (Configuration IIS - Azure App Service)
─────────────────────────────────────────────────────────────

<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="HTTP to HTTPS redirect" stopProcessing="true">
          <match url="(.*)" />
          <conditions>
            <add input="{HTTPS}" pattern="^OFF$" />
          </conditions>
          <action type="Redirect" url="https://{HTTP_HOST}/{R:1}" redirectType="Permanent" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>


════════════════════════════════════════════════════════════════════════════════

7️⃣ TESTS & VALIDATION
════════════════════════════════════════════════════════════════════════════════

CHECKLIST DE VALIDATION:
───────────────────────

☐ App Service créée et fonctionnelle
  Vérifier: Azure Portal > App Service > Overview
  
☐ Code déployé correctement
  Vérifier: az webapp log tail --name image-search-api
  
☐ Variables d'environnement configurées
  Vérifier: Portal > Configuration > Application settings
  
☐ Redis Azure connecté
  Vérifier: Appeler /api/v1/health → redis_connected: true
  
☐ Qdrant Cloud connecté
  Vérifier: Appeler /api/v1/health → qdrant_connected: true
  
☐ API répond sur les endpoints
  Vérifier: curl https://image-search-api.azurewebsites.net/api/v1/health

☐ Indexation fonctionne
  Vérifier: POST /api/v1/index-product → status: success

☐ Recherche fonctionne
  Vérifier: POST /api/v1/search → results avec similarity_score


════════════════════════════════════════════════════════════════════════════════

8️⃣ SCÉNARIOS DE CROISSANCE - QUAND SCALER?
════════════════════════════════════════════════════════════════════════════════

QUAND CHANGER DE PLAN?
──────────────────────

Rester sur B1 si:
├─ < 1,000 requêtes/jour
├─ < 1 sec de latence acceptable
├─ 1 seule instance suffit
└─ Pas besoin auto-scaling

Monter à B2 si:
├─ 1,000-10,000 requêtes/jour
├─ 2 vCPU pour mieux traiter les pics
├─ CPU utilisation > 80%
└─ Coût: +115% ($27/mois vs $13)

Monter à S1 (Standard) si:
├─ 10,000+ requêtes/jour
├─ Besoin auto-scaling
├─ Multi-instances
└─ Coût: +315% ($55/mois vs $13)

CROISSANCE DE COÛTS:
───────────────────

Phase 1 (MVP - 1 mois):         $31/mois
  └─ B1 + Redis Basic + Qdrant free

Phase 2 (Croissance - 6 mois):  $80-120/mois
  ├─ B2 (2 vCPU)
  ├─ Redis Standard (1GB)
  └─ Qdrant Cloud Paid ($20-50)

Phase 3 (Production - 12 mois):  $200-500/mois
  ├─ S1 ou S2 (avec auto-scaling)
  ├─ Redis Premium
  └─ Qdrant Cloud ou self-hosted


════════════════════════════════════════════════════════════════════════════════

📊 RÉSUMÉ FINANCIER - PREMIER ANNÉE
════════════════════════════════════════════════════════════════════════════════

Mois 1-2 (MVP):
├─ Coût: $31/mois × 2 = $62
└─ Activités: Tests, intégration, premiers utilisateurs

Mois 3-6 (Croissance légère):
├─ Coût: $80/mois × 4 = $320
├─ Upgrade: B2, Redis augmentée
└─ Activités: Collecte feedback, optimisations

Mois 7-12 (Production):
├─ Coût: $200/mois × 6 = $1,200
├─ Upgrade: S1, Qdrant Paid
└─ Activités: Croissance utilisateurs, features

TOTAL ANNÉE 1: ~$1,582

C'est très économique pour une startup! 💰


════════════════════════════════════════════════════════════════════════════════

🎯 COMMANDES RAPIDES - RÉSUMÉ
════════════════════════════════════════════════════════════════════════════════

# Connexion
az login

# Créer groupe
az group create --name myResourceGroup --location eastus

# Créer App Service Plan
az appservice plan create --name myAppServicePlan \
                          --resource-group myResourceGroup \
                          --sku B1 --is-linux

# Créer Web App
az webapp create --resource-group myResourceGroup \
                 --plan myAppServicePlan \
                 --name image-search-api \
                 --runtime "PYTHON|3.11"

# Configurer variables
az webapp config appsettings set \
   --resource-group myResourceGroup \
   --name image-search-api \
   --settings QDRANT_HOST="..." REDIS_HOST="..." ...

# Déployer code
az webapp deployment source config-zip \
   --resource-group myResourceGroup \
   --name image-search-api \
   --src project.zip

# Voir logs
az webapp log tail --name image-search-api \
                   --resource-group myResourceGroup

# Créer Redis
az redis create --resource-group myResourceGroup \
                --name image-search-redis \
                --location eastus --sku basic --vm-size c0

# Obtenir clé Redis
az redis list-keys --resource-group myResourceGroup \
                   --name image-search-redis


════════════════════════════════════════════════════════════════════════════════

💡 CONSEILS IMPORTANTS
════════════════════════════════════════════════════════════════════════════════

1. RÉGIONS:
   • East US = Moins cher
   • Garder les services dans la même région (pas d'egress)

2. SÉCURITÉ:
   • NE PAS stocker secrets en clair
   • Utiliser Azure Key Vault pour secrets
   • HTTPS automatique

3. MONITORING:
   • Activer Application Insights
   • Configurer alertes budgétaires
   • Vérifier coûts mensuels

4. PERFORMANCE:
   • B1 a vCPU limité (peut être lent)
   • Monitor CPU/memory dans Portal
   • Scaler si > 80% utilisation

5. CONTINUITÉ:
   • Backups automatiques (inclus)
   • Déploiements depuis Git
   • Rollback facile


════════════════════════════════════════════════════════════════════════════════

📞 SUPPORT
════════════════════════════════════════════════════════════════════════════════

Documentation officielle:
  App Service: https://docs.microsoft.com/azure/app-service/
  Redis Cache: https://docs.microsoft.com/azure/azure-cache-for-redis/
  Qdrant Cloud: https://cloud.qdrant.io/docs

CLI Reference:
  https://docs.microsoft.com/cli/azure/

Pricing Calculator:
  https://azure.microsoft.com/pricing/calculator/


════════════════════════════════════════════════════════════════════════════════

Des questions? Je suis prêt à vous guider! 🚀
