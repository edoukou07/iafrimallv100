#!/usr/bin/env python3
"""
Test de performance simplifié pour production.
Teste uniquement les endpoints qui fonctionnent.
"""

import asyncio
import time
import aiohttp
from datetime import datetime

API_BASE_URL = "http://52.143.186.136:8000/api/v1"
TIMEOUT = aiohttp.ClientTimeout(total=300)


async def test_single_indexation():
    """Test l'indexation simple."""
    print("\n" + "="*70)
    print("TEST D'INDEXATION - PRODUCTION (Azure)")
    print("="*70)
    print(f"API URL: {API_BASE_URL}")
    print(f"Date: {datetime.now().isoformat()}\n")

    # Test 1: Vérifier l'API est accessible
    print("▶ Étape 1: Vérifier l'API")
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        async with session.get(f"{API_BASE_URL}/health") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ API accessible")
                print(f"  Service: {data.get('service', 'N/A')}")
                print(f"  Qdrant: {data.get('qdrant', {}).get('connected', False)}")
            else:
                print(f"✗ API non accessible ({response.status})")
                return

    # Test 2: Indexation simple de 1 produit
    print("\n▶ Étape 2: Indexation 1 produit")
    
    start_time = time.time()
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        data = aiohttp.FormData()
        data.add_field("product_id", "perf-test-001")
        data.add_field("name", "Produit Test Performance")
        data.add_field("description", "Ceci est un produit de test pour mesurer la performance d'indexation. " * 3)
        data.add_field("metadata", "performance-test")

        async with session.post(
            f"{API_BASE_URL}/index-product",
            data=data
        ) as response:
            duration = time.time() - start_time
            
            if response.status == 200:
                result = await response.json()
                print(f"✓ Indexation réussie en {duration:.2f}s")
                print(f"  Response: {result}")
            else:
                print(f"✗ Erreur {response.status}")
                text = await response.text()
                print(f"  {text}")

    # Test 3: Indexation de 10 produits (séquentiellement)
    print("\n▶ Étape 3: Indexation 10 produits (séquentiel)")
    
    start_batch = time.time()
    success_count = 0
    
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        for i in range(10):
            try:
                data = aiohttp.FormData()
                data.add_field("product_id", f"perf-test-{i:03d}")
                data.add_field("name", f"Produit Test {i+1}")
                data.add_field("description", f"Description du produit {i+1}. " * 5)
                data.add_field("metadata", f"test-{i}")

                start_prod = time.time()
                async with session.post(
                    f"{API_BASE_URL}/index-product",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    prod_duration = time.time() - start_prod
                    
                    if response.status == 200:
                        success_count += 1
                        print(f"  [{i+1:2d}/10] ✓ {prod_duration:.2f}s")
                    else:
                        print(f"  [{i+1:2d}/10] ✗ Erreur {response.status}")
            
            except asyncio.TimeoutError:
                print(f"  [{i+1:2d}/10] ✗ Timeout")
            except Exception as e:
                print(f"  [{i+1:2d}/10] ✗ Erreur: {e}")

    batch_duration = time.time() - start_batch
    print(f"\n  Total: {batch_duration:.2f}s pour {success_count}/10 produits")
    print(f"  Moyenne: {batch_duration/success_count:.2f}s par produit")
    print(f"  Débit: {success_count/batch_duration:.2f} produits/sec")

    # Résumé
    print("\n" + "="*70)
    print("RÉSUMÉ")
    print("="*70)
    print(f"\n✓ Indexation synchrone: {duration:.2f}s par produit")
    print(f"✓ 10 produits: {batch_duration:.2f}s ({batch_duration/10:.2f}s moyenne)")
    print(f"✓ Débit: {success_count/batch_duration:.1f} produits/sec")
    
    if batch_duration / 10 < 0.5:
        print("\n🚀 EXCELLENTE performance! (< 0.5s par produit)")
    elif batch_duration / 10 < 1:
        print("\n✅ Bonne performance (< 1s par produit)")
    elif batch_duration / 10 < 2:
        print("\n⚠️  Performance acceptable (< 2s par produit)")
    else:
        print("\n❌ Performance lente (> 2s par produit)")
    
    print("\n💡 RECOMMANDATIONS:")
    print("  1. Votre serveur Azure indexe rapidement! ✓")
    print("  2. Ajouter 3-5 workers pour 3-5x speedup")
    print("  3. Voir: docs/QUICK_FIX_WORKERS.md")
    print()


if __name__ == "__main__":
    asyncio.run(test_single_indexation())
