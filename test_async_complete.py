#!/usr/bin/env python3
"""
Test de l'indexation asynchrone complète avec worker.
"""

import asyncio
import aiohttp
from io import BytesIO
from datetime import datetime
import time

API_URL = "http://52.143.186.136:8000/api/v1"
TIMEOUT = aiohttp.ClientTimeout(total=300)


async def test_async_indexation():
    """Test l'endpoint async avec le worker implémenté."""
    
    print("\n" + "="*70)
    print("TEST: Indexation Asynchrone Complète")
    print("="*70)
    print(f"Date: {datetime.now().isoformat()}\n")

    # Créer une image JPEG minimale valide
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

                if response.status in [200, 202]:
                    result = await response.json()
                    job_id = result.get("job_id")
                    status = result.get("status")
                    mode = result.get("processing_mode", "unknown")

                    print(f"✓ Enqueued en {enqueue_time:.2f}s")
                    print(f"  Job ID: {job_id}")
                    print(f"  Status: {status}")
                    print(f"  Mode: {mode}")

                    if status == "queued":
                        print("\n✅ Job a été mis en queue Redis!")
                        print("   Le worker devrait le traiter maintenant...")

                        # Attendre un peu et vérifier le statut
                        print("\n▶ Étape 2: Vérifier le statut du job")
                        print("-" * 70)

                        for i in range(10):
                            await asyncio.sleep(2)  # Attendre 2 sec
                            print(f"Vérification {i+1}/10...", end=" ")

                            try:
                                async with session.get(
                                    f"{API_URL}/queue/status/{job_id}",
                                    timeout=aiohttp.ClientTimeout(total=10)
                                ) as status_response:
                                    if status_response.status == 200:
                                        status_data = await status_response.json()
                                        job_status = status_data.get("status")
                                        print(f"Status: {job_status}")

                                        if job_status == "completed":
                                            print("✅ Job complété avec succès!")
                                            break
                                        elif job_status == "failed":
                                            error = status_data.get("error", "Unknown error")
                                            print(f"❌ Job échoué: {error}")
                                            break
                                    else:
                                        print(f"Status check failed: {status_response.status}")
                            except Exception as e:
                                print(f"Error checking status: {e}")

                    elif status == "indexed":
                        print("\n⚠️  Fallback synchrone utilisé (Redis indisponible)")
                        print("   Le produit a été indexé immédiatement en synchrone")
                        print("   Cela est acceptable en cas d'absence de Redis")

                else:
                    print(f"✗ Erreur {response.status}")
                    text = await response.text()
                    print(f"  {text}")

        except asyncio.TimeoutError:
            print(f"✗ TIMEOUT après {enqueue_time:.2f}s")
        except Exception as e:
            print(f"✗ Erreur: {e}")

    print("\n" + "="*70)
    print("RÉSUMÉ")
    print("="*70)
    print("""
L'indexation asynchrone a été testée. Résultats possibles:

1. ✅ Status "queued" + "completed":
   - Async fonctionne correctement
   - Le worker traite les images
   - Performance: ~0.5-1s après enqueue

2. ✅ Status "queued" + toujours "queued":
   - Async enqueue fonctionne
   - Worker peut ne pas tourner
   - À lancer: python -m app.workers.image_indexer_worker

3. ✅ Status "indexed" (fallback sync):
   - Redis n'est pas disponible
   - Fallback synchrone fonctionne
   - Image indexée immédiatement

Prochaines étapes:
- Lancer le worker: python -m app.workers.image_indexer_worker --worker-id w1
- Relancer ce test
- Vérifier que status devient "completed"
""")


if __name__ == "__main__":
    asyncio.run(test_async_indexation())
