#!/bin/bash

# Production Deployment Script
# This script handles production deployments with strict validation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Configuration
ENVIRONMENT="production"
COMPOSE_FILE="docker-compose.yml"
LOG_FILE="./logs/deployment_$(date +%Y%m%d_%H%M%S).log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."

    # Check if all secrets exist
    local required_secrets=(
        "secrets/mongodb_root_username.txt"
        "secrets/mongodb_root_password.txt"
        "secrets/redis_password.txt"
        "secrets/jwt_secret.txt"
        "secrets/encryption_key.txt"
        "secrets/beef_user.txt"
        "secrets/beef_password.txt"
    )

    for secret in "${required_secrets[@]}"; do
        if [ ! -f "$secret" ]; then
            error "Required secret file $secret not found"
            exit 1
        fi
    done

    # Check if domain is configured
    if [ -z "${DOMAIN:-}" ]; then
        error "DOMAIN environment variable is not set"
        exit 1
    fi

    # Validate docker-compose file
    if ! docker-compose -f "$COMPOSE_FILE" config --quiet; then
        error "Docker Compose configuration is invalid"
        exit 1
    fi

    success "Pre-deployment checks passed"
}

# Health check function
health_check() {
    local max_attempts=30
    local attempt=1

    log "Performing health checks..."

    while [ $attempt -le $max_attempts ]; do
        log "Health check attempt $attempt/$max_attempts"

        local all_healthy=true

        # Check nginx
        if ! curl -f -s "http://localhost/health" &> /dev/null; then
            all_healthy=false
        fi

        # Check backend
        if ! curl -f -s "http://localhost:8000/health" &> /dev/null; then
            all_healthy=false
        fi

        # Check beef
        if ! curl -f -s "http://localhost:3000/api/hooks" &> /dev/null; then
            all_healthy=false
        fi

        if $all_healthy; then
            success "All services are healthy"
            return 0
        fi

        sleep 10
        ((attempt++))
    done

    error "Health checks failed after $max_attempts attempts"
    return 1
}

# Main deployment process
main() {
    log "🚀 Starting Production Deployment"
    echo "=================================================="

    # Create logs directory
    mkdir -p logs

    # Run pre-deployment checks
    pre_deployment_checks

    # Create backup
    log "Creating pre-deployment backup..."
    ./deploy.sh --backup

    # Deploy with strict error handling
    log "Deploying services..."
    docker-compose -f "$COMPOSE_FILE" down --timeout 60

    # Build and start services
    docker-compose -f "$COMPOSE_FILE" build --parallel
    docker-compose -f "$COMPOSE_FILE" up -d --wait --timeout 300

    # Wait for services to stabilize
    sleep 30

    # Perform health checks
    if ! health_check; then
        error "Deployment failed health checks"
        log "Rolling back to previous version..."
        ./scripts/rollback.sh
        exit 1
    fi

    # Setup SSL if needed
    if [ ! -f "./nginx/ssl/live/$DOMAIN/fullchain.pem" ]; then
        log "Setting up SSL certificates..."
        docker-compose run --rm certbot
    fi

    # Final verification
    log "Running final verification..."
    docker-compose ps
    docker-compose logs --tail=50

    echo "=================================================="
    success "🎉 Production deployment completed successfully!"
    echo ""
    echo "🌐 Website: https://$DOMAIN"
    echo "📊 Status: $(docker-compose ps --format 'table {{.Service}}\t{{.Status}}\t{{.Ports}}')"
    echo "📝 Logs: $LOG_FILE"
}

# Run main function
main "$@"