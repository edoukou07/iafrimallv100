# Script PowerShell pour pousser le projet vers GitHub
# Exécutez ce script depuis le répertoire du projet

$GitHubURL = "https://github.com/edoukou07/iafrimallv100.git"
$Branch = "main"

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Pushing Image Search API to GitHub                          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 1. Initialiser le dépôt Git
Write-Host "1️⃣  Initializing Git repository..." -ForegroundColor Yellow
& git init
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "   ❌ Error initializing Git" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Configurer Git
Write-Host "2️⃣  Configuring Git..." -ForegroundColor Yellow
& git config user.name "Your Name" 2>$null
& git config user.email "your.email@example.com" 2>$null
Write-Host "   ✅ Git configured" -ForegroundColor Green
Write-Host ""

# 3. Ajouter tous les fichiers
Write-Host "3️⃣  Adding all files..." -ForegroundColor Yellow
& git add .
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Files added" -ForegroundColor Green
} else {
    Write-Host "   ❌ Error adding files" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 4. Créer le premier commit
Write-Host "4️⃣  Creating initial commit..." -ForegroundColor Yellow
$CommitMessage = @"
Initial commit: Complete Image Search API with CLIP + Qdrant + Redis

- FastAPI application with 4 endpoints
- CLIP embeddings for image and text
- Qdrant vector database integration
- Redis caching for performance
- Docker Compose setup
- Comprehensive documentation
- Python client and e-commerce examples
- Tests and configuration
"@

& git commit -m $CommitMessage
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Initial commit created" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Commit skipped (repository might already have commits)" -ForegroundColor Yellow
}
Write-Host ""

# 5. Ajouter la remote
Write-Host "5️⃣  Adding GitHub remote..." -ForegroundColor Yellow
& git remote add origin $GitHubURL 2>$null
if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq 128) {
    Write-Host "   ✅ Remote added: $GitHubURL" -ForegroundColor Green
}
Write-Host ""

# 6. Créer la branche main et pousser
Write-Host "6️⃣  Pushing to GitHub..." -ForegroundColor Yellow
& git branch -M main
& git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Project pushed to GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║   ✅ SUCCESS! Project is now on GitHub                        ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "Repository: $GitHubURL" -ForegroundColor Cyan
    Write-Host "Branch: $Branch" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Go to: https://github.com/edoukou07/iafrimallv100" -ForegroundColor White
    Write-Host "  2. Check your code" -ForegroundColor White
    Write-Host "  3. Share the link!" -ForegroundColor White
} else {
    Write-Host "   ❌ Error pushing to GitHub" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Make sure Git is installed" -ForegroundColor White
    Write-Host "  2. Check your GitHub credentials" -ForegroundColor White
    Write-Host "  3. Ensure the repository exists on GitHub" -ForegroundColor White
    Write-Host "  4. Try: git push -u origin main" -ForegroundColor White
    exit 1
}
