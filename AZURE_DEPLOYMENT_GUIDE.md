╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║         🚀 GUIDE DE DÉPLOIEMENT COMPLET - AZURE APP SERVICE B1                 ║
║              Image Search API - Pas à pas avec Azure CLI                       ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

⏱️  TEMPS TOTAL: ~45 minutes

════════════════════════════════════════════════════════════════════════════════

PRÉREQUIS À VÉRIFIER
════════════════════════════════════════════════════════════════════════════════

Avant de commencer, assurez-vous d'avoir:

✅ 1. Compte Azure
   └─ Créer gratuitement: https://azure.microsoft.com/free/
   └─ Crédit gratuit: $200 pour 30 jours

✅ 2. Azure CLI installé
   Windows:
   └─ https://aka.ms/azure-cli
   └─ Ou via Chocolatey: choco install azure-cli
   
   Vérifier: 
   az --version

✅ 3. Git installé
   └─ https://git-scm.com/
   └─ Vérifier: git --version

✅ 4. Compte GitHub (optionnel mais recommandé)
   └─ Pour déploiement continu

✅ 5. Code du projet prêt
   └─ Le projet est déjà dans: c:\Users\edou\Desktop\IAAPP\image-search-api


════════════════════════════════════════════════════════════════════════════════

PHASE 1: CONFIGURATION INITIALE AZURE (5 min)
════════════════════════════════════════════════════════════════════════════════

ÉTAPE 1️⃣ : Se connecter à Azure
────────────────────────────────

Ouvrez PowerShell/CMD et tapez:

```
az login
```

✅ Cela ouvrira un navigateur pour vous authentifier
✅ Une fois connecté, vous verrez vos souscriptions


ÉTAPE 2️⃣ : Définir votre souscription (si plusieurs)
────────────────────────────────────────────────────

```
az account list --output table
```

Copier l'ID de votre souscription, puis:

```
az account set --subscription "YOUR-SUBSCRIPTION-ID"
```


ÉTAPE 3️⃣ : Créer un groupe de ressources
──────────────────────────────────────────

Un groupe regroupe tous vos services Azure (App Service, Redis, etc.)

```
az group create --name image-search-rg --location eastus
```

⚠️  Region importante:
   • eastus = Moins cher (~15% moins que Europe)
   • westeurope = Proche de la France (mais +15%)

✅ Réponse attendue:
   "provisioningState": "Succeeded"


════════════════════════════════════════════════════════════════════════════════

PHASE 2: CRÉER L'APP SERVICE PLAN (3 min)
════════════════════════════════════════════════════════════════════════════════

ÉTAPE 4️⃣ : Créer le plan B1
────────────────────────────

Le plan définit les ressources (CPU, RAM)

```
az appservice plan create --name image-search-plan \
                          --resource-group image-search-rg \
                          --sku B1 \
                          --is-linux
```

Paramètres:
  • --name: Nom du plan (unique)
  • --sku B1: Plan Basic (1 vCPU, 1.75GB RAM)
  • --is-linux: Pour Python sur Linux (plus léger)

✅ Coût: $13.20/mois


════════════════════════════════════════════════════════════════════════════════

PHASE 3: CRÉER L'APP SERVICE (5 min)
════════════════════════════════════════════════════════════════════════════════

ÉTAPE 5️⃣ : Créer la Web App Python
────────────────────────────────────

```
az webapp create --resource-group image-search-rg \
                 --plan image-search-plan \
                 --name image-search-api-123 \
                 --runtime "PYTHON|3.11" \
                 --deployment-local-git
```

⚠️  IMPORTANT:
   • --name doit être UNIQUE (Azure empêche les doublons)
   • Ajouter un suffixe: image-search-api-XXXX
   • Ne pas utiliser d'espaces ou underscores

✅ Réponse attendue:
```
{
  "ftpPublishingUrl": "ftp://waws...",
  "id": "/subscriptions/.../image-search-api-123",
  "name": "image-search-api-123",
  "resourceGroup": "image-search-rg"
}
```

Notez le "name" pour plus tard!


ÉTAPE 6️⃣ : Configurer les variables d'environnement
───────────────────────────────────────────────────

Remplacez "image-search-api-123" par VOTRE NOM:

