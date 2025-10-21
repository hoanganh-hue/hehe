"""
CORS Middleware Configuration
Cross-Origin Resource Sharing setup for zalopaymerchan.com
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

logger = logging.getLogger(__name__)

def setup_cors(app: FastAPI):
    """Setup CORS middleware"""
    try:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=settings.CORS_METHODS,
            allow_headers=settings.CORS_HEADERS,
            expose_headers=["X-Total-Count", "X-Page-Count"],
            max_age=3600,  # 1 hour
        )
        
        logger.info(f"CORS middleware configured for origins: {settings.CORS_ORIGINS}")
        
    except Exception as e:
        logger.error(f"Failed to setup CORS middleware: {e}")
        raise
