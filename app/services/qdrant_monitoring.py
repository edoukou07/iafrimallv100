"""
Qdrant RAM and Performance Monitoring Module

Monitors:
1. RAM usage (container vs Qdrant cache)
2. Disk usage (vector database size)
3. Query latency
4. Cache hit rates
5. Collection statistics

Usage:
    from app.services.qdrant_monitoring import QdrantMonitor
    monitor = QdrantMonitor(qdrant_service)
    stats = monitor.get_performance_stats()
"""

import os
import psutil
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Single query performance metrics."""
    timestamp: datetime
    latency_ms: float
    query_size: int
    results_count: int
    cache_hit: bool  # True if result from cache


@dataclass
class PerformanceStats:
    """Overall performance statistics."""
    timestamp: datetime
    
    # Memory
    container_memory_mb: float
    container_memory_percent: float
    qdrant_cache_mb: float
    
    # Disk
    database_size_mb: float
    snapshots_size_mb: float
    total_disk_mb: float
    
    # Collection stats
    points_count: int
    vectors_count: int
    
    # Query performance
    avg_query_latency_ms: float
    p95_query_latency_ms: float
    p99_query_latency_ms: float
    cache_hit_rate: float
    
    # Health
    is_healthy: bool
    warnings: List[str]


class QdrantMonitor:
    """Monitor Qdrant performance and resource usage."""
    
    def __init__(self, qdrant_service, history_size: int = 1000):
        """
        Initialize monitor.
        
        Args:
            qdrant_service: IntegratedQdrantService instance
            history_size: Number of queries to keep in history for stats
        """
        self.qdrant_service = qdrant_service
        self.data_path = os.getenv("QDRANT_DATA_PATH", "/app/data/qdrant")
        
        # Query history for latency calculations
        self.query_history: deque = deque(maxlen=history_size)
        
        # Container memory info
        self.container_memory_limit_mb = self._get_container_memory_limit()
        
        logger.info(f"QdrantMonitor initialized")
        logger.info(f"  Data path: {self.data_path}")
        logger.info(f"  Container memory limit: {self.container_memory_limit_mb} MB")
    
    def _get_container_memory_limit(self) -> float:
        """Get container memory limit from cgroup."""
        try:
            # Read from cgroup v2 (modern containers)
            if os.path.exists("/sys/fs/cgroup/memory.max"):
                with open("/sys/fs/cgroup/memory.max") as f:
                    limit = int(f.read().strip())
                    if limit > 0:
                        return limit / 1024 / 1024
            
            # Read from cgroup v1 (older containers)
            if os.path.exists("/sys/fs/cgroup/memory/memory.limit_in_bytes"):
                with open("/sys/fs/cgroup/memory/memory.limit_in_bytes") as f:
                    limit = int(f.read().strip())
                    if limit > 0:
                        return limit / 1024 / 1024
        except Exception as e:
            logger.warning(f"Could not read memory limit from cgroup: {e}")
        
        # Fallback: system total memory
        return psutil.virtual_memory().total / 1024 / 1024
    
    def record_query(self, latency_ms: float, query_size: int, 
                    results_count: int, cache_hit: bool = False):
        """Record query performance metrics."""
        metric = QueryMetrics(
            timestamp=datetime.now(),
            latency_ms=latency_ms,
            query_size=query_size,
            results_count=results_count,
            cache_hit=cache_hit
        )
        self.query_history.append(metric)
    
    def _get_disk_usage_mb(self) -> tuple[float, float]:
        """
        Get disk usage for database and snapshots.
        
        Returns:
            (database_size_mb, snapshots_size_mb)
        """
        database_size = 0
        snapshots_size = 0
        
        if os.path.exists(self.data_path):
            try:
                for dirpath, dirnames, filenames in os.walk(self.data_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        size = os.path.getsize(filepath)
                        
                        if "snapshots" in dirpath:
                            snapshots_size += size
                        else:
                            database_size += size
            except Exception as e:
                logger.warning(f"Error calculating disk usage: {e}")
        
        return (
            database_size / 1024 / 1024,
            snapshots_size / 1024 / 1024
        )
    
    def _get_memory_stats(self) -> tuple[float, float, float]:
        """
        Get memory statistics.
        
        Returns:
            (container_memory_mb, container_memory_percent, qdrant_cache_mb)
        """
        try:
            # Get process memory
            process = psutil.Process()
            process_memory_mb = process.memory_info().rss / 1024 / 1024
            
            # Calculate container memory percentage
            memory_percent = (process_memory_mb / self.container_memory_limit_mb) * 100
            
            # Estimate Qdrant cache (rough estimate from config)
            # This is a simplified calculation - actual cache is managed by Qdrant
            qdrant_cache_mb = min(256, process_memory_mb * 0.6)  # Estimate 60% of process memory
            
            return (
                process_memory_mb,
                memory_percent,
                qdrant_cache_mb
            )
        except Exception as e:
            logger.warning(f"Error getting memory stats: {e}")
            return (0, 0, 0)
    
    def _get_query_latency_stats(self) -> tuple[float, float, float, float]:
        """
        Calculate query latency statistics.
        
        Returns:
            (avg_latency_ms, p95_latency_ms, p99_latency_ms, cache_hit_rate)
        """
        if not self.query_history:
            return (0, 0, 0, 0)
        
        latencies = [q.latency_ms for q in self.query_history]
        cache_hits = sum(1 for q in self.query_history if q.cache_hit)
        
        # Calculate percentiles
        sorted_latencies = sorted(latencies)
        avg_latency = sum(latencies) / len(latencies)
        p95_idx = int(len(sorted_latencies) * 0.95)
        p99_idx = int(len(sorted_latencies) * 0.99)
        
        p95_latency = sorted_latencies[p95_idx] if p95_idx < len(sorted_latencies) else sorted_latencies[-1]
        p99_latency = sorted_latencies[p99_idx] if p99_idx < len(sorted_latencies) else sorted_latencies[-1]
        
        cache_hit_rate = (cache_hits / len(self.query_history)) * 100 if self.query_history else 0
        
        return (avg_latency, p95_latency, p99_latency, cache_hit_rate)
    
    def _check_health(self, memory_percent: float, avg_latency: float) -> tuple[bool, List[str]]:
        """
        Check system health and identify warnings.
        
        Returns:
            (is_healthy, warnings_list)
        """
        warnings = []
        
        # Check memory
        if memory_percent > 90:
            warnings.append(f"CRITICAL: Memory usage at {memory_percent:.1f}%")
        elif memory_percent > 80:
            warnings.append(f"WARNING: Memory usage at {memory_percent:.1f}%")
        
        # Check latency
        if avg_latency > 200:
            warnings.append(f"WARNING: High avg query latency {avg_latency:.1f}ms")
        elif avg_latency > 100:
            warnings.append(f"INFO: Elevated query latency {avg_latency:.1f}ms")
        
        # Check Qdrant health
        try:
            if not self.qdrant_service.health_check():
                warnings.append("ERROR: Qdrant health check failed")
                return (False, warnings)
        except Exception as e:
            warnings.append(f"ERROR: Qdrant not responding: {e}")
            return (False, warnings)
        
        is_healthy = len([w for w in warnings if w.startswith("CRITICAL")]) == 0
        return (is_healthy, warnings)
    
    def get_performance_stats(self) -> PerformanceStats:
        """Get current performance and resource statistics."""
        try:
            # Memory stats
            memory_mb, memory_pct, cache_mb = self._get_memory_stats()
            
            # Disk stats
            db_size_mb, snap_size_mb = self._get_disk_usage_mb()
            
            # Collection stats
            collection_stats = self.qdrant_service.get_collection_stats()
            
            # Query latency stats
            avg_lat, p95_lat, p99_lat, cache_rate = self._get_query_latency_stats()
            
            # Health check
            is_healthy, warnings = self._check_health(memory_pct, avg_lat)
            
            stats = PerformanceStats(
                timestamp=datetime.now(),
                container_memory_mb=memory_mb,
                container_memory_percent=memory_pct,
                qdrant_cache_mb=cache_mb,
                database_size_mb=db_size_mb,
                snapshots_size_mb=snap_size_mb,
                total_disk_mb=db_size_mb + snap_size_mb,
                points_count=collection_stats.get("points_count", 0),
                vectors_count=collection_stats.get("vectors_count", 0),
                avg_query_latency_ms=avg_lat,
                p95_query_latency_ms=p95_lat,
                p99_query_latency_ms=p99_lat,
                cache_hit_rate=cache_rate,
                is_healthy=is_healthy,
                warnings=warnings
            )
            
            return stats
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            # Return zeros on error
            return PerformanceStats(
                timestamp=datetime.now(),
                container_memory_mb=0,
                container_memory_percent=0,
                qdrant_cache_mb=0,
                database_size_mb=0,
                snapshots_size_mb=0,
                total_disk_mb=0,
                points_count=0,
                vectors_count=0,
                avg_query_latency_ms=0,
                p95_query_latency_ms=0,
                p99_query_latency_ms=0,
                cache_hit_rate=0,
                is_healthy=False,
                warnings=[f"Error getting stats: {e}"]
            )
    
    def print_stats(self, stats: Optional[PerformanceStats] = None):
        """Pretty print performance statistics."""
        if stats is None:
            stats = self.get_performance_stats()
        
        print("\n" + "="*70)
        print("QDRANT PERFORMANCE MONITORING")
        print("="*70)
        
        # Memory section
        print("\n📊 MEMORY USAGE")
        print(f"  Container Memory: {stats.container_memory_mb:.1f} MB / {self.container_memory_limit_mb:.1f} MB ({stats.container_memory_percent:.1f}%)")
        print(f"  Qdrant Cache (est): {stats.qdrant_cache_mb:.1f} MB")
        
        # Disk section
        print("\n💾 DISK USAGE")
        print(f"  Database: {stats.database_size_mb:.1f} MB")
        print(f"  Snapshots: {stats.snapshots_size_mb:.1f} MB")
        print(f"  Total: {stats.total_disk_mb:.1f} MB")
        
        # Collection section
        print("\n📦 COLLECTION STATS")
        print(f"  Points indexed: {stats.points_count:,}")
        print(f"  Vectors: {stats.vectors_count:,}")
        
        # Query performance
        print("\n⚡ QUERY PERFORMANCE")
        print(f"  Avg Latency: {stats.avg_query_latency_ms:.1f} ms")
        print(f"  P95 Latency: {stats.p95_query_latency_ms:.1f} ms")
        print(f"  P99 Latency: {stats.p99_query_latency_ms:.1f} ms")
        print(f"  Cache Hit Rate: {stats.cache_hit_rate:.1f}%")
        
        # Health
        status_icon = "✅" if stats.is_healthy else "⚠️"
        print(f"\n{status_icon} HEALTH: {'HEALTHY' if stats.is_healthy else 'DEGRADED'}")
        if stats.warnings:
            for warning in stats.warnings:
                print(f"  ⚠️  {warning}")
        
        print("="*70 + "\n")
    
    def export_stats_json(self, stats: Optional[PerformanceStats] = None) -> Dict:
        """Export statistics as dictionary (for JSON serialization)."""
        if stats is None:
            stats = self.get_performance_stats()
        
        return {
            **asdict(stats),
            'timestamp': stats.timestamp.isoformat(),
            'memory_limit_mb': self.container_memory_limit_mb
        }
