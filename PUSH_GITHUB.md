# GUIDE - Pousser vers GitHub

## Option 1 : Avec Git CLI (Recommandé)

### Prérequis
- Git installé : https://git-scm.com/download/win
- Compte GitHub avec authentification configurée

### Étapes

```powershell
# 1. Naviguer au dossier du projet
cd c:\Users\edou\Desktop\IAAPP\image-search-api

# 2. Initialiser Git
git init

# 3. Configurer Git (une seule fois)
git config --global user.name "Votre Nom"
git config --global user.email "votre.email@gmail.com"

# 4. Ajouter tous les fichiers
git add .

# 5. Créer le premier commit
git commit -m "Initial commit: Complete Image Search API with CLIP + Qdrant + Redis"

# 6. Ajouter la remote GitHub
git remote add origin https://github.com/edoukou07/iafrimallv100.git

# 7. Renommer la branche en 'main'
git branch -M main

# 8. Pousser vers GitHub
git push -u origin main
```

### Authentification GitHub

Si vous n'êtes pas authentifié, vous aurez deux options :

**Option A : GitHub CLI (Recommandé)**
```powershell
# Installer GitHub CLI
winget install gh

# Authentifier
gh auth login

# Ensuite refaire: git push -u origin main
```

**Option B : Token Personnel**
```powershell
# Utiliser ce format pour le push:
git push -u origin main

# Quand demandé:
# Username: votre_username_github
# Password: votre_token_personnel (généré dans Settings > Developer settings > Personal access tokens)
```

---

## Option 2 : Script PowerShell Automatisé

```powershell
# Exécuter le script
.\push-to-github.ps1
```

Ce script fera automatiquement:
- Initialiser Git
- Configurer Git
- Ajouter les fichiers
- Créer le commit
- Ajouter la remote
- Pousser vers GitHub

---

## Option 3 : GitHub Desktop (Interface Graphique)

1. Télécharger : https://desktop.github.com/
2. Ouvrir GitHub Desktop
3. File → Clone Repository
4. Ou File → Add Local Repository
5. Sélectionner: c:\Users\edou\Desktop\IAAPP\image-search-api
6. Publish Repository

---

## Vérifier que c'est bon

```powershell
# Vérifier le statut Git
git status

# Voir les commits
git log --oneline

# Voir la remote
git remote -v
```

Vous devriez voir:
```
origin  https://github.com/edoukou07/iafrimallv100.git (fetch)
origin  https://github.com/edoukou07/iafrimallv100.git (push)
```

---

## Après le premier push

### Modifications futures

```powershell
# Après avoir modifié des fichiers
git add .
git commit -m "Description des changements"
git push
```

### Créer des branches

```powershell
# Créer une nouvelle branche
git checkout -b feature/nom-feature

# Faire des changements
git add .
git commit -m "Description"

# Pousser la branche
git push -u origin feature/nom-feature

# Fusionner dans main
git checkout main
git merge feature/nom-feature
git push
```

---

## Troubleshooting

### "Git is not recognized"
→ Installer Git: https://git-scm.com/download/win

### "Authentication failed"
→ Générer un token: https://github.com/settings/tokens
→ Utiliser: `git push https://{TOKEN}@github.com/edoukou07/iafrimallv100.git`

### "Repository not found"
→ Vérifier que le dépôt existe sur GitHub
→ Vérifier l'URL: https://github.com/edoukou07/iafrimallv100

### "Branch main exists remotely"
→ Forcer: `git push -u origin main --force`

### "Could not resolve host"
→ Vérifier la connexion Internet
→ Vérifier le proxy/firewall

---

## Fichiers du .gitignore (déjà configuré)

Le fichier `.gitignore` exclut déjà:
- `__pycache__/`
- `.venv/`, `venv/`
- `.env` (mais pas `.env.example`)
- `*.pyc`
- `uploads/`, `qdrant_storage/`, `redis_data/`
- `.pytest_cache/`
- Et autres fichiers temporaires

---

## Checkpoints

✅ **Avant de pousser**, vérifier:
- [ ] Git installé (`git --version`)
- [ ] Dossier du projet: `c:\Users\edou\Desktop\IAAPP\image-search-api`
- [ ] Dépôt GitHub créé: https://github.com/edoukou07/iafrimallv100
- [ ] Authentification GitHub configurée
- [ ] Fichiers locaux à jour

✅ **Après le push**, vérifier:
- [ ] Aller sur: https://github.com/edoukou07/iafrimallv100
- [ ] Voir les fichiers du projet
- [ ] Lire le README.md
- [ ] Voir l'historique des commits

---

## Support

Si vous rencontrez des problèmes:

1. **Vérifier Git est installé**
   ```powershell
   git --version
   ```

2. **Vérifier la configuration**
   ```powershell
   git config --list
   ```

3. **Voir le statut du dépôt**
   ```powershell
   git status
   git log --oneline
   ```

4. **Consulter la documentation officielle**
   - Git: https://git-scm.com/doc
   - GitHub: https://docs.github.com
   - GitHub CLI: https://cli.github.com/manual

---

## Commandes Rapides

```powershell
# Setup initial
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/edoukou07/iafrimallv100.git
git branch -M main
git push -u origin main

# Modifications ultérieures
git add .
git commit -m "Message"
git push

# Voir historique
git log --oneline -10

# Annuler le dernier commit (local)
git reset HEAD~1

# Annuler les modifications non stagées
git checkout -- .
```

---

Bonne chance! 🚀
