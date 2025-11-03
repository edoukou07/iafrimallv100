#!/usr/bin/env python3
"""
Test de diagnostic pour l'indexation sur un serveur déployé.
Teste directement contre l'API Azure.
"""

import asyncio
import time
import aiohttp
from typing import Dict, List
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://52.143.186.136:8000/api/v1"
TIMEOUT = aiohttp.ClientTimeout(total=300)  # 5 minutes de timeout


class RemoteIndexationTest:
    """Test de performance contre l'API déployée."""

    def __init__(self):
        self.results = {
            "tests": [],
            "errors": [],
            "total_time": 0
        }

    async def test_api_health(self) -> bool:
        """Vérifie si l'API est accessible."""
        try:
            async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
                async with session.get(f"{API_BASE_URL}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✓ API accessible: {data}")
                        return True
                    else:
                        print(f"✗ API retourne {response.status}")
                        return False
        except Exception as e:
            print(f"✗ Erreur de connexion: {e}")
            return False

    async def test_single_product_sync(self) -> Dict:
        """Test l'indexation synchrone d'un produit."""
        
        test_result = {
            "type": "sync_indexation",
            "product_name": "Test Product Sync",
            "start_time": datetime.now().isoformat(),
            "duration": 0,
            "success": False,
            "error": None,
            "response_status": None
        }

        try:
            product_data = {
                "product_id": "test-sync-001",
                "name": "Test Product Sync",
                "description": "Ceci est un produit de test pour vérifier la vitesse d'indexation synchrone.",
                "metadata": "test-sync"
            }

            print(f"\n▶ Test indexation SYNCHRONE")
            print(f"  Produit: {product_data['name']}")

            start_time = time.time()
            
            async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
                data = aiohttp.FormData()
                data.add_field("product_id", product_data["product_id"])
                data.add_field("name", product_data["name"])
                data.add_field("description", product_data["description"])
                data.add_field("metadata", product_data["metadata"])

                async with session.post(
                    f"{API_BASE_URL}/index-product",
                    data=data
                ) as response:
                    duration = time.time() - start_time
                    test_result["duration"] = duration
                    test_result["response_status"] = response.status

                    if response.status == 200:
                        result = await response.json()
                        test_result["success"] = True
                        print(f"  ✓ Succès en {duration:.2f}s")
                        print(f"  Response: {result}")
                    else:
                        error_text = await response.text()
                        test_result["error"] = f"Status {response.status}: {error_text}"
                        print(f"  ✗ Erreur {response.status}")
                        print(f"  Response: {error_text}")

        except asyncio.TimeoutError:
            test_result["error"] = "Timeout après 5 minutes"
            test_result["duration"] = 300
            print(f"  ✗ TIMEOUT > 5 minutes (goulot sérieux!)")
        except Exception as e:
            test_result["error"] = str(e)
            print(f"  ✗ Erreur: {e}")

        self.results["tests"].append(test_result)
        return test_result

    async def test_search_performance(self) -> Dict:
        """Test la performance de recherche."""
        
        test_result = {
            "type": "search",
            "query": "produit test",
            "start_time": datetime.now().isoformat(),
            "duration": 0,
            "success": False,
            "error": None,
            "response_status": None,
            "result_count": 0
        }

        try:
            print(f"\n▶ Test RECHERCHE")
            print(f"  Query: {test_result['query']}")

            start_time = time.time()
            
            async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
                params = {"q": test_result["query"], "limit": 10}
                
                async with session.get(
                    f"{API_BASE_URL}/search",
                    params=params
                ) as response:
                    duration = time.time() - start_time
                    test_result["duration"] = duration
                    test_result["response_status"] = response.status

                    if response.status == 200:
                        result = await response.json()
                        test_result["success"] = True
                        test_result["result_count"] = len(result.get("results", []))
                        print(f"  ✓ Recherche en {duration:.2f}s")
                        print(f"  Résultats trouvés: {test_result['result_count']}")
                    else:
                        error_text = await response.text()
                        test_result["error"] = f"Status {response.status}: {error_text}"
                        print(f"  ✗ Erreur {response.status}")

        except asyncio.TimeoutError:
            test_result["error"] = "Timeout"
            test_result["duration"] = 300
            print(f"  ✗ TIMEOUT")
        except Exception as e:
            test_result["error"] = str(e)
            print(f"  ✗ Erreur: {e}")

        self.results["tests"].append(test_result)
        return test_result

    async def test_endpoint_async(self) -> Dict:
        """Test l'endpoint d'indexation asynchrone."""
        
        test_result = {
            "type": "async_indexation",
            "product_name": "Test Product Async",
            "start_time": datetime.now().isoformat(),
            "enqueue_duration": 0,
            "status_check_duration": 0,
            "total_duration": 0,
            "success": False,
            "error": None,
            "job_id": None,
            "job_status": None
        }

        try:
            print(f"\n▶ Test indexation ASYNCHRONE")

            # Créer une vraie image JPEG minimale (1x1 pixel)
            from io import BytesIO
            
            # JPEG minimale valide (1x1 pixel rouge)
            jpeg_data = (
                b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01'
                b'\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07'
                b'\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14'
                b'\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444'
                b'\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x11'
                b'\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07'
                b'\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04'
                b'\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05'
                b'\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R'
                b'\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CD'
                b'EFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89'
                b'\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6'
                b'\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3'
                b'\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9'
                b'\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4'
                b'\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00'
                b'\xfe\xfe\xff\xd9'
            )
            test_image = BytesIO(jpeg_data)
            test_image.seek(0)

            start_time = time.time()

            async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
                data = aiohttp.FormData()
                data.add_field("product_id", "test-async-001")
                data.add_field("name", "Test Product Async")
                data.add_field("description", "Test product pour endpoint async")
                data.add_field("image_file", test_image, filename="test.jpg", content_type="image/jpeg")

                async with session.post(
                    f"{API_BASE_URL}/index-product-with-image",
                    data=data
                ) as response:
                    enqueue_time = time.time() - start_time
                    test_result["enqueue_duration"] = enqueue_time
                    test_result["response_status"] = response.status

                    if response.status == 202 or response.status == 200:
                        result = await response.json()
                        test_result["job_id"] = result.get("job_id", "unknown")
                        print(f"  ✓ Job enqueued en {enqueue_time:.2f}s")
                        print(f"  Job ID: {test_result['job_id']}")

                        # Vérifier le statut du job
                        await asyncio.sleep(1)  # Attendre un peu

                        status_start = time.time()
                        async with session.get(
                            f"{API_BASE_URL}/job/{test_result['job_id']}/status"
                        ) as status_response:
                            status_time = time.time() - status_start
                            test_result["status_check_duration"] = status_time

                            if status_response.status == 200:
                                status_data = await status_response.json()
                                test_result["job_status"] = status_data.get("status")
                                print(f"  ✓ Status check en {status_time:.2f}s")
                                print(f"  Job Status: {test_result['job_status']}")
                                test_result["success"] = True
                            else:
                                print(f"  ⚠ Statut check échoué: {status_response.status}")
                    else:
                        error_text = await response.text()
                        test_result["error"] = f"Status {response.status}: {error_text}"
                        print(f"  ✗ Erreur {response.status}")

            test_result["total_duration"] = time.time() - start_time

        except asyncio.TimeoutError:
            test_result["error"] = "Timeout"
            print(f"  ✗ TIMEOUT")
        except Exception as e:
            test_result["error"] = str(e)
            print(f"  ✗ Erreur: {e}")

        self.results["tests"].append(test_result)
        return test_result

    async def run_full_test(self):
        """Exécute tous les tests."""
        
        print("\n" + "="*70)
        print("TEST DE DIAGNOSTIC - SERVEUR DÉPLOYÉ")
        print("="*70)
        print(f"API URL: {API_BASE_URL}")
        print(f"Date: {datetime.now().isoformat()}\n")

        # Test 1: Vérifier santé API
        print("ÉTAPE 1: Vérification de l'API")
        print("-" * 70)
        health_ok = await self.test_api_health()

        if not health_ok:
            print("\n❌ L'API ne répond pas. Vérifier:")
            print("  - Le serveur est bien accessible: ping 52.143.186.136")
            print("  - Le port 8000 est ouvert")
            print("  - L'API est bien déployée")
            return

        # Test 2: Indexation synchrone
        print("\n\nÉTAPE 2: Indexation SYNCHRONE")
        print("-" * 70)
        await self.test_single_product_sync()

        # Test 3: Recherche
        print("\n\nÉTAPE 3: Recherche")
        print("-" * 70)
        await self.test_search_performance()

        # Test 4: Indexation asynchrone
        print("\n\nÉTAPE 4: Indexation ASYNCHRONE")
        print("-" * 70)
        await self.test_endpoint_async()

        # Résumé
        self._print_summary()

    def _print_summary(self):
        """Affiche un résumé des tests."""
        
        print("\n\n" + "="*70)
        print("RÉSUMÉ DES TESTS")
        print("="*70 + "\n")

        for test in self.results["tests"]:
            test_type = test["type"]
            success = "✓" if test["success"] else "✗"
            
            if test_type == "sync_indexation":
                print(f"{success} Indexation Synchrone: {test['duration']:.2f}s")
                if test["error"]:
                    print(f"  Erreur: {test['error']}")
            
            elif test_type == "search":
                print(f"{success} Recherche: {test['duration']:.2f}s ({test['result_count']} résultats)")
                if test["error"]:
                    print(f"  Erreur: {test['error']}")
            
            elif test_type == "async_indexation":
                print(f"{success} Indexation Asynchrone (enqueue): {test['enqueue_duration']:.2f}s")
                if test["job_status"]:
                    print(f"  Job Status: {test['job_status']}")
                if test["error"]:
                    print(f"  Erreur: {test['error']}")

        # Analyse des goulots
        print("\n" + "="*70)
        print("ANALYSE DES GOULOTS")
        print("="*70 + "\n")

        sync_test = next((t for t in self.results["tests"] if t["type"] == "sync_indexation"), None)
        search_test = next((t for t in self.results["tests"] if t["type"] == "search"), None)

        if sync_test and sync_test["duration"] > 5:
            print("⚠️  Indexation synchrone TRÈS LENTE (> 5s)")
            print("  Causes possibles:")
            print("  - Embedding CLIP en CPU (pas de GPU)")
            print("  - Réseau lent vers Qdrant")
            print("  - Serveur surchargé")
            print("\n  Solutions:")
            print("  - Ajouter GPU à la VM Azure")
            print("  - Utiliser endpoint async avec workers")
            print("  - Augmenter RUs Qdrant")

        if search_test and search_test["duration"] > 2:
            print("⚠️  Recherche LENTE (> 2s)")
            print("  Causes possibles:")
            print("  - Qdrant distant")
            print("  - Réseau lent")
            print("\n  Solutions:")
            print("  - Colocaliser Qdrant sur même VM")
            print("  - Vérifier latence réseau (ping)")

        # Recommandations
        print("\n" + "="*70)
        print("RECOMMANDATIONS")
        print("="*70 + "\n")

        print("✅ Pour production:")
        print("  1. Lancer 3-5 workers pour paralléliser l'indexation")
        print("  2. Utiliser endpoint async (/index-product-with-image)")
        print("  3. Monitorer avec Application Insights")
        print("  4. Augmenter resources si goulot GPU/CPU")
        print("\n📊 Voir:")
        print("  - docs/PARALLELISME_INDEXATION.md")
        print("  - docs/TEST_INDEXATION_PERFORMANCE.md")


async def main():
    """Point d'entrée."""
    try:
        tester = RemoteIndexationTest()
        await tester.run_full_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
