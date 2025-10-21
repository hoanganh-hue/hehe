"""
Router aggregation and registration
"""

from fastapi import APIRouter

# Import all routers (admin temporarily disabled)
from . import auth, oauth, capture, frontend  # admin

# Create main router
main_router = APIRouter()

# Include all sub-routers
main_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
main_router.include_router(oauth.router, prefix="/oauth", tags=["OAuth"])
main_router.include_router(capture.router, prefix="/capture", tags=["Capture"])
# main_router.include_router(admin.router, prefix="/admin", tags=["Admin"])  # Temporarily disabled
main_router.include_router(frontend.router, tags=["Frontend"])

__all__ = ["main_router"]
