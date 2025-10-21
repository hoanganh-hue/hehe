"""
Frontend Router
Static file serving and template rendering for merchant and admin interfaces
"""

import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

router = APIRouter()

# Setup templates
templates = Jinja2Templates(directory="frontend/templates")

# Static file directories
MERCHANT_STATIC_DIR = Path("frontend/merchant")
ADMIN_STATIC_DIR = Path("frontend/admin")

@router.get("/", response_class=HTMLResponse)
async def root():
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

# Merchant frontend routes
@router.get("/merchant/", response_class=HTMLResponse)
async def merchant_home():
    """Merchant homepage"""
    try:
        index_file = MERCHANT_STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Merchant homepage not found"
            )
    except Exception as e:
        logger.error(f"Merchant homepage error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/merchant/{file_name}", response_class=HTMLResponse)
async def merchant_static_files(file_name: str):
    """Serve merchant static files"""
    try:
        file_path = MERCHANT_STATIC_DIR / file_name
        
        # Security check - prevent directory traversal
        if not file_path.resolve().is_relative_to(MERCHANT_STATIC_DIR.resolve()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Merchant static file error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Admin frontend routes
@router.get("/admin/", response_class=HTMLResponse)
async def admin_home():
    """Admin homepage"""
    try:
        index_file = ADMIN_STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin homepage not found"
            )
    except Exception as e:
        logger.error(f"Admin homepage error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/admin/{file_name}", response_class=HTMLResponse)
async def admin_static_files(file_name: str):
    """Serve admin static files"""
    try:
        file_path = ADMIN_STATIC_DIR / file_name
        
        # Security check - prevent directory traversal
        if not file_path.resolve().is_relative_to(ADMIN_STATIC_DIR.resolve()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin static file error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# API documentation routes
@router.get("/docs", response_class=HTMLResponse)
async def api_docs():
    """API documentation"""
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>API Documentation</title>
            <meta http-equiv="refresh" content="0; url=/api/docs">
        </head>
        <body>
            <p>Redirecting to API documentation...</p>
        </body>
        </html>
        """
    )

# Health check for frontend
@router.get("/health/frontend")
async def frontend_health_check():
    """Frontend health check"""
    try:
        merchant_exists = (MERCHANT_STATIC_DIR / "index.html").exists()
        admin_exists = (ADMIN_STATIC_DIR / "index.html").exists()
        
        return {
            "status": "healthy" if merchant_exists and admin_exists else "degraded",
            "merchant_frontend": "available" if merchant_exists else "missing",
            "admin_frontend": "available" if admin_exists else "missing",
            "timestamp": "2025-01-27T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Frontend health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-01-27T00:00:00Z"
        }

# Static assets routes
@router.get("/static/{file_path:path}")
async def static_assets(file_path: str):
    """Serve static assets"""
    try:
        static_file = Path("frontend/static") / file_path
        
        # Security check
        if not static_file.resolve().is_relative_to(Path("frontend/static").resolve()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if static_file.exists() and static_file.is_file():
            return FileResponse(static_file)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Static assets error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/assets/{file_path:path}")
async def assets(file_path: str):
    """Serve assets"""
    try:
        asset_file = Path("frontend/assets") / file_path
        
        # Security check
        if not asset_file.resolve().is_relative_to(Path("frontend/assets").resolve()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if asset_file.exists() and asset_file.is_file():
            return FileResponse(asset_file)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assets error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
