#!/usr/bin/env python3
"""
Standalone test script to demonstrate backend serving frontend files
This script creates a minimal FastAPI server that serves the merchant interface
without requiring database connections or complex dependencies.
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Add backend directory to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

app = FastAPI(title="ZaloPay Merchant - Integration Test")

# Mount static files
css_path = backend_path / "frontend" / "css"
js_path = backend_path / "frontend" / "js"
merchant_path = backend_path / "frontend" / "merchant"
admin_path = backend_path / "frontend" / "admin"

if css_path.exists():
    app.mount("/css", StaticFiles(directory=str(css_path)), name="css")
    print(f"✓ Mounted CSS directory: {css_path}")

if js_path.exists():
    app.mount("/js", StaticFiles(directory=str(js_path)), name="js")
    print(f"✓ Mounted JS directory: {js_path}")

@app.get("/")
async def root():
    """Root endpoint - serve merchant frontend directly"""
    merchant_index = merchant_path / "index.html"
    if merchant_index.exists():
        print(f"✓ Serving merchant index from: {merchant_index}")
        return FileResponse(merchant_index)
    else:
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error - Frontend Not Found</title>
            </head>
            <body>
                <h1>Frontend files not found</h1>
                <p>Expected location: {merchant_index}</p>
                <p>Current directory: {Path.cwd()}</p>
            </body>
            </html>
            """,
            status_code=404
        )

@app.get("/merchant/{file_path:path}")
async def serve_merchant_files(file_path: str):
    """Serve merchant static files"""
    if not file_path or file_path.endswith('/'):
        file_path = (file_path or "") + "index.html"
    
    merchant_file = merchant_path / file_path
    
    # Security check - prevent directory traversal
    try:
        merchant_file = merchant_file.resolve()
        base_path = merchant_path.resolve()
        if not str(merchant_file).startswith(str(base_path)):
            return HTMLResponse("Forbidden", status_code=403)
    except Exception:
        return HTMLResponse("Bad Request", status_code=400)
    
    if merchant_file.exists() and merchant_file.is_file():
        return FileResponse(merchant_file)
    return HTMLResponse("Not Found", status_code=404)

@app.get("/admin/{file_path:path}")
async def serve_admin_files(file_path: str):
    """Serve admin static files"""
    if not file_path or file_path.endswith('/'):
        file_path = (file_path or "") + "index.html"
    
    admin_file = admin_path / file_path
    
    # Security check - prevent directory traversal
    try:
        admin_file = admin_file.resolve()
        base_path = admin_path.resolve()
        if not str(admin_file).startswith(str(base_path)):
            return HTMLResponse("Forbidden", status_code=403)
    except Exception:
        return HTMLResponse("Bad Request", status_code=400)
    
    if admin_file.exists() and admin_file.is_file():
        return FileResponse(admin_file)
    return HTMLResponse("Not Found", status_code=404)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Backend is serving frontend files",
        "merchant_available": merchant_path.exists(),
        "admin_available": admin_path.exists()
    }

if __name__ == "__main__":
    print("\n" + "="*70)
    print("ZaloPay Merchant - Backend Frontend Integration Test")
    print("="*70)
    print(f"\nBackend path: {backend_path}")
    print(f"Merchant path: {merchant_path}")
    print(f"Admin path: {admin_path}")
    print(f"\nChecking paths:")
    print(f"  Merchant exists: {merchant_path.exists()}")
    print(f"  Admin exists: {admin_path.exists()}")
    print(f"  CSS exists: {css_path.exists()}")
    print(f"  JS exists: {js_path.exists()}")
    print("\n" + "="*70)
    print("Starting server on http://0.0.0.0:8000")
    print("="*70)
    print("\nAccess points:")
    print("  - Merchant Interface: http://localhost:8000/")
    print("  - Admin Interface:    http://localhost:8000/admin/")
    print("  - Health Check:       http://localhost:8000/health")
    print("\nPress CTRL+C to stop the server\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
