# Backend Frontend Integration Guide

## Overview

The backend has been integrated to serve the merchant and admin frontend interfaces directly. This means you can now access the application through the backend port (8000) without needing to run the frontend container separately.

## Changes Made

### 1. Backend Configuration (`backend/config.py`)
- Created a centralized configuration management system using `pydantic-settings`
- Manages environment variables and application settings
- Compatible with Pydantic v2

### 2. Backend Main Application (`backend/main.py`)
Added functionality to serve frontend files:
- **Root endpoint (`/`)**: Serves the merchant interface homepage (`frontend/merchant/index.html`)
- **Merchant routes (`/merchant/*`)**: Serves all merchant interface pages
- **Admin routes (`/admin/*`)**: Serves all admin interface pages
- **Static assets (`/css/*`, `/js/*`)**: Serves CSS and JavaScript files

### 3. Docker Configuration
- **Dockerfile**: Updated to copy frontend files into the backend container
- **docker-compose.yml**: Exposed port 8000 for direct backend access

## Access Points

When the backend is running, you can access:

1. **Merchant Interface**: `http://localhost:8000/` or `http://localhost:8000/merchant/`
2. **Admin Interface**: `http://localhost:8000/admin/`
3. **Health Check**: `http://localhost:8000/health`
4. **API Endpoints**: `http://localhost:8000/api/*`

## How It Works

### File Serving Logic

```python
# Root endpoint serves merchant homepage
@app.get("/")
async def root():
    return FileResponse("frontend/merchant/index.html")

# Merchant pages
@app.get("/merchant/{file_path:path}")
async def serve_merchant_files(file_path: str):
    # Serves files from frontend/merchant/ directory
    # Includes security checks to prevent directory traversal

# Admin pages
@app.get("/admin/{file_path:path}")
async def serve_admin_files(file_path: str):
    # Serves files from frontend/admin/ directory
    # Includes security checks to prevent directory traversal

# Static assets
app.mount("/css", StaticFiles(directory="frontend/css"))
app.mount("/js", StaticFiles(directory="frontend/js"))
```

### Security Features

1. **Path Traversal Prevention**: All file requests are validated to ensure they don't escape the allowed directories
2. **File Type Validation**: Only files within the frontend directories are served
3. **404 Handling**: Non-existent files return appropriate error responses

## Testing

### Quick Test Script

A test script is provided at `test_backend_frontend_integration.py` to demonstrate the integration:

```bash
python3 test_backend_frontend_integration.py
```

This script:
- Creates a minimal FastAPI server
- Mounts frontend directories
- Serves merchant and admin interfaces
- Runs on port 8000

### Manual Testing

1. Start the backend (with symlink):
   ```bash
   cd backend
   ln -sf ../frontend frontend
   python3 main.py
   ```

2. Access the interfaces:
   - Open browser to `http://localhost:8000/`
   - Check `http://localhost:8000/admin/`
   - Verify CSS and JS load correctly

### Docker Testing

1. Build the backend container:
   ```bash
   docker build -t zalopay-backend -f backend/Dockerfile .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 zalopay-backend
   ```

3. Access `http://localhost:8000/`

## Deployment

### Using Docker Compose

The `docker-compose.yml` has been updated to:
- Use parent directory as build context
- Copy frontend files into backend container
- Expose port 8000 to the host

Start the services:
```bash
docker-compose up -d backend
```

### Production Considerations

1. **Nginx Reverse Proxy**: In production, you may still want to use nginx as a reverse proxy for:
   - SSL termination
   - Load balancing
   - Static file caching
   - Rate limiting

2. **Environment Variables**: Ensure all required environment variables are set in `.env` file

3. **File Permissions**: Frontend files must be readable by the backend container user

## Architecture

### Before Integration
```
Internet → Nginx LB → Backend (API only)
                    → Frontend Nginx (Static files)
```

### After Integration
```
Internet → Backend (API + Frontend files)
         (Optional: Nginx LB for SSL/caching)
```

## Benefits

1. **Simplified Deployment**: One container serves everything
2. **Easier Development**: Single port to access all features
3. **Reduced Complexity**: No need for separate frontend container
4. **Better Integration**: Backend and frontend are tightly coupled
5. **Flexible Architecture**: Can still use nginx for production optimizations

## Troubleshooting

### Frontend Files Not Found

**Problem**: 404 errors when accessing frontend pages

**Solution**: 
1. Check that the symlink exists: `ls -la backend/frontend`
2. Or ensure files were copied in Docker: `docker exec backend ls /app/frontend`

### CSS/JS Not Loading

**Problem**: Pages load but styling is broken

**Solution**:
1. Verify static file mounts: Check logs for "Frontend static files mounted successfully"
2. Check file paths in HTML: Ensure they reference `/css/` and `/js/`
3. Test direct access: `curl http://localhost:8000/css/merchant.css`

### Port Already in Use

**Problem**: Cannot start server on port 8000

**Solution**:
1. Check what's using the port: `lsof -i :8000`
2. Stop other services or change port in configuration

## Future Enhancements

1. **Template Engine**: Use Jinja2 for dynamic HTML generation
2. **Asset Bundling**: Minify and bundle CSS/JS files
3. **Caching**: Add HTTP caching headers for static files
4. **CDN Integration**: Serve static assets from CDN
5. **Service Worker**: Add offline support with service workers

## Related Files

- `backend/main.py` - Main application with frontend serving logic
- `backend/config.py` - Configuration management
- `backend/Dockerfile` - Container build instructions
- `docker-compose.yml` - Service orchestration
- `test_backend_frontend_integration.py` - Integration test script

## Support

For issues or questions about the integration, please check:
1. Application logs: `docker-compose logs backend`
2. Health endpoint: `http://localhost:8000/health`
3. This documentation
