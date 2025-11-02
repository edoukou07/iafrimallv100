═══════════════════════════════════════════════════════════════════════════════
                    ✅ CHECKLIST DE DÉPLOIEMENT AZURE
═══════════════════════════════════════════════════════════════════════════════

Temps estimé: 45 minutes
Coût estimé: ~$31/mois (B1 + Redis Basic + Qdrant Free)

═══════════════════════════════════════════════════════════════════════════════

PRÉPARATION (5 min)
───────────────────────────────────────────────────────────────────────────────

  ☐ 1. Installer Azure CLI (https://aka.ms/azure-cli)
       └─ Vérifier: az --version

  ☐ 2. S'authentifier Azure
       └─ Commande: az login

  ☐ 3. Installer Git (https://git-scm.com/)
       └─ Vérifier: git --version

  ☐ 4. Vérifier le projet dans: c:\Users\edou\Desktop\IAAPP\image-search-api
       └─ Vérifier que requirements.txt existe


DÉPLOIEMENT AUTOMATISÉ (35 min) - RECOMMANDÉ
───────────────────────────────────────────────────────────────────────────────

  ☐ 5. Exécuter le script PowerShell
       
       Ouvrir PowerShell et exécuter:
       
       cd c:\Users\edou\Desktop\IAAPP\image-search-api
       
       .\deploy-to-azure.ps1 -AppName "image-search-api-123" `
                             -ResourceGroup "image-search-rg" `
                             -Location "eastus" `
                             -Plan "image-search-plan" `
                             -RedisName "image-search-redis-123"
       
       ⚠️  IMPORTANT: 
           • Remplacer "image-search-api-123" par votre propre nom!
           • Le nom DOIT être unique sur Azure
           • Utiliser uniquement des chiffres/lettres/traits d'union
           • Longueur max 45 caractères

  ☐ 6. Créer un cluster Qdrant Cloud (pendant le déploiement)
  
       1. Aller sur: https://cloud.qdrant.io
       2. Créer un compte (email + mot de passe)
       3. Cliquer "Create Cluster"
       4. Nom: "image-search"
       5. Plan: FREE
       6. Region: us-east-1
       7. Attendre création (~2 min)
       8. Copier l'URL: https://xxxxx-qdrant.io
       9. Copier l'API Key

  ☐ 7. Configurer les variables Qdrant
  
       az webapp config appsettings set \
          --resource-group image-search-rg \
          --name image-search-api-123 \
          --settings \
             QDRANT_HOST="https://xxxxx-qdrant.io" \
             QDRANT_API_KEY="votre-clé-api"

  ☐ 8. Attendre le déploiement
       └─ Cela peut prendre 5-10 minutes


DÉPLOIEMENT MANUEL (si vous préférez étape par étape) - OPTIONNEL
───────────────────────────────────────────────────────────────────────────────

  ☐ 5. Créer groupe de ressources
       az group create --name image-search-rg --location eastus

  ☐ 6. Créer plan App Service B1
       az appservice plan create --name image-search-plan \
                                 --resource-group image-search-rg \
                                 --sku B1 --is-linux

  ☐ 7. Créer App Service
       az webapp create --resource-group image-search-rg \
                        --plan image-search-plan \
                        --name image-search-api-123 \
                        --runtime "PYTHON|3.11" \
                        --deployment-local-git

  ☐ 8. Créer Azure Cache for Redis
       az redis create --resource-group image-search-rg \
                       --name image-search-redis-123 \
                       --location eastus --sku basic --vm-size c0 \
                       --enable-non-ssl-port true

  ☐ 9. Récupérer détails Redis
       az redis show --resource-group image-search-rg \
                     --name image-search-redis-123
       
       az redis list-keys --resource-group image-search-rg \
                          --name image-search-redis-123

  ☐ 10. Configurer variables d'environnement
        az webapp config appsettings set \
           --resource-group image-search-rg \
           --name image-search-api-123 \
           --settings \
              QDRANT_HOST="https://xxxxx-qdrant.io" \
              QDRANT_API_KEY="votre-clé" \
              REDIS_HOST="your-redis-name.redis.cache.windows.net" \
              REDIS_PASSWORD="votre-password" \
              REDIS_PORT="6379" \
              CACHE_TTL="3600" \
              ENVIRONMENT="production" \
              WEBSITES_PORT="8000" \
              SCM_DO_BUILD_DURING_DEPLOYMENT="true"

  ☐ 11. Configurer startup
        az webapp config set --resource-group image-search-rg \
                             --name image-search-api-123 \
                             --startup-file "startup.sh"

  ☐ 12. Ajouter remote Git
        git remote add azure https://edoukou07@image-search-api-123.scm.azurewebsites.net/image-search-api-123.git

  ☐ 13. Déployer le code
        git push azure main


VÉRIFICATION POST-DÉPLOIEMENT
───────────────────────────────────────────────────────────────────────────────

  ☐ 14. Attendre le démarrage (3-5 minutes)
         └─ CLIP doit se télécharger (~500MB)

  ☐ 15. Consulter les logs
         az webapp log tail --name image-search-api-123 \
                            --resource-group image-search-rg
         
         Vérifier:
         ✅ "Application startup complete"
         ✅ "Uvicorn running on 0.0.0.0:8000"

  ☐ 16. Tester le Health Check
         https://image-search-api-123.azurewebsites.net/api/v1/health
         
         Réponse attendue:
         {
           "status": "healthy",
           "qdrant_connected": true,
           "redis_connected": true,
           "model_loaded": true
         }
         
         ⚠️  Si "model_loaded": false → Attendre 2-3 min de plus

  ☐ 17. Accéder à la documentation Swagger
         https://image-search-api-123.azurewebsites.net/docs

  ☐ 18. Tester indexation produit (POST /api/v1/index-product)
         {
           "id": "prod_test_001",
           "name": "Test Product",
           "description": "A test product",
           "image_url": "https://via.placeholder.com/400",
           "category": "test",
           "price": 29.99
         }

  ☐ 19. Tester recherche (POST /api/v1/search)
         {
           "text_query": "test product",
           "top_k": 5
         }

  ☐ 20. Vérifier health status
         GET /api/v1/health

  ☐ 21. Vérifier collections
         GET /api/v1/collections


POST-DÉPLOIEMENT - RECOMMANDÉ
───────────────────────────────────────────────────────────────────────────────

  ☐ 22. Configurer alertes de coûts
         Dans Azure Portal:
         • Aller à: Abonnements → Alertes
         • Créer une alerte si dépasse $50/mois

  ☐ 23. Configurer les alertes de performance
         Dans Azure Portal:
         • App Service → Alertes
         • Ajouter alerte si CPU > 80% (2+ min)
         • Ajouter alerte si taux d'erreur > 5%

  ☐ 24. Activer Application Insights (gratuit jusqu'à 5GB/mois)
         az webapp config appsettings set \
            --resource-group image-search-rg \
            --name image-search-api-123 \
            --settings APPINSIGHTS_INSTRUMENTATIONKEY="your-key"

  ☐ 25. Configurer les logs
         az webapp log config --resource-group image-search-rg \
                              --name image-search-api-123 \
                              --application-logging filesystem

  ☐ 26. Configurer backup automatique (optionnel)
         Dans Azure Portal:
         • App Service → Paramètres → Sauvegarde
         • Configurer sauvegarde quotidienne


INFORMATIONS IMPORTANTES
───────────────────────────────────────────────────────────────────────────────

URLs clés:
  • API Base: https://image-search-api-123.azurewebsites.net
  • Documentation: https://image-search-api-123.azurewebsites.net/docs
  • Health: https://image-search-api-123.azurewebsites.net/api/v1/health
  • Azure Portal: https://portal.azure.com

Coûts mensuels:
  • App Service B1: $13.20
  • Redis Basic (250MB): $15.30
  • Qdrant Cloud Free: $0.00
  • ─────────────────────────
  • TOTAL: ~$31/mois

Performance attendue:
  • Latence sans cache: 200-350ms
  • Latence avec cache: 30-100ms
  • Temps réponse health: <10ms
  • Premier démarrage: 1-2 min (CLIP)


COMMANDES DE GESTION COURANTES
───────────────────────────────────────────────────────────────────────────────

Redémarrer l'app:
  az webapp restart --name image-search-api-123 \
                    --resource-group image-search-rg

Voir les logs en temps réel:
  az webapp log tail --name image-search-api-123 \
                     --resource-group image-search-rg --follow

Mettre à jour une variable:
  az webapp config appsettings set \
     --resource-group image-search-rg \
     --name image-search-api-123 \
     --settings VARIABLE_NAME="new_value"

Voir toutes les variables:
  az webapp config appsettings list \
     --resource-group image-search-rg \
     --name image-search-api-123

Déployer à nouveau:
  cd c:\Users\edou\Desktop\IAAPP\image-search-api
  git push azure main

Supprimer tout (attention!):
  az group delete --name image-search-rg


TROUBLESHOOTING
───────────────────────────────────────────────────────────────────────────────

502 Bad Gateway?
  ✓ Attendre 3-5 minutes (CLIP se télécharge)
  ✓ Vérifier les logs: az webapp log tail ...
  ✓ Redémarrer: az webapp restart ...

qdrant_connected: false?
  ✓ Vérifier QDRANT_HOST et QDRANT_API_KEY
  ✓ Vérifier que le cluster Qdrant Cloud démarre
  ✓ Mettre à jour les variables d'environnement

redis_connected: false?
  ✓ Vérifier REDIS_HOST, REDIS_PASSWORD
  ✓ Vérifier que Redis a démarré: az redis show ...
  ✓ Dans Azure Portal vérifier le statut

model_loaded: false?
  ✓ Attendre 2-3 minutes (premier téléchargement CLIP)
  ✓ Vérifier les logs
  ✓ Redémarrer si besoin: az webapp restart ...

Trop lent?
  ✓ Plan B1 est lent (CPU partagé)
  ✓ Scaler vers B2 ou S1 Standard
  ✓ Attendre que le modèle soit chargé en cache


NOTES
───────────────────────────────────────────────────────────────────────────────

• Chaque ☐ représente une action à vérifier
• Effectuez-les dans l'ordre
• ⏱️  Le déploiement prend 30-45 minutes au total
• 🔄 Les redéploiements sont plus rapides (5-10 min)
• 💾 Les logs sont stockés 24h
• 🔐 Les variables d'environnement sont chiffrées


SUPPORT
───────────────────────────────────────────────────────────────────────────────

Besoin d'aide?
  • Docs Azure App Service: https://docs.microsoft.com/azure/app-service/
  • Docs Qdrant: https://qdrant.tech/documentation/
  • Docs FastAPI: https://fastapi.tiangolo.com/
  • Stack Overflow tag: azure-app-service

═══════════════════════════════════════════════════════════════════════════════
