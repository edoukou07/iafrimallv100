#!/bin/bash
# Script pour pousser le projet vers GitHub
# Exécutez ce script depuis le répertoire du projet

# Configuration
GITHUB_URL="https://github.com/edoukou07/iafrimallv100.git"
BRANCH="main"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Pushing Image Search API to GitHub                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 1. Initialiser le dépôt Git
echo "1️⃣  Initializing Git repository..."
git init
echo "   ✅ Git repository initialized"
echo ""

# 2. Configurer Git (si nécessaire)
echo "2️⃣  Configuring Git..."
git config user.name "Your Name" 2>/dev/null || git config --global user.name "Your Name"
git config user.email "your.email@example.com" 2>/dev/null || git config --global user.email "your.email@example.com"
echo "   ✅ Git configured"
echo ""

# 3. Ajouter tous les fichiers
echo "3️⃣  Adding all files..."
git add .
echo "   ✅ Files added"
echo ""

# 4. Créer le premier commit
echo "4️⃣  Creating initial commit..."
git commit -m "Initial commit: Complete Image Search API with CLIP + Qdrant + Redis

- FastAPI application with 4 endpoints
- CLIP embeddings for image and text
- Qdrant vector database integration
- Redis caching for performance
- Docker Compose setup
- Comprehensive documentation
- Python client and e-commerce examples
- Tests and configuration"
echo "   ✅ Initial commit created"
echo ""

# 5. Ajouter la remote
echo "5️⃣  Adding GitHub remote..."
git remote add origin "$GITHUB_URL"
echo "   ✅ Remote added: $GITHUB_URL"
echo ""

# 6. Créer la branche main et pousser
echo "6️⃣  Pushing to GitHub..."
git branch -M main
git push -u origin main
echo "   ✅ Project pushed to GitHub!"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   ✅ SUCCESS! Project is now on GitHub                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Repository: $GITHUB_URL"
echo "Branch: $BRANCH"
echo ""
echo "Next steps:"
echo "  1. Go to: https://github.com/edoukou07/iafrimallv100"
echo "  2. Check your code"
echo "  3. Share the link!"
echo ""
