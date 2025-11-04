#!/usr/bin/env python3
"""
Diagnostic basé sur les conteneurs vus dans 'docker ps'

Conteneurs actuels:
- redis:7-alpine (image-search-redis) - UP 4 minutes, HEALTHY
- iafrimallv100-api (image-search-api) - UP 4 minutes, HEALTHY
- iafrimallv100-worker1 (image-search-worker-1) - UP 4 minutes, UNHEALTHY
- iafrimallv100-worker2 (image-search-worker-2) - UP 4 minutes, UNHEALTHY
- qdrant/qdrant:latest (image-search-qdrant) - UP 4 minutes, HEALTHY
"""

import subprocess
import sys

def run_docker_cmd(container_pattern, description):
    """Récupère le container ID par pattern et exécute une commande."""
    print(f"\n{'='*70}")
    print(f"🔍 {description}")
    print(f"{'='*70}\n")
    
    try:
        # Récupérer le container ID
        result = subprocess.run(
            f'docker ps -q --filter "name={container_pattern}"',
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        container_id = result.stdout.strip().split('\n')[0] if result.stdout else None
        
        if not container_id:
            print(f"❌ Conteneur '{container_pattern}' non trouvé")
            return False
        
        print(f"Container ID: {container_id[:12]}")
        print(f"Nom pattern: {container_pattern}\n")
        
        # Récupérer les logs
        result = subprocess.run(
            f'docker logs {container_id} 2>&1',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Afficher les 30 dernières lignes
        lines = result.stdout.split('\n')
        for line in lines[-30:]:
            if line.strip():
                print(line)
        
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("🔍 DIAGNOSTIC: État des Conteneurs Docker")
    print("="*70)
    
    # 1. Redis
    redis_ok = run_docker_cmd("redis", "1. REDIS (image-search-redis)")
    redis_status = "✅ OK" if redis_ok else "❌ ERREUR"
    print(f"\n{redis_status}")
    
    # 2. API
    api_ok = run_docker_cmd("api", "2. API (image-search-api)")
    api_status = "✅ OK" if api_ok else "❌ ERREUR"
    print(f"\n{api_status}")
    
    # 3. Worker 1
    worker1_ok = run_docker_cmd("worker-1", "3. WORKER 1 (image-search-worker-1)")
    worker1_status = "✅ OK" if worker1_ok else "❌ ERREUR"
    print(f"\n{worker1_status}")
    
    # 4. Worker 2
    worker2_ok = run_docker_cmd("worker-2", "4. WORKER 2 (image-search-worker-2)")
    worker2_status = "✅ OK" if worker2_ok else "❌ ERREUR"
    print(f"\n{worker2_status}")
    
    # 5. Qdrant
    qdrant_ok = run_docker_cmd("qdrant", "5. QDRANT (image-search-qdrant)")
    qdrant_status = "✅ OK" if qdrant_ok else "❌ ERREUR"
    print(f"\n{qdrant_status}")
    
    # Résumé
    print("\n" + "="*70)
    print("📋 RÉSUMÉ")
    print("="*70)
    print(f"""
Redis:   {redis_status}
API:     {api_status}
Worker1: {worker1_status}
Worker2: {worker2_status}
Qdrant:  {qdrant_status}

PROBLÈME DÉTECTÉ:
- Workers sont "unhealthy" malgré que le conteneur soit "UP"
- Cela signifie que l'healthcheck échoue mais le conteneur continue à tourner

CAUSES POSSIBLES (à vérifier dans les logs ci-dessus):
1. Redis non accessible par les workers
2. Erreur d'import Python dans le worker
3. Exception non gérée au démarrage du worker
4. Configuration REDIS_URL incorrecte dans les workers

PROCHAINES ÉTAPES:
1. Vérifier les erreurs dans les logs du worker (chercher "Error", "Traceback")
2. Si erreur d'import: Vérifier que les dépendances sont installées
3. Si erreur Redis: Vérifier la variable REDIS_URL
4. Redémarrer si nécessaire: docker compose restart worker1 worker2
5. Relancer le test: python test_async_real.py
""")

if __name__ == "__main__":
    main()
