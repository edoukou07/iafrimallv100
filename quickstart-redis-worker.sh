#!/bin/bash
# Quick start script for Redis Async Worker System

set -e

echo "================================"
echo "Redis Async Worker - Quick Start"
echo "================================"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "✗ Docker is not installed"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "✗ Docker Compose is not installed"
    exit 1
fi

echo "✓ Docker and Docker Compose found"
echo ""

# Stop existing containers
echo "▶ Cleaning up existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true
echo ""

# Build images
echo "▶ Building Docker images..."
docker-compose build --no-cache
echo ""

# Start services
echo "▶ Starting services..."
docker-compose up -d
echo ""

# Wait for services to be ready
echo "▶ Waiting for services to be ready..."
sleep 5

# Check if services are running
echo "▶ Checking services..."
docker-compose ps
echo ""

# Test Redis connection
echo "▶ Testing Redis connection..."
if docker exec image-search-redis redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis is ready"
else
    echo "✗ Redis connection failed"
    exit 1
fi

# Test API
echo "▶ Testing API..."
for i in {1..10}; do
    if curl -s http://localhost:8000/queue/stats > /dev/null 2>&1; then
        echo "✓ API is ready"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "✗ API not responding after 10 attempts"
        exit 1
    fi
    sleep 1
done

echo ""
echo "================================"
echo "✓ System started successfully!"
echo "================================"
echo ""
echo "Available endpoints:"
echo "  POST   http://localhost:8000/queue/enqueue    - Enqueue a task"
echo "  GET    http://localhost:8000/queue/status/:id - Get task status"
echo "  GET    http://localhost:8000/queue/stats      - Get queue stats"
echo "  GET    http://localhost:8000/queue/workers    - List workers"
echo ""
echo "Run tests:"
echo "  python test_async_worker.py --test full"
echo "  python test_async_worker.py --monitor 60"
echo ""
echo "View logs:"
echo "  docker-compose logs -f api"
echo "  docker-compose logs -f worker1"
echo "  docker-compose logs -f redis"
echo ""
echo "Stop system:"
echo "  docker-compose down"
echo ""
