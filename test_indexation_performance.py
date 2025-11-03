#!/usr/bin/env python3
"""
Test de performance pour l'indexation.
Teste le temps d'indexation par étape :
- Génération d'embeddings CLIP
- Indexation dans Qdrant
- End-to-end (total)
"""

import asyncio
import time
import json
from typing import Dict, List
from pathlib import Path
import sys

# Ajouter le répertoire app au path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from services.embedding_service import EmbeddingService
from services.qdrant_service import QdrantService
from core.logger import get_logger

logger = get_logger(__name__)


class IndexationPerformanceTest:
    """Test de performance pour l'indexation."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService()
        self.results = {
            "embedding_times": [],
            "indexing_times": [],
            "total_times": [],
            "errors": []
        }

    async def test_single_product(self, product_data: Dict) -> Dict:
        """Test l'indexation d'un seul produit."""
        
        test_result = {
            "product_id": product_data.get("id", "unknown"),
            "name": product_data.get("name", "unknown"),
            "embedding_time": 0,
            "indexing_time": 0,
            "total_time": 0,
            "success": False,
            "error": None
        }

        try:
            # 1. Tester la génération d'embedding
            start_embed = time.time()
            
            text = f"{product_data.get('name', '')} {product_data.get('description', '')}"
            embedding = await asyncio.to_thread(
                self.embedding_service.embed_text,
                text
            )
            
            embed_time = time.time() - start_embed
            test_result["embedding_time"] = embed_time
            self.results["embedding_times"].append(embed_time)

            logger.info(f"✓ Embedding généré en {embed_time:.2f}s")

            # 2. Tester l'indexation dans Qdrant
            start_index = time.time()
            
            await asyncio.to_thread(
                self.qdrant_service.index_product,
                product_id=product_data.get("id"),
                product_name=product_data.get("name"),
                embedding=embedding,
                metadata={
                    "description": product_data.get("description", ""),
                    "image_url": product_data.get("image_url", "")
                }
            )
            
            index_time = time.time() - start_index
            test_result["indexing_time"] = index_time
            self.results["indexing_times"].append(index_time)

            logger.info(f"✓ Indexation Qdrant en {index_time:.2f}s")

            # 3. Calculer le total
            total_time = embed_time + index_time
            test_result["total_time"] = total_time
            self.results["total_times"].append(total_time)
            test_result["success"] = True

            logger.info(f"✓ Total pour '{product_data.get('name')}': {total_time:.2f}s\n")

        except Exception as e:
            error_msg = str(e)
            test_result["error"] = error_msg
            test_result["success"] = False
            self.results["errors"].append(error_msg)
            logger.error(f"✗ Erreur: {error_msg}\n")

        return test_result

    async def test_batch_indexing(self, num_products: int = 5, sequential: bool = True) -> List[Dict]:
        """
        Test l'indexation d'un batch de produits.
        
        Args:
            num_products: Nombre de produits à tester
            sequential: Si True, indexe séquentiellement. Si False, en parallèle.
        """
        
        # Générer des produits de test
        test_products = self._generate_test_products(num_products)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"TEST BATCH: {num_products} produits ({'séquentiel' if sequential else 'parallèle'})")
        logger.info(f"{'='*70}\n")

        batch_results = []
        start_total = time.time()

        if sequential:
            # Mode séquentiel
            for product in test_products:
                result = await self.test_single_product(product)
                batch_results.append(result)
        else:
            # Mode parallèle
            tasks = [self.test_single_product(product) for product in test_products]
            batch_results = await asyncio.gather(*tasks, return_exceptions=False)

        total_batch_time = time.time() - start_total

        # Résumé du batch
        successful = sum(1 for r in batch_results if r["success"])
        failed = num_products - successful

        logger.info(f"{'='*70}")
        logger.info(f"RÉSUMÉ BATCH")
        logger.info(f"{'='*70}")
        logger.info(f"Total: {num_products} produits")
        logger.info(f"✓ Succès: {successful}")
        logger.info(f"✗ Erreurs: {failed}")
        logger.info(f"Temps total: {total_batch_time:.2f}s")
        logger.info(f"Moyenne par produit: {total_batch_time/num_products:.2f}s")
        logger.info(f"Débit: {num_products/total_batch_time:.2f} produits/sec\n")

        return batch_results

    async def run_full_test(self):
        """Exécute une suite complète de tests."""
        
        logger.info("\n" + "="*70)
        logger.info("TEST DE PERFORMANCE D'INDEXATION")
        logger.info("="*70 + "\n")

        # Test 1: Un seul produit
        logger.info("┌─ TEST 1: Un seul produit")
        logger.info("└─\n")
        single_product = self._generate_test_products(1)[0]
        single_result = await self.test_single_product(single_product)

        # Test 2: 5 produits séquentiels
        logger.info("┌─ TEST 2: 5 produits séquentiels")
        logger.info("└─\n")
        seq_results = await self.test_batch_indexing(num_products=5, sequential=True)

        # Test 3: 5 produits en parallèle
        logger.info("┌─ TEST 3: 5 produits en parallèle")
        logger.info("└─\n")
        par_results = await self.test_batch_indexing(num_products=5, sequential=False)

        # Afficher les statistiques finales
        self._print_final_stats(single_result, seq_results, par_results)

    def _print_final_stats(self, single: Dict, sequential: List[Dict], parallel: List[Dict]):
        """Affiche les statistiques finales."""
        
        logger.info("\n" + "="*70)
        logger.info("STATISTIQUES FINALES")
        logger.info("="*70 + "\n")

        # Statistiques pour un seul produit
        logger.info("📊 UN SEUL PRODUIT")
        logger.info(f"  Embedding: {single['embedding_time']:.2f}s")
        logger.info(f"  Indexation: {single['indexing_time']:.2f}s")
        logger.info(f"  Total: {single['total_time']:.2f}s\n")

        # Statistiques pour les tests batch
        seq_total = sum(r["total_time"] for r in sequential if r["success"])
        par_total = max(r["total_time"] for r in parallel if r["success"])

        logger.info("📊 5 PRODUITS - SÉQUENTIEL")
        logger.info(f"  Embedding total: {sum(r['embedding_time'] for r in sequential if r['success']):.2f}s")
        logger.info(f"  Indexation total: {sum(r['indexing_time'] for r in sequential if r['success']):.2f}s")
        logger.info(f"  Temps total: {seq_total:.2f}s\n")

        logger.info("📊 5 PRODUITS - PARALLÈLE")
        logger.info(f"  Temps total (max): {par_total:.2f}s")
        if seq_total > 0:
            speedup = seq_total / par_total
            logger.info(f"  Speedup: {speedup:.1f}x\n")

        # Résumé des goulots d'étranglement
        logger.info("⚠️  GOULOTS D'ÉTRANGLEMENT")
        if self.results["embedding_times"]:
            avg_embed = sum(self.results["embedding_times"]) / len(self.results["embedding_times"])
            logger.info(f"  Embedding moyen: {avg_embed:.2f}s (main bottleneck)")
        if self.results["indexing_times"]:
            avg_index = sum(self.results["indexing_times"]) / len(self.results["indexing_times"])
            logger.info(f"  Indexation moyen: {avg_index:.2f}s\n")

        # Recommandations
        logger.info("💡 RECOMMANDATIONS")
        if self.results["embedding_times"] and max(self.results["embedding_times"]) > 3:
            logger.info("  ⚠️  L'embedding CLIP prend > 3s (GPU lent?)")
            logger.info("     → Vérifier GPU disponible (nvidia-smi)")
            logger.info("     → Utiliser quantization du modèle")
        logger.info("  → Lancer 3-5 workers pour paralléliser")
        logger.info("  → Utiliser endpoint async (/index-product-with-image)")
        logger.info("  → Voir PARALLELISME_INDEXATION.md pour configs\n")

    @staticmethod
    def _generate_test_products(count: int = 5) -> List[Dict]:
        """Génère des produits de test."""
        products = []
        for i in range(count):
            products.append({
                "id": f"test-product-{i+1}",
                "name": f"Produit Test {i+1}",
                "description": f"Ceci est une description de produit de test numéro {i+1}. "
                              f"C'est un produit pour tester la performance de l'indexation. "
                              f"Le produit contient plusieurs mots pour générer un embedding significatif. "
                              f"Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                              f"Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
                "image_url": f"https://example.com/image{i+1}.jpg"
            })
        return products


async def main():
    """Point d'entrée principal."""
    try:
        tester = IndexationPerformanceTest()
        await tester.run_full_test()
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
