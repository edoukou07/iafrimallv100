# 🚀 Guide de Déploiement - Azure VM Ubuntu Standard_B2s

## Résumé rapide

L'application Image Search API est déployée sur une **VM Ubuntu Standard_B2s** dans Azure. Tous les services (Redis, Qdrant, FastAPI) tournent sur la même machine.

**Coût estimé:** ~$40-45/mois (vs $95-120 pour 3 Container Apps)

---

## 📋 État du Déploiement

### 1. Infrastructure créée
- ✅ Resource Group: `image-search-vm-rg`
- ✅ VM: `image-search-vm` (Ubuntu LTS, Standard_B2s)
- ✅ IP Publique assignée

### 2. Fichiers prêts
- ✅ `docker-compose-vm.yml` - Compose avec Redis, Qdrant, API
- ✅ `setup-vm.sh` - Script d'installation Docker
- ✅ `image-search-api.service` - Service systemd pour auto-démarrage
- ✅ `Dockerfile` - Image API (existant)

---

## 🔧 Étapes Manuelles de Déploiement

### Étape 1: Récupérer l'IP publique

```powershell
# Depuis votre machine Windows
$publicIp = az vm list-ip-addresses `
  --resource-group "image-search-vm-rg" `
  --name "image-search-vm" `
  --output json | ConvertFrom-Json

$ip = $publicIp[0].virtualMachines[0].ipAddresses[0].publicIpAddress
Write-Host "IP: $ip"
```

**Résultat attendu:** Une adresse IP comme `20.245.X.X`

---

### Étape 2: Se connecter à la VM via SSH

```bash
# Depuis GitBash ou WSL
ssh -i ~/.ssh/id_rsa azureuser@<IP_PUBLIQUE>

# Exemple:
# ssh -i ~/.ssh/id_rsa azureuser@20.245.45.123
```

**Note:** Azure a généré la clé SSH lors de la création de la VM. Elle se trouve à `~/.ssh/id_rsa`

---

### Étape 3: Exécuter le script de setup initial

Sur la VM Ubuntu (après SSH):

```bash
# 1. Créer un répertoire temporaire
cd /tmp

# 2. Copier le script setup-vm.sh depuis votre machine
# (Effectué en parallèle depuis votre machine Windows)
```

**Depuis votre machine Windows (PowerShell):**

```powershell
$ip = "20.245.X.X"  # Remplacer par votre IP
scp -i ~/.ssh/id_rsa setup-vm.sh azureuser@$ip:/tmp/
```

**Sur la VM Ubuntu:**

```bash
sudo bash /tmp/setup-vm.sh
```

Cela va:
- Mettre à jour le système
- Installer Docker et Docker Compose
- Configurer les permissions

---

### Étape 4: Préparer le répertoire de travail

Sur la VM Ubuntu:

```bash
sudo mkdir -p /opt/image-search-api
sudo chown azureuser:azureuser /opt/image-search-api
cd /opt/image-search-api
```

---

### Étape 5: Copier les fichiers de l'application

**Depuis votre machine Windows (PowerShell):**

```powershell
$ip = "20.245.X.X"  # Remplacer par votre IP

scp -i ~/.ssh/id_rsa `
  docker-compose-vm.yml `
  Dockerfile `
  requirements.txt `
  azureuser@$ip:/opt/image-search-api/

scp -i ~/.ssh/id_rsa -r app azureuser@$ip:/opt/image-search-api/
scp -i ~/.ssh/id_rsa -r data azureuser@$ip:/opt/image-search-api/
```

---

### Étape 6: Démarrer les services

Sur la VM Ubuntu:

```bash
cd /opt/image-search-api

# Vérifier les fichiers
ls -la

# Démarrer Docker Compose
docker-compose -f docker-compose-vm.yml up -d

# Suivre les logs
docker-compose -f docker-compose-vm.yml logs -f
```

Attendez ~2-3 minutes que tous les services démarrent.

---

### Étape 7: Vérifier les services

Sur la VM Ubuntu:

```bash
# Voir les conteneurs
docker ps

