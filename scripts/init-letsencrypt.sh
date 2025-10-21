#!/bin/bash

# ZaloPay Merchant Phishing Platform - Let's Encrypt SSL Certificate Initialization
# Automated SSL certificate acquisition and renewal setup

set -e

# Configuration
DOMAIN=${DOMAIN:-"zalopaymerchan.com"}
EMAIL=${SSL_EMAIL:-"admin@zalopaymerchan.com"}
NGINX_CONTAINER=${NGINX_CONTAINER:-"nginx"}
CERTBOT_CONTAINER=${CERTBOT_CONTAINER:-"certbot"}
WEBROOT_PATH="/var/www/certbot"

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
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    log "Docker is running"
}

# Check if domain is reachable
check_domain() {
    log "Checking if domain $DOMAIN is reachable..."
    
    if ! nslookup $DOMAIN > /dev/null 2>&1; then
        error "Domain $DOMAIN is not resolvable. Please check your DNS settings."
        exit 1
    fi
    
    # Check if domain points to this server
    DOMAIN_IP=$(nslookup $DOMAIN | grep -A 1 "Name:" | tail -1 | awk '{print $2}')
    SERVER_IP=$(curl -s ifconfig.me)
    
    if [[ "$DOMAIN_IP" != "$SERVER_IP" ]]; then
        warning "Domain $DOMAIN ($DOMAIN_IP) does not point to this server ($SERVER_IP)"
        warning "SSL certificate acquisition may fail. Please update your DNS settings."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        success "Domain $DOMAIN correctly points to this server"
    fi
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    mkdir -p certbot/conf
    mkdir -p certbot/www
    mkdir -p nginx/ssl
    
    # Set proper permissions
    chmod 755 certbot/conf
    chmod 755 certbot/www
    chmod 755 nginx/ssl
    
    success "Directories created successfully"
}

# Check if certificates already exist
check_existing_certificates() {
    log "Checking for existing SSL certificates..."
    
    if [[ -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]] && [[ -f "certbot/conf/live/$DOMAIN/privkey.pem" ]]; then
        success "SSL certificates already exist for $DOMAIN"
        
        # Check certificate expiry
        EXPIRY_DATE=$(openssl x509 -enddate -noout -in "certbot/conf/live/$DOMAIN/fullchain.pem" | cut -d= -f2)
        EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
        CURRENT_EPOCH=$(date +%s)
        DAYS_UNTIL_EXPIRY=$(( (EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))
        
        if [[ $DAYS_UNTIL_EXPIRY -gt 30 ]]; then
            success "Certificate is valid for $DAYS_UNTIL_EXPIRY more days"
            return 0
        else
            warning "Certificate expires in $DAYS_UNTIL_EXPIRY days. Renewal recommended."
        fi
    fi
    
    return 1
}

# Start temporary nginx for certificate validation
start_temp_nginx() {
    log "Starting temporary nginx for certificate validation..."
    
    # Create temporary nginx config for certificate validation
    cat > nginx/temp-ssl.conf << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 200 'SSL certificate validation in progress...';
        add_header Content-Type text/plain;
    }
}
EOF

    # Start nginx container with temporary config
    docker run -d \
        --name temp-nginx-ssl \
        -p 80:80 \
        -v "$(pwd)/nginx/temp-ssl.conf:/etc/nginx/conf.d/default.conf" \
        -v "$(pwd)/certbot/www:/var/www/certbot" \
        nginx:alpine
    
    # Wait for nginx to start
    sleep 5
    
    # Test if nginx is responding
    if curl -f http://localhost/.well-known/acme-challenge/test > /dev/null 2>&1; then
        success "Temporary nginx is running"
    else
        error "Failed to start temporary nginx"
        return 1
    fi
}

# Stop temporary nginx
stop_temp_nginx() {
    log "Stopping temporary nginx..."
    
    if docker ps -q -f name=temp-nginx-ssl | grep -q .; then
        docker stop temp-nginx-ssl
        docker rm temp-nginx-ssl
        success "Temporary nginx stopped"
    fi
    
    # Clean up temporary config
    rm -f nginx/temp-ssl.conf
}

# Acquire SSL certificates
acquire_certificates() {
    log "Acquiring SSL certificates for $DOMAIN..."
    
    # Run certbot to acquire certificates
    docker run --rm \
        -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
        -v "$(pwd)/certbot/www:/var/www/certbot" \
        certbot/certbot \
        certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        -d $DOMAIN \
        -d www.$DOMAIN
    
    if [[ $? -eq 0 ]]; then
        success "SSL certificates acquired successfully"
        return 0
    else
        error "Failed to acquire SSL certificates"
        return 1
    fi
}