```
az webapp config appsettings set \
   --resource-group image-search-rg \
   --name image-search-api-123 \
   --settings \
      QDRANT_HOST="https://your-qdrant-url.qdrant.io" \
      QDRANT_API_KEY="your-qdrant-api-key" \
      REDIS_HOST="your-redis-host.redis.cache.windows.net" \
      REDIS_PORT="6379" \
      REDIS_PASSWORD="your-redis-password" \
      ENVIRONMENT="production" \
      WEBSITES_PORT="8000" \
      SCM_DO_BUILD_DURING_DEPLOYMENT="true"
```

⚠️  Vous allez remplir ces valeurs plus tard!
    Pour maintenant, mettez des placeholder


════════════════════════════════════════════════════════════════════════════════

PHASE 4: CRÉER REDIS AZURE (5 min)
════════════════════════════════════════════════════════════════════════════════

ÉTAPE 7️⃣ : Créer Azure Cache for Redis
─────────────────────────────────────────

```
az redis create --resource-group image-search-rg \
                --name image-search-redis-123 \
                --location eastus \
                --sku basic \
                --vm-size c0 \
                --enable-non-ssl-port true
```

Paramètres:
  • --sku basic: Plan Basic ($15/mois)
  • --vm-size c0: 250MB (suffisant)
  • --enable-non-ssl-port: Pour déploiement simple

⏳ Attendre 5-10 minutes pour création...

```
az redis show --resource-group image-search-rg \
              --name image-search-redis-123
```

✅ Notez:
   • "hostName": Votre REDIS_HOST
   • "port": 6379


ÉTAPE 8️⃣ : Récupérer la clé Redis
──────────────────────────────────

```
az redis list-keys --resource-group image-search-rg \
                   --name image-search-redis-123
```

✅ Copier:
   • "primaryKey": Votre REDIS_PASSWORD


════════════════════════════════════════════════════════════════════════════════

PHASE 5: CONFIGURER QDRANT CLOUD (5 min)
════════════════════════════════════════════════════════════════════════════════

ÉTAPE 9️⃣ : S'inscrire à Qdrant Cloud
─────────────────────────────────────

1. Aller sur: https://cloud.qdrant.io
2. Cliquer "Sign up" (gratuit)
3. Créer compte avec email

