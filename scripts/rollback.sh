#!/bin/bash

# Rollback Script for ZaloPay Platform
# This script handles rollback to previous deployments

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Configuration
COMPOSE_FILE="docker-compose.yml"
LOG_FILE="./logs/rollback_$(date +%Y%m%d_%H%M%S).log"

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

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

# List available backups
list_backups() {
    echo "Available backups:"
    echo "=================================================="

    if [ -d "./backups" ]; then
        local count=0
        while IFS= read -r -d '' backup_dir; do
            ((count++))
            local backup_name=$(basename "$backup_dir")
            echo "$count) $backup_name"

            # Show backup info if available
            if [ -f "$backup_dir/backup_info.txt" ]; then
                echo "   $(cat "$backup_dir/backup_info.txt")"
            fi
            echo ""
        done < <(find ./backups -maxdepth 1 -type d -name "20*" -print0 | sort -z -r)
    else
        echo "No backups found in ./backups directory"
        exit 1
    fi
}

# Validate backup
validate_backup() {
    local backup_path="$1"

    if [ ! -d "$backup_path" ]; then
        error "Backup directory $backup_path does not exist"
        exit 1
    fi

    # Check for required backup files
    local required_files=(
        "docker_ps.txt"
        "docker_logs.txt"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "$backup_path/$file" ]; then
            warning "Required backup file $file not found"
        fi
    done

    success "Backup validation completed"
}

# Perform rollback
perform_rollback() {
    local backup_path="$1"

    log "Starting rollback to: $(basename "$backup_path")"

    # Stop current deployment
    log "Stopping current deployment..."
    docker-compose -f "$COMPOSE_FILE" down --timeout 60

    # Restore MongoDB data if available
    if [ -d "$backup_path/mongodump" ]; then
        log "Restoring MongoDB data..."

        # Start MongoDB
        docker-compose -f "$COMPOSE_FILE" up -d mongodb

        # Wait for MongoDB to be ready
        sleep 15

        # Restore data
        docker run --rm \
            -v zalopay_mongodb_data:/data/db \
            -v "$backup_path/mongodump:/tmp/mongodump" \
            mongo:6.0 \
            mongorestore \
            --username "$(cat secrets/mongodb_root_username.txt)" \
            --password "$(cat secrets/mongodb_root_password.txt)" \
            --authenticationDatabase admin \
            /tmp/mongodump

        # Stop MongoDB
        docker-compose -f "$COMPOSE_FILE" stop mongodb

        success "MongoDB data restored"
    else
        warning "No MongoDB backup found, skipping database restore"
    fi

    # Start services
    log "Starting services from backup..."
    docker-compose -f "$COMPOSE_FILE" up -d --wait --timeout 300

    # Wait for services to stabilize
    sleep 30

    # Verify rollback
    verify_rollback

    success "Rollback completed successfully"
}

# Verify rollback
verify_rollback() {
    log "Verifying rollback..."

    local services=("nginx" "backend" "beef" "mongodb" "redis")
    local failed_services=()

    for service in "${services[@]}"; do
        if ! docker-compose ps -q "$service" &> /dev/null; then
            error "Service $service is not running after rollback"
            failed_services+=("$service")
            continue
        fi

        # Check health endpoints
        case $service in
            "nginx")
                if ! curl -f -s "http://localhost/health" &> /dev/null; then
                    error "Nginx health check failed after rollback"
                    failed_services+=("$service")
                fi
                ;;
            "backend")
                if ! curl -f -s "http://localhost:8000/health" &> /dev/null; then
                    error "Backend health check failed after rollback"
                    failed_services+=("$service")
                fi
                ;;
            "beef")
                if ! curl -f -s "http://localhost:3000/api/hooks" &> /dev/null; then
                    error "BeEF health check failed after rollback"
                    failed_services+=("$service")
                fi
                ;;
        esac
    done

    if [ ${#failed_services[@]} -eq 0 ]; then
        success "All services are healthy after rollback"
    else
        error "Some services failed after rollback: ${failed_services[*]}"
        return 1
    fi
}

# Main rollback process
main() {
    local target_backup=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backup)
                target_backup="$2"
                shift 2
                ;;
            --list)
                list_backups
                exit 0
                ;;
            --help)
                echo "Usage: $0 [--backup BACKUP_DIR] [--list] [--help]"
                echo ""
                echo "Options:"
                echo "  --backup BACKUP_DIR  Specify backup directory to rollback to"
                echo "  --list               List available backups"
                echo "  --help               Show this help message"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Create logs directory
    mkdir -p logs

    log "🔄 Starting Rollback Process"
    echo "=================================================="

    if [ -z "$target_backup" ]; then
        echo "No backup specified. Available backups:"
        list_backups
        echo ""
        read -p "Enter backup number or path: " selection

        # Check if selection is a number
        if [[ $selection =~ ^[0-9]+$ ]]; then
            # Get backup by number
            local backups=($(find ./backups -maxdepth 1 -type d -name "20*" | sort -r))
            if [ $selection -gt ${#backups[@]} ] || [ $selection -lt 1 ]; then
                error "Invalid backup number"
                exit 1
            fi
            target_backup="${backups[$selection-1]}"
        else
            # Treat as path
            target_backup="./backups/$selection"
        fi
    fi

    # Validate backup
    validate_backup "$target_backup"

    # Perform rollback
    if ! perform_rollback "$target_backup"; then
        error "Rollback failed"
        exit 1
    fi

    echo "=================================================="
    success "🎉 Rollback completed successfully!"
    echo ""
    echo "📝 Rollback logs: $LOG_FILE"
    echo "🔧 You can check service status with: docker-compose ps"
}

# Run main function
main "$@"