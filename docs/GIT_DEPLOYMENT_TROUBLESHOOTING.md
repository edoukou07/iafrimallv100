# 🔧 Git Deployment Troubleshooting

## Problème

L'authentification git échoue pour pousser vers Azure Web App.

## Solutions disponibles

### Option 1: Utiliser Azure CLI pour déployer (Recommandé ⭐)

```powershell
# Créer une archive zip du code
Compress-Archive -Path app, requirements.txt, Dockerfile, .dockerignore -DestinationPath deployment.zip -Force

# Déployer via zip deployment
az webapp deployment source config-zip `
  --resource-group ia-image-search-rg `
  --name image-search-api-123 `
  --src-path deployment.zip
```

**Avantages:**
- ✅ Plus simple et rapide
- ✅ Pas de problèmes d'authentification git
- ✅ Directement supporté par Azure

### Option 2: Réinitialiser les credentials Azure

```powershell
# Obtenir vos credentials via le portail Azure
# https://portal.azure.com → image-search-api-123 → Deployment Center

# Ou via Azure CLI
az webapp deployment list-publishing-profiles `
  --resource-group ia-image-search-rg `
  --name image-search-api-123 `
  --query "[0]" -o json
```

### Option 3: Utiliser VS Code Azure Extension

1. Installer l'extension Azure App Service
2. S'authentifier avec votre compte Azure
3. Right-click sur le Web App → Deploy to Web App
4. Sélectionner le dossier `iafrimallv100`

### Option 4: Configuration Git manuelle

```powershell
# Supprimer le remote actuel
git remote remove azure

# Recréer avec la commande Azure CLI
$gitUrl = az webapp deployment source config-local-git `
  --resource-group ia-image-search-rg `
  --name image-search-api-123 `
  --query url -o tsv

# Ajouter le nouveau remote
git remote add azure $gitUrl

# Vous devrez entrer vos credentials interactivement
git push -u azure main
```

---

## Recommandation: Utiliser ZIP Deployment

C'est la solution la plus fiable:

```powershell
# 1. Créer le zip
cd C:\Users\hynco\Desktop\iaafrimall\iafrimallv100
Compress-Archive -Path app, requirements.txt, Dockerfile, .dockerignore `
  -DestinationPath deployment.zip -Force

# 2. Déployer
az webapp deployment source config-zip `
  --resource-group ia-image-search-rg `
  --name image-search-api-123 `
  --src-path deployment.zip

# 3. Vérifier le statut
az webapp deployment show `
  --resource-group ia-image-search-rg `
  --name image-search-api-123
```

---

## Credentials actuels

```
Username: iafrimal-deploy
Password: AzureDeploy2025Secure123
```

Vous pouvez les réinitialiser via Azure CLI si besoin:

```powershell
az webapp deployment user set --user-name "new-user" --password "NewPassword123"
```

---

## Vérifier le déploiement

Une fois le déploiement lancé (par n'importe quelle méthode):

```powershell
# Voir les logs
az webapp log tail -g ia-image-search-rg -n image-search-api-123

# Vérifier l'état
curl https://image-search-api-123.azurewebsites.net/health
```

---

**Prochaine action:** Utilisez l'Option 1 (ZIP Deployment) - c'est plus simple et plus fiable!
