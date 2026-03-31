import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.api.routes import router
from app.api.indexation_routes import router as indexation_router
from app.dependencies import initialize_services
from app.utils.logger import setup_logger
from app.security.headers import SecurityHeadersMiddleware
from app.security.jwt_handler import initialize_jwt_handler

# Setup logger
logger = setup_logger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info(f"Starting up application ({settings.environment})...")
    try:
        # Initialize security
        initialize_jwt_handler(settings.secret_key)
        logger.info("✓ Security initialized")
        
        # Initialize services
        initialize_services()
        logger.info("✓ Services initialized")
        
        # Validate production settings
        if settings.environment == "production":
            logger.warning("⚠️  Running in PRODUCTION mode")
            logger.info(f"  - DEBUG: {settings.debug}")
            logger.info(f"  - CORS Origins: {settings.cors_origins}")
            logger.info(f"  - Rate Limiting: {settings.rate_limit_enabled}")
        
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# ===== Security Middlewares (Order matters!) =====

# 1. Trusted Host - prevent Host Header attacks
# app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.cors_origins)

# 2. CORS Middleware - restrict origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# 3. Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 4. GZIP Compression (reduces response size)
app.add_middleware(GZIPMiddleware, minimum_size=1000)

# 5. Custom middleware for request size limiting
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Middleware to limit request body size"""
    if request.method in ["POST", "PUT", "PATCH"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_body_size:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request body too large (max {settings.max_body_size} bytes)"}
            )
    return await call_next(request)

# Mount static files (only if directory exists and in debug mode)
if settings.debug:
    static_dir = Path(__file__).parent.parent / "static"
    try:
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
            logger.info(f"Mounted static files from {static_dir}")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")
else:
    logger.info("Static files disabled in production")

# Include routers
app.include_router(router)
app.include_router(indexation_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "title": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "docs": "/docs" if settings.debug else None,
        "environment": settings.environment,
    }

@app.get("/test")
async def test_page():
    """Serve the test panel (debug only)"""
    if not settings.debug:
        return JSONResponse(
            status_code=404,
            content={"detail": "Test page not available in production"}
        )
    
    # Try multiple locations
    test_files = [
        Path(__file__).parent.parent / "static" / "test_panel.html",
        Path(__file__).parent.parent / "static" / "test.html",
        Path(__file__).parent / "static" / "test_panel.html",
    ]
    
    for test_file in test_files:
        if test_file.exists():
            logger.info(f"Serving test panel from: {test_file}")
            return FileResponse(str(test_file), media_type="text/html")
    
    return {
        "error": "Test page not found",
        "message": f"Place test_panel.html in the static directory. Checked: {[str(f) for f in test_files]}"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler - never expose internal errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # In production, don't expose error details
    if settings.environment == "production":
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    else:
        # In development, include error details for debugging
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