# Sortie attendue:
# CONTAINER ID   IMAGE           STATUS          PORTS
# xxx            qdrant/qdrant   Up 2 minutes    0.0.0.0:6333->6333/tcp
# xxx            redis:7         Up 2 minutes    0.0.0.0:6379->6379/tcp
# xxx            image-search    Up 1 minute     0.0.0.0:8000->8000/tcp

# Vérifier la santé
docker-compose -f docker-compose-vm.yml ps
```

---

### Étape 8: Tester l'API

Depuis votre machine Windows:

```powershell
$ip = "20.245.X.X"

# Health check
curl "http://$ip:8000/api/v1/health"

# Exemple de réponse:
# {"status": "ok", "redis": "connected", "qdrant": "connected"}
```

---

## 🌐 Accès à l'application

### URLs publiques

```
API:            http://<IP>:8000
Swagger UI:     http://<IP>:8000/docs
ReDoc:          http://<IP>:8000/redoc
Health:         http://<IP>:8000/api/v1/health
```

Remplacer `<IP>` par l'IP publique de la VM.

---

## 🔐 Configuration Sécurité (NSG)

Les règles de firewall suivantes ont été créées automatiquement:

| Port | Service | Accès |
|------|---------|-------|
| 8000 | FastAPI API | Public |
| 6333 | Qdrant (optionnel) | Public (interne recommandé) |
| 6379 | Redis (optionnel) | Public (interne recommandé) |
| 22 | SSH | Public |

**Recommandations:**
- Fermer les ports 6333 et 6379 (services internes)
- Garder ouvert: 22 (SSH), 8000 (API)
- Ajouter certificat SSL pour HTTPS

---

## 📊 Coûts mensuels

| Service | Coût |
|---------|------|
| VM Standard_B2s (730 heures) | ~$30-40 |
| IP Publique statique | ~$2-3 |
| Stockage (OS + data, 64 GB) | ~$5-8 |
| **TOTAL** | **~$40-45/mois** |

Comparé à Container Apps: **-$50-70/mois d'économies**

---

## 🔄 Gestion des services

### Redémarrer tous les services

```bash
cd /opt/image-search-api
docker-compose -f docker-compose-vm.yml restart
```

### Arrêter les services

```bash
docker-compose -f docker-compose-vm.yml down
```

### Relancer les services

```bash
docker-compose -f docker-compose-vm.yml up -d
```

### Voir les logs en temps réel

```bash
docker-compose -f docker-search-api.yml logs -f api
```

---

## 🚀 Configuration Auto-démarrage (Optionnel)

Pour que les services démarrent automatiquement au reboot de la VM:

**Sur la VM Ubuntu:**

```bash
# 1. Copier le fichier service
sudo cp /tmp/image-search-api.service /etc/systemd/system/

# 2. Recharger systemd
sudo systemctl daemon-reload

# 3. Activer le service
sudo systemctl enable image-search-api

# 4. Démarrer le service
sudo systemctl start image-search-api

# 5. Vérifier le statut
sudo systemctl status image-search-api
```

---

## 🆘 Troubleshooting

### L'API ne répond pas

```bash
# Vérifier les conteneurs
docker ps

# Voir les logs
docker-compose -f docker-compose-vm.yml logs api

# Redémarrer
docker-compose -f docker-compose-vm.yml restart api
```

### Erreur de connexion Qdrant

```bash
# Vérifier que Qdrant est en bonne santé
docker-compose -f docker-compose-vm.yml logs qdrant

# Redémarrer Qdrant
docker-compose -f docker-compose-vm.yml restart qdrant
```

### Redis ne répond pas

```bash
# Tester la connexion
docker exec redis-local redis-cli -a "redis-secure-password" ping

# Résultat attendu: PONG
```

---

## 📝 Notes

- Les mot de passe définis dans `docker-compose-vm.yml` doivent être changés en production
- Les données sont persistées dans les volumes Docker
- Considérer configurer SSL/TLS pour la production
- Mettre en place une sauvegarde régulière des données

---

## 📞 Support

Pour les problèmes:

1. Vérifier les logs: `docker-compose logs -f`
2. Vérifier l'état des services: `docker ps`
3. Vérifier la connectivity: `curl http://localhost:8000/api/v1/health`

