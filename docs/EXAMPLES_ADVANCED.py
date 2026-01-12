"""
EXEMPLES AVANCÉS - Image Search API
====================================

Ce fichier contient les exemples avancés non couverts dans EXAMPLES.py:
- Génération d'embeddings CLIP
- Vérification du statut des tâches asynchrones
- Monitoring et statistiques de queue
- Métriques de performance
- Suppression de produits
"""

import requests
from typing import List, Dict

API_URL = "http://20.238.104.13:8000"


# ============================================================================
# 1. GÉNÉRER UN EMBEDDING TEXTE (CLIP)
# ============================================================================

def get_text_embedding(text: str) -> List[float]:
    """
    Générer un embedding CLIP pour une requête texte.
    Utile pour stocker et comparer les embeddings.
    
    Args:
        text: Texte à embedder (ex: "red running shoes")
        
    Returns:
        List[float]: Embedding de 512 dimensions CLIP
        
    Usage:
        embedding = get_text_embedding("blue shoes")
        print(f"Embedding: {len(embedding)} dimensions")
    """
    try:
        response = requests.post(
            f"{API_URL}/api/v1/embed",
            json={"text": text},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        embedding = data.get("embedding", [])
        print(f"✅ Text embedding généré: {len(embedding)} dimensions")
        return embedding
    except Exception as e:
        print(f"❌ Erreur embedding texte: {e}")
        return []


# ============================================================================
# 2. GÉNÉRER UN EMBEDDING IMAGE (CLIP)
# ============================================================================

def get_image_embedding(image_path: str) -> List[float]:
    """
    Générer un embedding CLIP pour une image.
    Utile pour indexing et recherche par image.
    
    Args:
        image_path: Chemin vers le fichier image local
        
    Returns:
        List[float]: Embedding de 512 dimensions CLIP
        
    Usage:
        embedding = get_image_embedding("shoe.jpg")
        print(f"Embedding: {len(embedding)} dimensions")
    """
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{API_URL}/api/v1/embed-image",
                files=files,
                timeout=30
            )
        response.raise_for_status()
        data = response.json()
        embedding = data.get("embedding", [])
        print(f"✅ Image embedding généré: {len(embedding)} dimensions")
        return embedding
    except Exception as e:
        print(f"❌ Erreur embedding image: {e}")
        return []


# ============================================================================
# 3. VÉRIFIER LE STATUT D'UNE TÂCHE ASYNCHRONE
# ============================================================================

def check_job_status(job_id: str) -> Dict:
    """
    Vérifier le statut d'une tâche d'indexing asynchrone.
    
    Statuts possibles:
    - pending: Tâche en attente de traitement
    - processing: Tâche actuellement traitée
    - completed: Tâche terminée avec succès
    - failed: Tâche échouée
    
    Args:
        job_id: ID de la tâche (retourné lors de l'indexing)
        
    Returns:
        Dict with: {
            'job_id': str,
            'status': 'pending|processing|completed|failed',
            'product_id': str,
            'product_name': str,
            'progress': int,  # 0-100
            'indexed_at': str,
            'error': str or null
        }
        
    Usage:
        status = check_job_status("550e8400-e29b-41d4-a716-446655440000")
        print(f"Status: {status['status']}")
        if status['status'] == 'failed':
            print(f"Error: {status['error']}")
    """
    try:
        response = requests.get(
            f"{API_URL}/api/v1/queue/status/{job_id}",
            timeout=10
        )
        response.raise_for_status()
        status = response.json()
        print(f"✅ Statut tâche: {status['status']}")
        return status
    except Exception as e:
        print(f"❌ Erreur vérification statut: {e}")
        return {}


# ============================================================================
# 4. RÉCUPÉRER LES STATISTIQUES DE LA QUEUE
# ============================================================================

def get_queue_stats() -> Dict:
    """
    Récupérer les statistiques de la queue Redis.
    
    Returns:
        {
            'total_jobs': int,
            'pending': int,           # Tâches en attente
            'processing': int,        # Tâches en cours
            'completed': int,         # Tâches complétées
            'failed': int,            # Tâches échouées
            'avg_time_ms': float      # Temps moyen de traitement
        }
        
    Usage:
        stats = get_queue_stats()
        print(f"Pending: {stats['pending']}")
        print(f"Completed: {stats['completed']}")
        print(f"Failed: {stats['failed']}")
    """
    try:
        response = requests.get(
            f"{API_URL}/api/v1/queue/stats",
            timeout=10
        )
        response.raise_for_status()
        stats = response.json()
        print(f"📊 Queue stats:")
        print(f"  - Total: {stats.get('total_jobs', 0)}")
        print(f"  - Pending: {stats.get('pending', 0)}")
        print(f"  - Processing: {stats.get('processing', 0)}")
        print(f"  - Completed: {stats.get('completed', 0)}")
        print(f"  - Failed: {stats.get('failed', 0)}")
        print(f"  - Avg time: {stats.get('avg_time_ms', 0)}ms")
        return stats
    except Exception as e:
        print(f"❌ Erreur récupération stats: {e}")
        return {}


# ============================================================================
# 5. RÉCUPÉRER LES MÉTRIQUES DE PERFORMANCE
# ============================================================================

