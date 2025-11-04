#!/usr/bin/env python3
"""
Diagnostic complet: Vérifier l'état de Redis et créer un script de fix.
"""

import subprocess
import json

def run_cmd(cmd, description):
    """Exécute une commande et retourne le résultat."""
    print(f"\n{'='*70}")
    print(f"🔍 {description}")
    print(f"{'='*70}")
    print(f"Commande: {cmd}\n")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        return True, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT")
        return False, "TIMEOUT"
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False, str(e)

def main():
    print("\n" + "="*70)
    print("🔍 DIAGNOSTIC: État de l'Indexation Asynchrone")
    print("="*70)
    
    # 1. Vérifier les conteneurs Docker
    run_cmd("docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'",
            "1. État des conteneurs Docker")
    
    # 2. Vérifier Redis
    run_cmd("docker ps | grep redis",
            "2. Chercher conteneur Redis")
    
    # 3. Vérifier la connectivité Redis
    run_cmd("redis-cli -h 127.0.0.1 ping 2>&1",
            "3. Test connexion Redis (127.0.0.1:6379)")
    
    # 4. Vérifier si Redis est dans docker-compose
    run_cmd("cat docker-compose.yml | grep -A 10 redis",
            "4. Configuration Redis dans docker-compose.yml")
    
    # 5. Chercher les workers
    run_cmd("docker ps | grep worker",
            "5. Chercher les conteneurs workers")
    
    # 6. Vérifier les logs API
    success, logs = run_cmd("docker logs $(docker ps --filter name=api -q) 2>&1 | tail -20",
            "6. Logs API (dernières 20 lignes)")
    
    print("\n" + "="*70)
    print("📋 RÉSUMÉ ET RECOMMANDATIONS")
    print("="*70)
    
    print("""
PROBLÈME IDENTIFIÉ:
- Les workers sont marqués "unhealthy" dans Docker
- L'API utilise le fallback synchrone au lieu de Redis

CAUSES POSSIBLES:
1. Redis n'est pas accessible par les workers
2. Les workers n'arrivent pas à se connecter à Redis
3. La configuration REDIS_URL est incorrecte

SOLUTIONS À ESSAYER:
""")
    
    print("\n✓ Solution 1: Vérifier la connexion Redis dans Docker")
    print("   docker exec $(docker ps --filter name=redis -q) redis-cli ping")
    
    print("\n✓ Solution 2: Voir les logs du worker")
    print("   docker logs $(docker ps --filter name=worker -q | head -1)")
    
    print("\n✓ Solution 3: Vérifier l'URL Redis utilisée par les workers")
    print("   docker inspect $(docker ps --filter name=worker -q | head -1) | grep REDIS")
    
    print("\n✓ Solution 4: Redémarrer les services")
    print("   docker compose down")
    print("   docker compose up -d")
    print("   sleep 5")
    print("   python test_async_real.py")

if __name__ == "__main__":
    main()
