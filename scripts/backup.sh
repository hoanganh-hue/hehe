#!/bin/bash

# Backup Script for ZaloPay Phishing Platform
# This script creates backups of databases, configurations, and logs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="zalopay_phishing_backup_$DATE"
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

create_backup_directory() {
    log_info "Creating backup directory..."
    
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
    
    log_success "Backup directory created: $BACKUP_DIR/$BACKUP_NAME"
}

backup_mongodb() {
    log_info "Backing up MongoDB..."
    
    # Create MongoDB backup
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T mongodb mongodump \
        --db zalopay_phishing \
        --out /tmp/backup
    
    # Copy backup from container
    docker cp $(docker-compose -f $DOCKER_COMPOSE_FILE ps -q mongodb):/tmp/backup "$BACKUP_DIR/$BACKUP_NAME/mongodb"
    
    log_success "MongoDB backup completed"
}

backup_redis() {
    log_info "Backing up Redis..."
    
    # Create Redis backup
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T redis redis-cli BGSAVE
    
    # Wait for backup to complete
    sleep 5
    
    # Copy backup from container
    docker cp $(docker-compose -f $DOCKER_COMPOSE_FILE ps -q redis):/data/dump.rdb "$BACKUP_DIR/$BACKUP_NAME/redis/"
    
    log_success "Redis backup completed"
}

backup_influxdb() {
    log_info "Backing up InfluxDB..."
    
    # Create InfluxDB backup
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T influxdb influx backup /tmp/backup
    
    # Copy backup from container
    docker cp $(docker-compose -f $DOCKER_COMPOSE_FILE ps -q influxdb):/tmp/backup "$BACKUP_DIR/$BACKUP_NAME/influxdb"
    
    log_success "InfluxDB backup completed"
}

backup_configurations() {
    log_info "Backing up configurations..."
    
    # Backup environment file
    if [ -f ".env" ]; then
        cp .env "$BACKUP_DIR/$BACKUP_NAME/"
        log_success "Environment file backed up"
    fi
    
    # Backup docker-compose file
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        cp $DOCKER_COMPOSE_FILE "$BACKUP_DIR/$BACKUP_NAME/"
        log_success "Docker Compose file backed up"
    fi
    
    # Backup SSL certificates
    if [ -d "ssl" ]; then
        cp -r ssl "$BACKUP_DIR/$BACKUP_NAME/"
        log_success "SSL certificates backed up"
    fi
    
    # Backup Nginx configuration
    if [ -d "nginx" ]; then
        cp -r nginx "$BACKUP_DIR/$BACKUP_NAME/"
        log_success "Nginx configuration backed up"
    fi
    
    # Backup scripts
    if [ -d "scripts" ]; then
        cp -r scripts "$BACKUP_DIR/$BACKUP_NAME/"
        log_success "Scripts backed up"
    fi
}

backup_logs() {
    log_info "Backing up logs..."
    
    if [ -d "logs" ] && [ "$(ls -A logs)" ]; then
        cp -r logs "$BACKUP_DIR/$BACKUP_NAME/"
        log_success "Logs backed up"
    else
        log_warning "No logs found to backup"
    fi
}

backup_data() {
    log_info "Backing up data directories..."
    
    # Backup MongoDB data
    if [ -d "data/mongodb" ]; then
        cp -r data/mongodb "$BACKUP_DIR/$BACKUP_NAME/data/"
        log_success "MongoDB data backed up"
    fi
    
    # Backup Redis data
    if [ -d "data/redis" ]; then
        cp -r data/redis "$BACKUP_DIR/$BACKUP_NAME/data/"
        log_success "Redis data backed up"
    fi
    
    # Backup InfluxDB data
    if [ -d "data/influxdb" ]; then
        cp -r data/influxdb "$BACKUP_DIR/$BACKUP_NAME/data/"
        log_success "InfluxDB data backed up"
    fi
    
    # Backup BeEF data
    if [ -d "data/beef" ]; then
        cp -r data/beef "$BACKUP_DIR/$BACKUP_NAME/data/"
        log_success "BeEF data backed up"
    fi
}

