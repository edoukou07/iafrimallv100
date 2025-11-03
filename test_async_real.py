#!/usr/bin/env python3
"""
Test de l'indexation asynchrone avec une vraie image PIL.
"""

import asyncio
import aiohttp
from io import BytesIO
from datetime import datetime
import time

try:
    from PIL import Image
except ImportError:
    print("⚠️  PIL non trouvé, installation...")
    import subprocess
    subprocess.run(["pip", "install", "pillow", "-q"], check=True)
    from PIL import Image

API_URL = "http://52.143.186.136:8000/api/v1"
TIMEOUT = aiohttp.ClientTimeout(total=300)


def create_test_image() -> bytes:
    """Crée une vraie image JPEG pour le test."""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return buffer.getvalue()


async def test_async_indexation():
    """Test l'endpoint async avec le worker implémenté."""
    
    print("\n" + "="*70)
    print("TEST: Indexation Asynchrone Complète (Vraie Image)")
    print("="*70)
    print(f"Date: {datetime.now().isoformat()}\n")

    # Créer une vraie image JPEG
    print("Création d'une image JPEG de test...")
    jpeg_data = create_test_image()
    print(f"✓ Image créée: {len(jpeg_data)} bytes\n")

    print("▶ Étape 1: Enqueuer un produit avec image")
    print("-" * 70)

    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        data = aiohttp.FormData()
        data.add_field("product_id", "async-test-001")
        data.add_field("name", "Produit Test Async")
        data.add_field("description", "Ceci est un produit de test pour vérifier l'indexation asynchrone complète.")
        data.add_field("image_file", BytesIO(jpeg_data), filename="test.jpg", content_type="image/jpeg")

        print("Envoi du produit avec image...")
        start_enqueue = time.time()

        try:
            async with session.post(
                f"{API_URL}/index-product-with-image",
                data=data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                enqueue_time = time.time() - start_enqueue

                print(f"Réponse: {response.status} (en {enqueue_time:.2f}s)\n")

                if response.status in [200, 202]:
                    result = await response.json()
                    job_id = result.get("job_id")
                    status = result.get("status")
                    mode = result.get("processing_mode", "unknown")

                    print(f"✓ Enqueued en {enqueue_time:.2f}s")
                    print(f"  Job ID: {job_id}")
                    print(f"  Status: {status}")
                    print(f"  Mode: {mode}\n")

                    if status == "queued":
                        print("✅ Job a été mis en queue Redis!")
                        print("   Le worker devrait le traiter maintenant...\n")

                        # Attendre un peu et vérifier le statut
                        print("▶ Étape 2: Vérifier le statut du job")
                        print("-" * 70)

                        max_wait = 30
                        for i in range(max_wait):
                            await asyncio.sleep(1)
                            print(f"Vérification {i+1}/{max_wait}...", end=" ", flush=True)

                            try:
                                async with session.get(
                                    f"{API_URL}/queue/status/{job_id}",
                                    timeout=aiohttp.ClientTimeout(total=10)
                                ) as status_response:
                                    if status_response.status == 200:
                                        status_data = await status_response.json()
                                        job_status = status_data.get("status")
                                        print(f"[{job_status}]")

                                        if job_status == "completed":
                                            print("\n✅ Job complété avec succès!")
                                            print(f"   Le produit est indexé dans Qdrant")
                                            break
                                        elif job_status == "failed":
                                            error = status_data.get("error", "Unknown error")
                                            print(f"\n❌ Job échoué: {error}")
                                            break
                                    else:
                                        print(f"❌ Status check failed: {status_response.status}")
                                        break
                            except Exception as e:
                                print(f"❌ Error: {e}")
                                break
                        else:
                            print(f"\n⚠️  Timeout après {max_wait}s (worker peut ne pas tourner)")

                    elif status == "indexed":
                        print("✅ Fallback synchrone utilisé (indexation immédiate)")
                        print("   Cela indique que Redis n'est pas disponible")
                        print("   ou que le worker ne tourne pas")

                    print("\n▶ Étape 3: Vérifier le produit dans Qdrant")
                    print("-" * 70)

                    try:
                        async with session.get(
                            f"{API_URL}/search?q=Test+Async&limit=5",
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as search_response:
                            if search_response.status == 200:
                                search_results = await search_response.json()
                                results = search_results.get("results", [])
                                print(f"Résultats de recherche: {len(results)} produits\n")

                                for r in results:
                                    if r.get("product_id") == "async-test-001":
                                        print(f"✅ Produit trouvé dans Qdrant!")
                                        print(f"   ID: {r.get('product_id')}")
                                        print(f"   Nom: {r.get('name')}")
                                        print(f"   Score: {r.get('score'):.4f}")
                                        break
                                else:
                                    print(f"⚠️  Produit pas trouvé dans les résultats")
                    except Exception as e:
                        print(f"⚠️  Erreur de recherche: {e}")

                else:
                    print(f"✗ Erreur {response.status}")
                    text = await response.text()
                    print(f"  {text}")

        except asyncio.TimeoutError:
            print(f"✗ TIMEOUT après {enqueue_time:.2f}s")
        except Exception as e:
            print(f"✗ Erreur: {e}")

    print("\n" + "="*70)
    print("RÉSUMÉ & RÉSULTATS")
    print("="*70)
    print("""
✅ Scénarios possibles:

1. Status "queued" → "completed":
   ✓ Async fonctionne complètement
   ✓ Worker traite les images
   ✓ Produit indexé dans Qdrant

2. Status "queued" → toujours "queued":
   ⚠️  Async enqueue fonctionne
   ❌ Worker n'est pas lancé
   Action: Lancer `python -m app.workers.image_indexer_worker --worker-id w1`

3. Status "indexed":
   ✓ Fallback synchrone fonctionne
   ⚠️  Redis peut être indisponible
   Action: Vérifier `docker logs` ou Redis

Prochaines étapes:
- Si erreur: Vérifier les logs Azure
- Si "queued": Lancer le worker en background
- Si "completed": Async fonctionne! 🎉
""")


if __name__ == "__main__":
    asyncio.run(test_async_indexation())
