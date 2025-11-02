@echo off
REM Script batch pour pousser le projet vers GitHub
REM Exécutez ce fichier en double-cliquant ou depuis cmd.exe

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║   Pushing Image Search API to GitHub                          ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Vérifier si Git est installé
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git n'est pas trouvé. Veuillez installer Git depuis: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo ✅ Git trouvé

REM Configuration
set GITHUB_URL=https://github.com/edoukou07/iafrimallv100.git
set BRANCH=main

echo.
echo 1️⃣  Initializing Git repository...
git init
echo ✅ Git repository initialized
echo.

echo 2️⃣  Adding all files...
git add .
echo ✅ Files added
echo.

echo 3️⃣  Creating initial commit...
git commit -m "Initial commit: Complete Image Search API with CLIP + Qdrant + Redis"
if errorlevel 1 (
    echo ⚠️  Commit skipped (repository might already have commits)
)
echo.

echo 4️⃣  Adding GitHub remote...
git remote remove origin >nul 2>&1
git remote add origin %GITHUB_URL%
echo ✅ Remote added: %GITHUB_URL%
echo.

echo 5️⃣  Setting up main branch...
git branch -M main
echo ✅ Branch renamed to main
echo.

echo 6️⃣  Pushing to GitHub...
git push -u origin main

if errorlevel 1 (
    echo.
    echo ❌ Error pushing to GitHub
    echo.
    echo Troubleshooting:
    echo   1. Check your GitHub credentials
    echo   2. Make sure the repository exists
    echo   3. Try manually: git push -u origin main
    pause
    exit /b 1
)

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║   ✅ SUCCESS! Project is now on GitHub                        ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo Repository: %GITHUB_URL%
echo Branch: %BRANCH%
echo.
echo Next steps:
echo   1. Go to: https://github.com/edoukou07/iafrimallv100
echo   2. Check your code
echo   3. Share the link!
echo.
pause
