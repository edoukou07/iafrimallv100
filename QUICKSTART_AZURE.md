═══════════════════════════════════════════════════════════════════════════════
                     GUIDE RAPIDE - DEPLOYER SUR AZURE
═══════════════════════════════════════════════════════════════════════════════

Ce guide vous explique comment déployer votre Image Search API sur Azure
en 45 minutes environ.

═══════════════════════════════════════════════════════════════════════════════

PREREQUIS (À installer d'abord)
───────────────────────────────────────────────────────────────────────────────

1. Azure CLI
   ├─ Télécharger: https://aka.ms/azure-cli
   ├─ Installation Windows: Exécuter le .msi
   └─ Vérifier: Ouvrir PowerShell et taper "az --version"

2. Git
   ├─ Télécharger: https://git-scm.com/
   ├─ Installation: Accepter les paramètres par défaut
   └─ Vérifier: Ouvrir PowerShell et taper "git --version"

3. Compte Azure
   ├─ Créer gratuitement: https://azure.microsoft.com/free/
   ├─ Obtenir $200 de crédit pour 30 jours
   └─ Nécessaire pour déployer

═══════════════════════════════════════════════════════════════════════════════

ÉTAPE 1: SE CONNECTER À AZURE (2 min)
───────────────────────────────────────────────────────────────────────────────

Ouvrez PowerShell et exécutez:

    az login

Un navigateur s'ouvrira pour vous authentifier. Une fois fait, PowerShell
affichera vos informations Azure.

═══════════════════════════════════════════════════════════════════════════════

ÉTAPE 2: CRÉER UN CLUSTER QDRANT (5 min)
──────────────────────────────────────────────────────────────────────────────

Pendant que vous attendez, créons le cluster Qdrant:

1. Aller sur: https://cloud.qdrant.io
2. Créer un compte (email + mot de passe)
3. Cliquer "Create Cluster"
4. Nom: "image-search"
5. Plan: "FREE" (gratuit!)
6. Region: us-east-1
7. Cliquer "Create"
8. Attendre 2-3 minutes
9. Une fois créé:
   ├─ Copier l'URL (ressemble à: https://xxxxx-qdrant.io)
   └─ Copier l'API Key

Gardez ces deux valeurs à portée de main!

═══════════════════════════════════════════════════════════════════════════════

ÉTAPE 3: EXÉCUTER LE SCRIPT DE DÉPLOIEMENT (35 min)
────────────────────────────────────────────────────────────────────────────

Ouvrez PowerShell ET CHANGEZ DE RÉPERTOIRE:

    cd c:\Users\edou\Desktop\IAAPP\image-search-api

Exécutez le script (remplacez "VOTREAPPNAME" par un nom unique):

    .\deploy-to-azure.ps1 -AppName "image-search-api-VOTREAPPNAME"

Exemples de noms valides:
  ✓ image-search-api-edou
  ✓ image-search-api-123
  ✓ image-search-my-app
  ✓ produit-search-api

Points importants:
  • Le nom DOIT être unique (Azure empêche les doublons)
  • Utiliser uniquement des lettres, chiffres, traits d'union
  • Max 45 caractères
  • Pas d'espaces ou caractères spéciaux

Le script va:
  1. Créer un groupe de ressources Azure
  2. Créer un plan App Service B1
  3. Créer l'App Service
  4. Créer Redis Cache
  5. Configurer toutes les variables
  6. Déployer le code via Git

Cela prend environ 20-30 minutes.

═══════════════════════════════════════════════════════════════════════════════

ÉTAPE 4: CONFIGURER QDRANT (3 min)
───────────────────────────────────────────────────────────────────────────────

Une fois le script terminé, il affichera une commande à exécuter.

Exécutez cette commande (remplacez les valeurs Qdrant):

    az webapp config appsettings set `
       -g image-search-rg `
       -n image-search-api-VOTREAPPNAME `
       --settings `
          QDRANT_HOST="https://xxxxx-qdrant.io" `
          QDRANT_API_KEY="votre-clé-api-ici"

Remplacez:
  • image-search-api-VOTREAPPNAME par votre APP NAME
  • https://xxxxx-qdrant.io par l'URL Qdrant copiée plus tôt
  • votre-clé-api-ici par la clé API Qdrant

═══════════════════════════════════════════════════════════════════════════════

ÉTAPE 5: ATTENDRE ET VÉRIFIER (5 min)
──────────────────────────────────────────────────────────────────────────────

Attendre 2-3 minutes (CLIP doit se télécharger).

Puis exécutez:

    az webapp log tail -n image-search-api-VOTREAPPNAME -g image-search-rg

Vous verrez les logs. Attendez de voir:
  ✅ "Application startup complete"
  ✅ "Uvicorn running on 0.0.0.0:8000"

Sinon, attendez 2-3 minutes de plus.

═══════════════════════════════════════════════════════════════════════════════

ÉTAPE 6: TESTER L'API (2 min)
─────────────────────────────────────────────────────────────────────────────

Ouvrez votre navigateur et allez à:

    https://image-search-api-VOTREAPPNAME.azurewebsites.net/api/v1/health

Vous devriez voir une réponse JSON:
{
  "status": "healthy",
  "qdrant_connected": true,
  "redis_connected": true,
  "model_loaded": true
}

Si "model_loaded" est false, attendez 2 minutes et réessayez.

═══════════════════════════════════════════════════════════════════════════════

ÉTAPE 7: ACCÉDER À LA DOCUMENTATION (BONUS)
──────────────────────────────────────────────────────────────────────────────

Accédez à Swagger UI (documentation interactive):

    https://image-search-api-VOTREAPPNAME.azurewebsites.net/docs

Vous pouvez essayer les endpoints directement!

Par exemple, indexer un produit:
  1. Cliquer sur "POST /api/v1/index-product"
  2. Cliquer "Try it out"
  3. Entrer un JSON produit
  4. Cliquer "Execute"

Puis chercher:
  1. Cliquer sur "POST /api/v1/search"
  2. Cliquer "Try it out"
  3. Entrer "text_query": "your search here"
  4. Cliquer "Execute"

═══════════════════════════════════════════════════════════════════════════════

PROBLÈMES COURANTS
───────────────────────────────────────────────────────────────────────────────

❌ ERREUR: "502 Bad Gateway"
   └─ Solution: Attendre 3-5 minutes (CLIP se télécharge)
              Vérifier les logs: az webapp log tail ...

❌ ERREUR: "qdrant_connected: false"
   └─ Solution: Vérifier l'URL et la clé API Qdrant
              Vérifier que le cluster Qdrant Cloud est démarré

❌ ERREUR: "redis_connected: false"
   └─ Solution: Vérifier que Redis a bien été créé
              Voir: az redis show -n image-search-redis-123 -g image-search-rg

❌ ERREUR: "model_loaded: false"
   └─ Solution: Attendre 2-3 minutes de plus
              CLIP (~500MB) doit se télécharger depuis HuggingFace

❌ ERREUR: Application trop lente
   └─ Solution: Plan B1 a un CPU limité
              Scaler vers B2 (+$14/mois) ou S1 (+$42/mois)

═══════════════════════════════════════════════════════════════════════════════

COÛTS
─────────────────────────────────────────────────────────────────────────────

Service                          Coût mensuel
────────────────────────────────────────────────
App Service Plan B1              $13.20
Azure Cache for Redis Basic      $15.30
Qdrant Cloud (gratuit)           $0.00
────────────────────────────────────────────────
TOTAL                            ~$31/mois

Remarques:
  • Les prix sont en USD
  • B1 = 1 vCPU, 1.75GB RAM, suffisant pour ~500k produits
  • Redis = 250MB cache, bon pour requêtes fréquentes
  • Qdrant Free = 30GB, ~500k vecteurs

═══════════════════════════════════════════════════════════════════════════════

APRÈS LE DÉPLOIEMENT
──────────────────────────────────────────────────────────────────────────────

✓ URLs à retenir:
  API: https://image-search-api-VOTREAPPNAME.azurewebsites.net
  Docs: https://image-search-api-VOTREAPPNAME.azurewebsites.net/docs
  Health: https://image-search-api-VOTREAPPNAME.azurewebsites.net/api/v1/health

✓ Commandes courantes:

  Voir les logs en direct:
  az webapp log tail -n image-search-api-VOTREAPPNAME -g image-search-rg --follow

  Redémarrer l'app:
  az webapp restart -n image-search-api-VOTREAPPNAME -g image-search-rg

  Voir les variables d'environnement:
  az webapp config appsettings list -n image-search-api-VOTREAPPNAME -g image-search-rg

  Redéployer le code (après une modification):
  cd c:\Users\edou\Desktop\IAAPP\image-search-api
  git push azure main

  Supprimer tout (attention!):
  az group delete -n image-search-rg

═══════════════════════════════════════════════════════════════════════════════

BESOIN D'AIDE?
──────────────────────────────────────────────────────────────────────────────

Documentation:
  • Azure App Service: https://docs.microsoft.com/azure/app-service/
  • Qdrant: https://qdrant.tech/documentation/
  • FastAPI: https://fastapi.tiangolo.com/

Pour plus de détails sur le déploiement:
  → Lire AZURE_DEPLOYMENT_GUIDE.md (guide complet 50 étapes)
  → Lire DEPLOYMENT_CHECKLIST.md (checklist interactive)

═══════════════════════════════════════════════════════════════════════════════
