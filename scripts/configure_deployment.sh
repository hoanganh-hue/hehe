#!/bin/bash

# ZaloPay Merchant Platform - Deployment Configuration Script
# This script sets up the environment for deployment to 221.120.163.129

set -e  # Exit on error

echo "========================================"
echo "ZaloPay Merchant Platform Deployment"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Domain and server configuration
DOMAIN="zalopaymerchan.com"
SERVER_IP="221.120.163.129"

echo -e "${GREEN}Domain Configuration:${NC}"
echo "  Domain: ${DOMAIN}"
echo "  Server IP: ${SERVER_IP}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from template...${NC}"
    
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}Created .env from .env.example${NC}"
    else
        echo -e "${RED}Error: .env.example not found. Cannot create .env file.${NC}"
        exit 1
    fi
fi

# Update domain in .env if needed
echo -e "${YELLOW}Checking domain configuration in .env...${NC}"
if ! grep -q "DOMAIN=${DOMAIN}" .env; then
    echo -e "${YELLOW}Updating DOMAIN in .env...${NC}"
    sed -i "s/^DOMAIN=.*/DOMAIN=${DOMAIN}/" .env
    echo -e "${GREEN}Updated DOMAIN to ${DOMAIN}${NC}"
fi

# Verify DNS configuration
echo ""
echo -e "${GREEN}Verifying DNS configuration...${NC}"
DNS_IP=$(dig +short ${DOMAIN} 2>/dev/null || echo "")

if [ -z "$DNS_IP" ]; then
    echo -e "${YELLOW}Warning: Could not resolve ${DOMAIN}${NC}"
    echo "  Please ensure DNS A record is configured:"
    echo "  ${DOMAIN} → ${SERVER_IP}"
else
    echo "  ${DOMAIN} resolves to: ${DNS_IP}"
    if [ "$DNS_IP" == "$SERVER_IP" ]; then
        echo -e "${GREEN}  ✓ DNS correctly configured${NC}"
    else
        echo -e "${YELLOW}  ⚠ DNS points to different IP${NC}"
        echo "  Expected: ${SERVER_IP}"
        echo "  Actual: ${DNS_IP}"
    fi
fi

echo ""
echo -e "${GREEN}Routing Architecture:${NC}"
echo "  Root (/)            → Router page (auto-detection)"
echo "  /merchant/          → Customer interface"
echo "  /admin/             → Management dashboard"
echo "  /api/               → Backend API"
echo "  /beef/              → BeEF Framework"
echo ""

# Check required files
echo -e "${GREEN}Checking required files...${NC}"
REQUIRED_FILES=(
    "frontend/index.html"
    "frontend/merchant/index.html"
    "frontend/admin/index.html"
    "nginx/conf.d/default.conf"
    "nginx/conf.d/production.conf"
    "frontend/conf.d/default.conf"
    "docker-compose.yml"
)

MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}  ✗ Missing: $file${NC}"
        MISSING_FILES=$((MISSING_FILES + 1))
    else
        echo -e "${GREEN}  ✓ Found: $file${NC}"
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo -e "${RED}Error: $MISSING_FILES required file(s) missing${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}  ✓ Docker and Docker Compose are installed${NC}"

echo ""
echo -e "${GREEN}Configuration Summary:${NC}"
echo "  Domain: ${DOMAIN}"
echo "  Server IP: ${SERVER_IP}"
echo "  Router page: /frontend/index.html"
echo "  Nginx configs: Updated with IP and routing logic"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Ensure DNS A record points ${DOMAIN} to ${SERVER_IP}"
echo "  2. Configure .env with required secrets and credentials"
echo "  3. Run: docker compose build"
echo "  4. Run: docker compose up -d"
echo "  5. Test routing:"
echo "     - http://${DOMAIN}/ → Router page"
echo "     - http://${DOMAIN}/merchant/ → Merchant interface"
echo "     - http://${DOMAIN}/admin/ → Admin interface"
echo "     - http://${DOMAIN}/api/health → Backend health"
echo ""

echo -e "${GREEN}Configuration complete!${NC}"
