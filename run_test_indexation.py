#!/usr/bin/env python3
"""
Wrapper pour lancer le test de performance d'indexation.
Vérifie les prérequis et configure l'environnement.
"""

import subprocess
import sys
import os
from pathlib import Path
import time

def check_redis():
    """Vérifie si Redis est accessible."""
    try:
        result = subprocess.run(
            ["redis-cli", "ping"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0 and "PONG" in result.stdout
    except Exception:
        return False

def check_qdrant():
    """Vérifie si Qdrant est accessible."""
    try:
        import requests
        response = requests.get("http://localhost:6333/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def check_api():
    """Vérifie si l'API FastAPI est accessible."""
    try:
        import requests
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def main():
    """Point d'entrée principal."""
    
    print("\n" + "="*70)
    print("VÉRIFICATION DES PRÉREQUIS")
    print("="*70 + "\n")

    # Vérifications
    checks = {
        "Redis": check_redis,
        "Qdrant": check_qdrant,
        "API FastAPI": check_api
    }

    all_ok = True
    for name, check_fn in checks.items():
        print(f"Vérification {name}...", end=" ")
        if check_fn():
            print("✓ OK")
        else:
            print("✗ ERREUR")
            all_ok = False

    print()

    if not all_ok:
        print("⚠️  Certains services ne sont pas disponibles!")
        print("\nSolutions:")
        print("  1. Lancer Redis:")
        print("     docker run -d -p 6379:6379 redis:7")
        print()
        print("  2. Lancer Qdrant:")
        print("     docker run -d -p 6333:6333 qdrant/qdrant")
        print()
        print("  3. Lancer l'API:")
        print("     cd c:\\Users\\hynco\\Desktop\\iaafrimall\\iafrimallv100")
        print("     .\\venv\\Scripts\\Activate.ps1")
        print("     python -m uvicorn app.main:app --reload")
        print()
        print("  OU utiliser Docker Compose:")
        print("     docker-compose up -d")
        print()
        sys.exit(1)

    print("✓ Tous les services sont disponibles!\n")

    # Lancer le test
    print("="*70)
    print("LANCEMENT DU TEST DE PERFORMANCE")
    print("="*70 + "\n")

    script_path = Path(__file__).parent / "test_indexation_performance.py"
    
    try:
        subprocess.run(
            [sys.executable, str(script_path)],
            check=False
        )
    except KeyboardInterrupt:
        print("\n\n✗ Test interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erreur lors de l'exécution du test: {e}")
        sys.exit(1)

    print("\n" + "="*70)
    print("TEST TERMINÉ")
    print("="*70)
    print("\nProchaines étapes:")
    print("  1. Analyser les résultats ci-dessus")
    print("  2. Voir docs/TEST_INDEXATION_PERFORMANCE.md pour interpréter")
    print("  3. Voir docs/PARALLELISME_INDEXATION.md pour optimiser\n")


if __name__ == "__main__":
    main()
