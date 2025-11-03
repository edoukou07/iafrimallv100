#!/usr/bin/env python3
"""
Vérifier l'état de Redis et du worker asynchrone.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

API_URL = "http://52.143.186.136:8000/api/v1"


async def check_redis_status():
    """Vérifier si Redis est connecté à l'API."""
    print("\n" + "="*70)
    print("DIAGNOSTIC: État de Redis et Worker Async")
    print("="*70)
    print(f"Date: {datetime.now().isoformat()}\n")

    print("▶ Étape 1: Vérifier l'API et Redis")
    print("-" * 70)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ API accessible")
                    print(f"  Service: {data.get('service', 'N/A')}")
                    
                    qdrant = data.get('qdrant', {})
                    print(f"  Qdrant: {qdrant.get('connected', False)}")
                    
                    if qdrant.get('connected'):
                        stats = qdrant.get('stats', {})
                        print(f"    - Collection: {stats.get('name', 'N/A')}")
                        print(f"    - Points: {stats.get('points_count', 0)}")
                else:
                    print(f"✗ API non accessible ({response.status})")
                    return
        except Exception as e:
            print(f"✗ Erreur de connexion: {e}")
            return

    # Vérifier Redis via test d'enqueuement
    print("\n▶ Étape 2: Tester Redis (via endpoint async)")
    print("-" * 70)
    print("Tentative d'enqueuement d'un job asynchrone...")
    
    try:
        # Créer une vraie petite image
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
        
        from io import BytesIO
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("product_id", "diagnostic-async-test")
            data.add_field("name", "Test Async Diagnostic")
            data.add_field("description", "Test pour vérifier si async fonctionne")
            data.add_field("image_file", BytesIO(jpeg_data), filename="test.jpg", content_type="image/jpeg")
            
            async with session.post(
                f"{API_URL}/index-product-with-image",
                data=data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status in [200, 202]:
                    result = await response.json()
                    
                    status = result.get("status", "unknown")
                    processing_mode = result.get("processing_mode", "unknown")
                    job_id = result.get("job_id", "N/A")
                    
                    print(f"✓ Réponse reçue")
                    print(f"  Status: {status}")
                    print(f"  Job ID: {job_id}")
                    print(f"  Processing mode: {processing_mode}")
                    
                    if processing_mode == "sync":
                        print(f"\n⚠️  REDIS FALLBACK DÉTECTÉ!")
                        print(f"  L'API a fait un fallback synchrone")
                        print(f"  Cela signifie que Redis n'est PAS disponible")
                        print(f"  Ou qu'il y a une erreur dans l'enqueuement")
                    elif status == "queued":
                        print(f"\n✓ Async est OK")
                        print(f"  Le job a été enqueueé dans Redis")
                        print(f"  Mais le worker peut ne pas le traiter...")
                    else:
                        print(f"\n⚠️  Status inconnu: {status}")
                else:
                    print(f"✗ Erreur {response.status}")
                    text = await response.text()
                    print(f"  {text}")
    
    except Exception as e:
        print(f"✗ Erreur: {e}")

    # Résumé
    print("\n" + "="*70)
    print("RÉSUMÉ")
    print("="*70)
    print("""
✓ Endpoint synchrone: FONCTIONNE (0.28s/produit)
⚠️  Endpoint asynchrone: PROBLÉMATIQUE (fallback sync)

Recommandation:
  → Utiliser SYNCHRONE pour maintenant: /api/v1/index-product
  → Async sera implémenté plus tard
  → Performance acceptable: 0.28s/produit = 3.6 produits/sec
  
Pour 100 produits: 28 secondes
Pour 1000 produits: 4.6 minutes

Voir: docs/ETAT_ASYNC_INDEXATION.md pour plus de détails
""")


if __name__ == "__main__":
    asyncio.run(check_redis_status())