# Verify certificates
verify_certificates() {
    log "Verifying SSL certificates..."
    
    CERT_PATH="certbot/conf/live/$DOMAIN"
    
    if [[ ! -f "$CERT_PATH/fullchain.pem" ]] || [[ ! -f "$CERT_PATH/privkey.pem" ]]; then
        error "Certificate files not found"
        return 1
    fi
    
    # Verify certificate validity
    if openssl x509 -in "$CERT_PATH/fullchain.pem" -text -noout > /dev/null 2>&1; then
        success "SSL certificates are valid"
        
        # Display certificate information
        log "Certificate information:"
        openssl x509 -in "$CERT_PATH/fullchain.pem" -text -noout | grep -E "(Subject:|Issuer:|Not Before:|Not After:)"
        
        return 0
    else
        error "SSL certificates are invalid"
        return 1
    fi
}

# Set up certificate renewal
setup_renewal() {
    log "Setting up automatic certificate renewal..."
    
    # Create renewal script
    cat > scripts/renew-ssl.sh << 'EOF'
#!/bin/bash

# SSL Certificate Renewal Script
set -e

DOMAIN=${DOMAIN:-"zalopaymerchan.com"}
NGINX_CONTAINER=${NGINX_CONTAINER:-"nginx"}

echo "Renewing SSL certificates for $DOMAIN..."

# Renew certificates
docker run --rm \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    certbot/certbot \
    renew \
    --webroot \
    --webroot-path=/var/www/certbot

# Reload nginx if certificates were renewed
if docker exec $NGINX_CONTAINER nginx -t; then
    docker exec $NGINX_CONTAINER nginx -s reload
    echo "Nginx reloaded successfully"
else
    echo "Nginx configuration test failed"
    exit 1
fi

echo "SSL certificate renewal completed"
EOF

    chmod +x scripts/renew-ssl.sh
    
    # Add to crontab for automatic renewal (every Monday at 2 AM)
    (crontab -l 2>/dev/null; echo "0 2 * * 1 $(pwd)/scripts/renew-ssl.sh >> $(pwd)/logs/ssl-renewal.log 2>&1") | crontab -
    
    success "Automatic certificate renewal configured"
}

# Create nginx SSL configuration
create_nginx_ssl_config() {
    log "Creating nginx SSL configuration..."
    
    # Backup existing config if it exists
    if [[ -f "nginx/conf.d/default.conf" ]]; then
        cp nginx/conf.d/default.conf nginx/conf.d/default.conf.backup
        log "Backed up existing nginx configuration"
    fi
    
    # The SSL configuration is already created in nginx/conf.d/default.conf
    # Just verify it exists and has the correct certificate paths
    if [[ -f "nginx/conf.d/default.conf" ]]; then
        success "Nginx SSL configuration is ready"
    else
        error "Nginx SSL configuration not found"
        return 1
    fi
}

# Test SSL configuration
test_ssl_config() {
    log "Testing SSL configuration..."
    
    # Test nginx configuration
    if docker run --rm \
        -v "$(pwd)/nginx/conf.d:/etc/nginx/conf.d" \
        -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
        nginx:alpine \
        nginx -t; then
        success "Nginx SSL configuration is valid"
    else
        error "Nginx SSL configuration is invalid"
        return 1
    fi
}

# Main execution
main() {
    log "Starting SSL certificate initialization for $DOMAIN"
    
    # Pre-flight checks
    check_root
    check_docker
    check_domain
    
    # Create necessary directories
    create_directories
    
    # Check if certificates already exist
    if check_existing_certificates; then
        log "Certificates already exist and are valid"
        setup_renewal
        exit 0
    fi
    
    # Start temporary nginx for validation
    if ! start_temp_nginx; then
        error "Failed to start temporary nginx"
        exit 1
    fi
    
    # Acquire certificates
    if acquire_certificates; then
        success "SSL certificates acquired successfully"
    else
        error "Failed to acquire SSL certificates"
        stop_temp_nginx
        exit 1
    fi
    
    # Stop temporary nginx
    stop_temp_nginx
    
    # Verify certificates
    if ! verify_certificates; then
        error "Certificate verification failed"
        exit 1
    fi
    
    # Create nginx SSL configuration
    if ! create_nginx_ssl_config; then
        error "Failed to create nginx SSL configuration"
        exit 1
    fi
    
    # Test SSL configuration
    if ! test_ssl_config; then
        error "SSL configuration test failed"
        exit 1
    fi
    
    # Set up automatic renewal
    setup_renewal
    
    success "SSL certificate initialization completed successfully!"
    log "You can now start your application with SSL enabled"
    log "Certificates will be automatically renewed every Monday at 2 AM"
}

# Run main function
main "$@"