4. Une fois connecté:
   • Cliquer "Create Cluster"
   • Nom: "image-search"
   • Plan: FREE (gratuit!)
   • Region: us-east-1 (proche d'Azure East US)

5. Attendre création (~2 min)

6. Une fois créé, cliquer sur le cluster
   • Copier URL: https://xxxxx-qdrant.io
   • Copier API Key

ÉTAPE 🔟 : Mettre à jour variables Azure
─────────────────────────────────────────

```
az webapp config appsettings set \
   --resource-group image-search-rg \
   --name image-search-api-123 \
   --settings \
      QDRANT_HOST="https://xxxxx-qdrant.io" \
      QDRANT_API_KEY="your-actual-api-key" \
      REDIS_HOST="image-search-redis-123.redis.cache.windows.net" \
      REDIS_PASSWORD="your-actual-redis-password"
```


════════════════════════════════════════════════════════════════════════════════

PHASE 6: PRÉPARER LE CODE POUR DÉPLOIEMENT (10 min)
════════════════════════════════════════════════════════════════════════════════

ÉTAPE 1️⃣1️⃣ : Naviguer vers le projet
──────────────────────────────────────

```
cd c:\Users\edou\Desktop\IAAPP\image-search-api
```

ÉTAPE 1️⃣2️⃣ : Vérifier requirements.txt
─────────────────────────────────────────

Ouvrir le fichier et vérifier qu'il contient:

```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.2
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
gunicorn==21.2.0
```

Si absent, l'ajouter!

ÉTAPE 1️⃣3️⃣ : Créer fichier startup.sh
──────────────────────────────────────

Créer un fichier nommé `startup.sh` à la racine:

```bash
#!/bin/bash
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting Gunicorn server..."
exec gunicorn --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    app.main:app
```

ÉTAPE 1️⃣4️⃣ : Configurer startup command
────────────────────────────────────────

```
az webapp config set \
   --resource-group image-search-rg \
   --name image-search-api-123 \
   --startup-file "startup.sh"
```

ÉTAPE 1️⃣5️⃣ : Créer fichier .gitignore (si absent)
─────────────────────────────────────────────────

À la racine du projet, créer/vérifier `.gitignore`:

```
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
env/
*.egg-info/
.env
.DS_Store
.idea/
*.log
```

ÉTAPE 1️⃣6️⃣ : Vérifier .git
───────────────────────────

```
git status
```

Si pas de repo:
```
git init
git add .
git commit -m "Initial commit for Azure deployment"
```


════════════════════════════════════════════════════════════════════════════════

PHASE 7: DÉPLOYER LE CODE (15 min)
════════════════════════════════════════════════════════════════════════════════

ÉTAPE 1️⃣7️⃣ : Configurer déploiement Git local
──────────────────────────────────────────────

```
az webapp deployment source config-local-git \
   --resource-group image-search-rg \
   --name image-search-api-123
```

✅ Cela vous retourne une URL Git, par exemple:
   https://edoukou07@image-search-api-123.scm.azurewebsites.net/image-search-api-123.git


ÉTAPE 1️⃣8️⃣ : Ajouter remote Azure à Git
──────────────────────────────────────────

Remplacez l'URL par celle retournée:

```
git remote add azure https://edoukou07@image-search-api-123.scm.azurewebsites.net/image-search-api-123.git
```

Vérifier:
```
git remote -v
```


ÉTAPE 1️⃣9️⃣ : Déployer le code!
─────────────────────────────────

```
git push azure main
```

Si vous êtes sur "master":
```
git push azure master:main
```

⏳ Attendre le déploiement (~5 minutes)

✅ Vous verrez des messages comme:
   "Counting objects..."
   "Installing dependencies..."
   "Starting app..."


ÉTAPE 2️⃣0️⃣ : Vérifier les logs
───────────────────────────────

```
az webapp log tail --name image-search-api-123 \
                   --resource-group image-search-rg
```

Cherchez:
  ✅ "Application startup complete"
  ✅ "Uvicorn running on 0.0.0.0:8000"


════════════════════════════════════════════════════════════════════════════════

PHASE 8: TESTER L'API (5 min)
════════════════════════════════════════════════════════════════════════════════

ÉTAPE 2️⃣1️⃣ : Obtenir l'URL de votre app
─────────────────────────────────────────

```
az webapp show --resource-group image-search-rg \
               --name image-search-api-123 \
               --query defaultHostName --output tsv
```

✅ Résultat: image-search-api-123.azurewebsites.net


ÉTAPE 2️⃣2️⃣ : Tester Health Check
──────────────────────────────────

```
curl https://image-search-api-123.azurewebsites.net/api/v1/health
```

✅ Réponse attendue:
```json
{
  "status": "healthy",
  "qdrant_connected": true,
  "redis_connected": true,
  "model_loaded": true
}
```

Si erreurs:
  ❌ "model_loaded": false
  → Attendre 2-3 min, CLIP se télécharge

  ❌ "redis_connected": false
  → Vérifier variables d'environnement Redis

  ❌ "qdrant_connected": false
  → Vérifier variables d'environnement Qdrant


ÉTAPE 2️⃣3️⃣ : Accéder à la documentation
──────────────────────────────────────────

Ouvrir dans navigateur:
https://image-search-api-123.azurewebsites.net/docs

✅ Vous verrez Swagger UI avec tous les endpoints!


ÉTAPE 2️⃣4️⃣ : Tester indexation produit
─────────────────────────────────────────

Via Swagger UI:
1. Cliquer sur "POST /api/v1/index-product"
2. Cliquer "Try it out"
3. Remplacer le JSON:

```json
{
  "id": "prod_test_001",
  "name": "Test Product",
  "description": "A test product",
  "image_url": "https://via.placeholder.com/400",
  "category": "test",
  "price": 29.99,
  "attributes": {"color": "red"}
}
```

4. Cliquer "Execute"

✅ Réponse attendue:
```json
{
  "status": "success",
  "product_id": "prod_test_001"
}
```


ÉTAPE 2️⃣5️⃣ : Tester recherche
──────────────────────────────

Via Swagger UI:
1. Cliquer sur "POST /api/v1/search"
2. Cliquer "Try it out"
3. Remplacer le JSON:

```json
{
  "text_query": "red product",
  "top_k": 5
}
```

4. Cliquer "Execute"

✅ Réponse attendue:
```json
{
  "query_type": "text",
  "top_k": 5,
  "total_results": 1,
  "results": [
    {
      "product_id": "prod_test_001",
      "name": "Test Product",
      "similarity_score": 0.95,
      "price": 29.99,
      "category": "test"
    }
  ],
  "execution_time_ms": 245.3
}
```


════════════════════════════════════════════════════════════════════════════════

✅ DÉPLOIEMENT RÉUSSI!
════════════════════════════════════════════════════════════════════════════════

Félicitations! Votre app est en production! 🎉

URL de l'API:
  https://image-search-api-123.azurewebsites.net

Documentation interactive:
  https://image-search-api-123.azurewebsites.net/docs

Endpoints:
  POST https://image-search-api-123.azurewebsites.net/api/v1/search
  POST https://image-search-api-123.azurewebsites.net/api/v1/index-product
  GET https://image-search-api-123.azurewebsites.net/api/v1/health
  GET https://image-search-api-123.azurewebsites.net/api/v1/collections


════════════════════════════════════════════════════════════════════════════════

🔧 COMMANDES UTILES APRÈS DÉPLOIEMENT
════════════════════════════════════════════════════════════════════════════════

Voir les logs:
```
az webapp log tail --name image-search-api-123 \
                   --resource-group image-search-rg \
                   --follow
```

Redémarrer l'app:
```
az webapp restart --name image-search-api-123 \
                  --resource-group image-search-rg
```

Voir les variables d'environnement:
```
az webapp config appsettings list --name image-search-api-123 \
                                  --resource-group image-search-rg
```

Mettre à jour une variable:
```
az webapp config appsettings set \
   --name image-search-api-123 \
   --resource-group image-search-rg \
   --settings VARIABLE_NAME="new_value"
```

Voir les métriques:
```
az monitor metrics list --resource /subscriptions/SUB_ID/resourceGroups/image-search-rg/providers/Microsoft.Web/sites/image-search-api-123
```

Supprimer tout (attention!):
```
az group delete --name image-search-rg
```


════════════════════════════════════════════════════════════════════════════════

⚠️  TROUBLESHOOTING
════════════════════════════════════════════════════════════════════════════════

PROBLÈME 1: "502 Bad Gateway"
───────────────────────────────
Cause: App ne démarre pas
Solution:
  1. Vérifier les logs: az webapp log tail ...
  2. Attendre 3-5 min (CLIP se télécharge)
  3. Redémarrer: az webapp restart ...


PROBLÈME 2: "qdrant_connected: false"
──────────────────────────────────────
Cause: Variables d'environnement incorrectes
Solution:
  1. Vérifier les valeurs: az webapp config appsettings list ...
  2. Vérifier l'URL Qdrant Cloud
  3. Vérifier l'API key
  4. Redéployer les settings


PROBLÈME 3: "redis_connected: false"
──────────────────────────────────────
Cause: Redis non accessible
Solution:
  1. Vérifier que Azure Cache for Redis a démarré
  2. Vérifier les variables REDIS_HOST et REDIS_PASSWORD
  3. Vérifier les firewall/ACL Azure


PROBLÈME 4: "Module not found" ou "ImportError"
─────────────────────────────────────────────────
Cause: Dépendances manquantes
Solution:
  1. Vérifier requirements.txt
  2. Ajouter la dépendance manquante
  3. Redéployer: git push azure main


PROBLÈME 5: App trop lente
──────────────────────────
Cause: Plan B1 limité (CPU partagé)
Solution:
  1. Scaler vers B2 (+$14/mois)
  2. Ou S1 Standard (+$42/mois)
  3. Attendre que CLIP soit chargé


════════════════════════════════════════════════════════════════════════════════

📊 COÛTS MENSUELS VÉRIFIÉS
════════════════════════════════════════════════════════════════════════════════

App Service Plan B1        $13.20
Azure Cache Redis Basic    $15.30
Qdrant Cloud Free           $0.00
Monitoring (free tier)      $0.00
─────────────────────────────────
TOTAL                      ~$28.50/mois

Plus taxes (10% en moyenne) = ~$31/mois


════════════════════════════════════════════════════════════════════════════════

🎯 PROCHAINES ÉTAPES
════════════════════════════════════════════════════════════════════════════════

1. ✅ Tester l'API en production
2. 📈 Monitorer les performances
3. 🔄 Configurer déploiement continu (GitHub)
4. 🔐 Ajouter authentification si besoin
5. 📊 Configurer alertes de coûts
6. 🚀 Scaler si augmentation trafic


════════════════════════════════════════════════════════════════════════════════

Des questions? Besoin d'aide?

Les logs sont vos amis: az webapp log tail ...
La documentation: https://docs.microsoft.com/azure/

Bon déploiement! 🚀