create_backup_manifest() {
    log_info "Creating backup manifest..."
    
    manifest_file="$BACKUP_DIR/$BACKUP_NAME/manifest.txt"
    
    {
        echo "ZaloPay Phishing Platform Backup Manifest"
        echo "=========================================="
        echo "Backup Date: $(date)"
        echo "Backup Name: $BACKUP_NAME"
        echo "Backup Size: $(du -sh "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)"
        echo ""
        echo "Contents:"
        echo "========="
        find "$BACKUP_DIR/$BACKUP_NAME" -type f | sort
        echo ""
        echo "System Information:"
        echo "==================="
        echo "Hostname: $(hostname)"
        echo "OS: $(uname -a)"
        echo "Docker Version: $(docker --version)"
        echo "Docker Compose Version: $(docker-compose --version)"
        echo ""
        echo "Service Status:"
        echo "==============="
        docker-compose -f $DOCKER_COMPOSE_FILE ps
        echo ""
        echo "Disk Usage:"
        echo "==========="
        df -h
        echo ""
        echo "Memory Usage:"
        echo "============="
        free -h
        
    } > "$manifest_file"
    
    log_success "Backup manifest created: $manifest_file"
}

compress_backup() {
    log_info "Compressing backup..."

    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
    cd ..

    # Remove uncompressed directory
    rm -rf "$BACKUP_DIR/$BACKUP_NAME"

    log_success "Backup compressed: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
}

cleanup_old_backups() {
    log_info "Cleaning up old backups..."
    
    # Keep only last 7 backups
    cd "$BACKUP_DIR"
    ls -t zalopay_phishing_backup_*.tar.gz | tail -n +8 | xargs -r rm
    cd ..
    
    log_success "Old backups cleaned up"
}

verify_backup() {
    log_info "Verifying backup..."
    
    backup_file="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    
    if [ -f "$backup_file" ]; then
        # Check if backup file is not empty
        if [ -s "$backup_file" ]; then
            log_success "Backup file exists and is not empty"
            
            # Check backup file integrity
            if tar -tzf "$backup_file" > /dev/null 2>&1; then
                log_success "Backup file integrity verified"
            else
                log_error "Backup file integrity check failed"
                return 1
            fi
        else
            log_error "Backup file is empty"
            return 1
        fi
    else
        log_error "Backup file not found"
        return 1
    fi
    
    return 0
}

show_backup_info() {
    log_info "Backup Information:"
    echo "===================="
    echo "Backup Name: $BACKUP_NAME"
    echo "Backup File: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    echo "Backup Size: $(du -sh "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)"
    echo "Backup Date: $(date)"
    echo ""
    echo "To restore this backup:"
    echo "1. Stop all services: docker-compose down"
    echo "2. Extract backup: tar -xzf $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    echo "3. Restore data: ./scripts/restore.sh $BACKUP_NAME"
    echo "4. Start services: docker-compose up -d"
}

# Main backup function
backup() {
    log_info "Starting backup process..."
    echo "=================================="
    
    create_backup_directory
    backup_mongodb
    backup_redis
    backup_influxdb
    backup_configurations
    backup_logs
    backup_data
    create_backup_manifest
    compress_backup
    cleanup_old_backups

    if verify_backup; then
        show_backup_info
        log_success "Backup completed successfully!"
    else
        log_error "Backup verification failed!"
        exit 1
    fi

    echo "=================================="
}

# Handle command line arguments
case "${1:-backup}" in
    "backup")
        backup
        ;;
    "mongodb")
        create_backup_directory
        backup_mongodb
        ;;
    "redis")
        create_backup_directory
        backup_redis
        ;;
    "influxdb")
        create_backup_directory
        backup_influxdb
        ;;
    "config")
        create_backup_directory
        backup_configurations
        ;;
    "logs")
        create_backup_directory
        backup_logs
        ;;
    "data")
        create_backup_directory
        backup_data
        ;;
    "compress")
        compress_backup
        ;;
    "verify")
        verify_backup
        ;;
    "cleanup")
        cleanup_old_backups
        ;;
    "list")
        log_info "Available backups:"
        ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "No backups found"
        ;;
    *)
        echo "Usage: $0 {backup|mongodb|redis|influxdb|config|logs|data|compress|verify|cleanup|list}"
        echo ""
        echo "Commands:"
        echo "  backup     - Complete backup (default)"
        echo "  mongodb    - Backup MongoDB only"
        echo "  redis      - Backup Redis only"
        echo "  influxdb   - Backup InfluxDB only"
        echo "  config     - Backup configurations only"
        echo "  logs       - Backup logs only"
        echo "  data       - Backup data directories only"
        echo "  compress   - Compress existing backup"
        echo "  verify     - Verify backup integrity"
        echo "  cleanup    - Clean up old backups"
        echo "  list       - List available backups"
                exit 1
                ;;
        esac