def get_performance_metrics() -> Dict:
    """
    Récupérer les métriques de performance de l'API.
    
    Returns:
        {
            'avg_search_latency_ms': float,   # Latence moyenne
            'p95_latency_ms': float,          # 95e percentile
            'p99_latency_ms': float,          # 99e percentile
            'requests_per_sec': float,        # Débit actuel
            'total_requests': int,            # Total reqêtes servies
            'uptime_hours': float,            # Uptime en heures
            'cpu_usage_percent': float,       # Usage CPU
            'memory_usage_mb': int            # Memory usage
        }
        
    Usage:
        metrics = get_performance_metrics()
        print(f"Avg latency: {metrics['avg_search_latency_ms']}ms")
        print(f"P95: {metrics['p95_latency_ms']}ms")
        print(f"Requests/sec: {metrics['requests_per_sec']}")
    """
    try:
        response = requests.get(
            f"{API_URL}/api/v1/performance/monitor",
            timeout=10
        )
        response.raise_for_status()
        metrics = response.json()
        print(f"📈 Performance Metrics:")
        print(f"  - Avg latency: {metrics.get('avg_search_latency_ms', 0)}ms")
        print(f"  - P95 latency: {metrics.get('p95_latency_ms', 0)}ms")
        print(f"  - P99 latency: {metrics.get('p99_latency_ms', 0)}ms")
        print(f"  - Requests/sec: {metrics.get('requests_per_sec', 0)}")
        print(f"  - Total requests: {metrics.get('total_requests', 0)}")
        print(f"  - Uptime: {metrics.get('uptime_hours', 0)}h")
        print(f"  - CPU: {metrics.get('cpu_usage_percent', 0)}%")
        print(f"  - Memory: {metrics.get('memory_usage_mb', 0)}MB")
        return metrics
    except Exception as e:
        print(f"❌ Erreur récupération metrics: {e}")
        return {}


# ============================================================================
# 6. SUPPRIMER UN PRODUIT DE L'INDEX
# ============================================================================

def delete_product(product_id: str) -> bool:
    """
    Supprimer un produit de l'index Qdrant.
    
    Args:
        product_id: ID du produit à supprimer
        
    Returns:
        bool: True si succès, False sinon
        
    Usage:
        if delete_product("123"):
            print("Product deleted successfully")
        else:
            print("Failed to delete product")
    """
    try:
        response = requests.delete(
            f"{API_URL}/api/v1/collections/products/points/{product_id}",
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            print(f"✅ Produit {product_id} supprimé de l'index")
            return True
        else:
            print(f"❌ Erreur suppression: {result.get('message')}")
            return False
    except Exception as e:
        print(f"❌ Erreur suppression produit: {e}")
        return False


# ============================================================================
# 7. PATTERN DE MONITORING COMPLET
# ============================================================================

def full_monitoring_report():
    """
    Générer un rapport complet de monitoring de l'API.
    Combine santé, queue, et performance.
    """
    print("\n" + "="*80)
    print("MONITORING COMPLET - IMAGE SEARCH API")
    print("="*80 + "\n")
    
    # 1. Queue stats
    print("1️⃣  QUEUE STATISTICS:")
    queue_stats = get_queue_stats()
    print()
    
    # 2. Performance metrics
    print("2️⃣  PERFORMANCE METRICS:")
    perf_metrics = get_performance_metrics()
    print()
    
    # 3. Health check
    try:
        response = requests.get(f"{API_URL}/api/v1/health", timeout=5)
        health = response.json()
        print("3️⃣  API HEALTH:")
        print(f"  - Status: {health.get('status')}")
        print(f"  - Version: {health.get('version')}")
        print(f"  - Qdrant connected: {health.get('qdrant', {}).get('connected')}")
        stats = health.get('qdrant', {}).get('stats', {})
        print(f"  - Products indexed: {stats.get('points_count', 0)}")
        print()
    except Exception as e:
        print(f"❌ Health check failed: {e}\n")
    
    print("="*80 + "\n")


# ============================================================================
# 8. PATTERN DE WORKFLOW COMPLET
# ============================================================================

def complete_workflow():
    """
    Pattern de workflow complet pour utiliser l'API.
    
    Flow:
    1. Vérifier santé
    2. Générer embeddings
    3. Indexer produits
    4. Vérifier statut
    5. Effectuer recherches
    6. Monitorer performance
    """
    print("\n" + "="*80)
    print("COMPLETE WORKFLOW - IMAGE SEARCH API")
    print("="*80 + "\n")
    
    # 1. Health check
    print("Step 1️⃣ : API Health Check")
    try:
        response = requests.get(f"{API_URL}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy\n")
        else:
            print("❌ API is not healthy - Stopping\n")
            return
    except Exception as e:
        print(f"❌ Cannot reach API: {e} - Stopping\n")
        return
    
    # 2. Text embedding
    print("Step 2️⃣ : Generate Text Embedding")
    text_emb = get_text_embedding("blue running shoes")
    print()
    
    # 3. Image embedding (demo)
    print("Step 3️⃣ : Generate Image Embedding")
    print("(Skipping - requires actual image file)\n")
    
    # 4. Check initial stats
    print("Step 4️⃣ : Initial Queue Stats")
    initial_stats = get_queue_stats()
    print()
    
    # 5. Performance check
    print("Step 5️⃣ : Performance Metrics")
    perf = get_performance_metrics()
    print()
    
    # 6. Final report
    print("Step 6️⃣ : Final Report")
    print("✅ Workflow completed successfully\n")
    
    print("="*80 + "\n")


# ============================================================================
# MAIN - DEMO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("IMAGE SEARCH API - ADVANCED EXAMPLES")
    print("="*80)
    
    # Exécuter les démonstrations
    full_monitoring_report()
    complete_workflow()
    
    # Exemples individuels:
    # text_embedding = get_text_embedding("shoes")
    # job_status = check_job_status("job-uuid-here")
    # queue_stats = get_queue_stats()
    # perf_metrics = get_performance_metrics()
    # delete_product("product-id")
