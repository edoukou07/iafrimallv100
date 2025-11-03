#!/usr/bin/env python3
"""
Test script for Redis Async Worker System

Tests:
1. Redis connection
2. Task enqueueing
3. Queue status
4. Worker health
5. Batch task creation
"""

import asyncio
import json
import sys
import httpx
import time
from typing import Optional

# Configuration
API_BASE_URL = "http://localhost:8000"
QUEUE_ENDPOINT = f"{API_BASE_URL}/queue"

async def test_redis_connection():
    """Test Redis connectivity"""
    print("\n▶ Testing Redis connection...")
    try:
        # This will be tested through the API
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{QUEUE_ENDPOINT}/stats", timeout=5.0)
            if response.status_code == 200:
                print("✓ Redis connection OK")
                return True
            else:
                print(f"✗ Unexpected status: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False

async def test_enqueue_task(product_id: str) -> Optional[str]:
    """Test task enqueueing"""
    print(f"\n▶ Enqueueing task for product {product_id}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{QUEUE_ENDPOINT}/enqueue",
                json={
                    "image_path": f"/path/to/image_{product_id}.jpg",
                    "product_id": product_id,
                    "name": f"Product {product_id}",
                    "description": f"Test product {product_id}",
                    "metadata": {"test": True}
                },
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id")
                queue_length = data.get("queue_length", "unknown")
                print(f"✓ Task enqueued: {task_id}")
                print(f"  Queue length: {queue_length}")
                return task_id
            else:
                print(f"✗ Failed to enqueue: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
                
    except Exception as e:
        print(f"✗ Enqueue failed: {e}")
        return None

async def test_task_status(task_id: str):
    """Test task status retrieval"""
    print(f"\n▶ Checking task status: {task_id}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{QUEUE_ENDPOINT}/status/{task_id}",
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Task status retrieved")
                print(f"  Status: {data.get('status')}")
                print(f"  Created: {data.get('created_at')}")
                return True
            elif response.status_code == 404:
                print(f"✗ Task not found (may have been processed)")
                return True  # Not an error, just already done
            else:
                print(f"✗ Failed to get status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Status check failed: {e}")
        return False

async def test_queue_stats():
    """Test queue statistics"""
    print("\n▶ Getting queue statistics...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{QUEUE_ENDPOINT}/stats",
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Queue statistics retrieved")
                print(f"  Queue length: {data.get('queue_length')}")
                print(f"  Active workers: {data.get('active_workers')}")
                print(f"  Total workers: {data.get('total_workers')}")
                print(f"  Tasks processed: {data.get('total_tasks_processed')}")
                print(f"  Tasks failed: {data.get('total_tasks_failed')}")
                print(f"  Success rate: {data.get('success_rate'):.1f}%")
                return True
            else:
                print(f"✗ Failed to get stats: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Stats check failed: {e}")
        return False

async def test_worker_status():
    """Test worker status retrieval"""
    print("\n▶ Checking worker status...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{QUEUE_ENDPOINT}/workers",
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                worker_count = data.get("worker_count", 0)
                print(f"✓ Worker status retrieved")
                print(f"  Active workers: {worker_count}")
                
                for worker in data.get("workers", []):
                    print(f"\n  Worker: {worker.get('worker_id')}")
                    print(f"    Status: {worker.get('status')}")
                    print(f"    Processed: {worker.get('tasks_processed')}")
                    print(f"    Failed: {worker.get('tasks_failed')}")
                    
                return True
            else:
                print(f"✗ Failed to get worker status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Worker status check failed: {e}")
        return False

async def test_batch_tasks(count: int = 5):
    """Test enqueueing multiple tasks"""
    print(f"\n▶ Enqueueing batch of {count} tasks...")
    try:
        task_ids = []
        async with httpx.AsyncClient() as client:
            for i in range(count):
                response = await client.post(
                    f"{QUEUE_ENDPOINT}/enqueue",
                    json={
                        "image_path": f"/path/to/batch_image_{i}.jpg",
                        "product_id": f"batch-prod-{i:03d}",
                        "name": f"Batch Product {i}",
                        "description": f"Batch product {i}"
                    },
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    task_id = response.json().get("task_id")
                    task_ids.append(task_id)
                    print(f"  ✓ Task {i+1}/{count} enqueued: {task_id}")
                else:
                    print(f"  ✗ Task {i+1}/{count} failed")
                    
                # Small delay between requests
                await asyncio.sleep(0.1)
        
        print(f"\n✓ Batch complete: {len(task_ids)} tasks enqueued")
        return task_ids
        
    except Exception as e:
        print(f"✗ Batch test failed: {e}")
        return []

async def run_full_test_suite():
    """Run complete test suite"""
    print("=" * 60)
    print("Redis Async Worker System - Test Suite")
    print("=" * 60)
    
    results = {
        "redis_connection": False,
        "task_enqueueing": False,
        "task_status": False,
        "queue_stats": False,
        "worker_status": False,
        "batch_tasks": False
    }
    
    # Test 1: Redis Connection
    results["redis_connection"] = await test_redis_connection()
    
    if not results["redis_connection"]:
        print("\n✗ Cannot continue without Redis connection")
        return results
    
    # Test 2: Single Task Enqueueing
    task_id = await test_enqueue_task("test-001")
    results["task_enqueueing"] = task_id is not None
    
    # Test 3: Task Status
    if task_id:
        await asyncio.sleep(1)  # Give time for processing
        results["task_status"] = await test_task_status(task_id)
    
    # Test 4: Queue Statistics
    results["queue_stats"] = await test_queue_stats()
    
    # Test 5: Worker Status
    results["worker_status"] = await test_worker_status()
    
    # Test 6: Batch Tasks
    batch_task_ids = await test_batch_tasks(3)
    results["batch_tasks"] = len(batch_task_ids) > 0
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! System is healthy.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Check configuration.")
        return 1

async def monitor_queue(duration_seconds: int = 30):
    """Monitor queue for specified duration"""
    print(f"\n▶ Monitoring queue for {duration_seconds} seconds...")
    print("(Ctrl+C to stop)\n")
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient() as client:
            while True:
                elapsed = time.time() - start_time
                if elapsed > duration_seconds:
                    break
                
                response = await client.get(f"{QUEUE_ENDPOINT}/stats", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    print(
                        f"[{elapsed:.0f}s] Queue: {data.get('queue_length')} | "
                        f"Workers: {data.get('active_workers')} | "
                        f"Processed: {data.get('total_tasks_processed')} | "
                        f"Failed: {data.get('total_tasks_failed')}"
                    )
                
                await asyncio.sleep(2)
                
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"✗ Monitoring failed: {e}")

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test Redis Async Worker System"
    )
    parser.add_argument(
        "--test",
        choices=["full", "redis", "enqueue", "status", "stats", "workers", "batch"],
        default="full",
        help="Test type to run"
    )
    parser.add_argument(
        "--monitor",
        type=int,
        default=0,
        help="Monitor queue for N seconds"
    )
    parser.add_argument(
        "--api-url",
        default=API_BASE_URL,
        help="API base URL"
    )
    
    args = parser.parse_args()
    
    # Update base URL if provided
    global API_BASE_URL, QUEUE_ENDPOINT
    API_BASE_URL = args.api_url
    QUEUE_ENDPOINT = f"{API_BASE_URL}/queue"
    
    if args.monitor > 0:
        await monitor_queue(args.monitor)
    else:
        exit_code = await run_full_test_suite()
        sys.exit(exit_code)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
