@echo off
REM Quick start script for Redis Async Worker System (Windows)

setlocal enabledelayedexpansion

echo.
echo ================================
echo Redis Async Worker - Quick Start
echo ================================
echo.

REM Check Docker
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X Docker is not installed
    exit /b 1
)

REM Check Docker Compose
where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X Docker Compose is not installed
    exit /b 1
)

echo + Docker and Docker Compose found
echo.

REM Stop existing containers
echo + Cleaning up existing containers...
docker-compose down --remove-orphans 2>nul
if %ERRORLEVEL% EQU 0 (
    echo.
) else (
    echo   (No existing containers to stop)
    echo.
)

REM Build images
echo + Building Docker images...
docker-compose build --no-cache
if %ERRORLEVEL% NEQ 0 (
    echo X Build failed
    exit /b 1
)
echo.

REM Start services
echo + Starting services...
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo X Failed to start services
    exit /b 1
)
echo.

REM Wait for services to be ready
echo + Waiting for services to be ready...
timeout /t 5 /nobreak
echo.

REM Check if services are running
echo + Checking services...
docker-compose ps
echo.

REM Test Redis connection
echo + Testing Redis connection...
docker exec image-search-redis redis-cli ping >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo + Redis is ready
) else (
    echo X Redis connection failed
    exit /b 1
)

REM Test API
echo + Testing API...
for /L %%i in (1,1,10) do (
    curl -s http://localhost:8000/queue/stats >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo + API is ready
        goto :api_ready
    )
    if %%i LSS 10 (
        timeout /t 1 /nobreak >nul
    )
)
echo X API not responding after 10 attempts
exit /b 1

:api_ready
echo.
echo ================================
echo + System started successfully!
echo ================================
echo.
echo Available endpoints:
echo   POST   http://localhost:8000/queue/enqueue    - Enqueue a task
echo   GET    http://localhost:8000/queue/status/:id - Get task status
echo   GET    http://localhost:8000/queue/stats      - Get queue stats
echo   GET    http://localhost:8000/queue/workers    - List workers
echo.
echo Run tests:
echo   python test_async_worker.py --test full
echo   python test_async_worker.py --monitor 60
echo.
echo View logs:
echo   docker-compose logs -f api
echo   docker-compose logs -f worker1
echo   docker-compose logs -f redis
echo.
echo Stop system:
echo   docker-compose down
echo.
