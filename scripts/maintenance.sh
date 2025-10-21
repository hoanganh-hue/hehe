#!/bin/bash

# Maintenance Script for ZaloPay Platform
# This script performs routine maintenance tasks

set -euo pipefail

# Configuration
LOG_FILE="./logs/maintenance_$(date +%Y%m%d_%H%M%S).log"
MAINTENANCE_LOG="./logs/maintenance.log"

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

# Rotate logs
rotate_logs() {
    log "Rotating logs..."

    # Create log directories
    mkdir -p logs

    # Rotate application logs
    if [ -d "./logs" ]; then
        # Compress old log files
        find ./logs -name "*.log" -type f -mtime +7 -exec gzip {} \;

        # Remove logs older than 30 days
        find ./logs -name "*.log.gz" -type f -mtime +30 -delete

        success "Log rotation completed"
    fi
}

# Clean Docker resources
clean_docker_resources() {
    log "Cleaning Docker resources..."

    # Remove stopped containers
    local stopped_containers=$(docker container prune -f | grep -o '[0-9]\+ containers' || true)
    if [ -n "$stopped_containers" ]; then
        success "Cleaned: $stopped_containers"
    fi

    # Remove unused images
    local cleaned_images=$(docker image prune -f | grep -o '[0-9.]\+ MB' || true)
    if [ -n "$cleaned_images" ]; then
        success "Cleaned: $cleaned_images of unused images"
    fi

    # Remove unused networks
    local cleaned_networks=$(docker network prune -f | grep -o '[0-9]\+ networks' || true)
    if [ -n "$cleaned_networks" ]; then
        success "Cleaned: $cleaned_networks"
    fi

    # Remove unused volumes
    local cleaned_volumes=$(docker volume prune -f | grep -o '[0-9]\+ volumes' || true)
    if [ -n "$cleaned_volumes" ]; then
        success "Cleaned: $cleaned_volumes"
    fi
}

# Update Docker images
update_docker_images() {
    log "Updating Docker images..."

    # Pull latest images
    if docker-compose pull; then
        success "Docker images updated"
    else
        warning "Failed to update some Docker images"
    fi
}

# Optimize databases
optimize_databases() {
    log "Optimizing databases..."

    # MongoDB optimization
    if docker-compose ps -q mongodb &> /dev/null; then
        log "Optimizing MongoDB..."

        # Run MongoDB optimization commands
        docker-compose exec -T mongodb mongosh \
            --username "$(cat secrets/mongodb_root_username.txt)" \
            --password "$(cat secrets/mongodb_root_password.txt)" \
            --authenticationDatabase admin \
            --eval "
                use zalopay_phishing;
                db.repairDatabase();
                db.adminCommand({ setParameter: 1, syncdelay: 60 });
            "

        success "MongoDB optimization completed"
    fi

    # Redis optimization
    if docker-compose ps -q redis &> /dev/null; then
        log "Optimizing Redis..."

        # Set Redis memory policy and save configuration
        docker-compose exec -T redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
        docker-compose exec -T redis redis-cli BGSAVE

        success "Redis optimization completed"
    fi
}

# Security updates
security_updates() {
    log "Checking for security updates..."

    # Update package lists
    if command -v apt-get &> /dev/null; then
        apt-get update &> /dev/null

        # Check for security updates (don't actually install)
        local security_updates=$(apt-get upgrade --dry-run 2>/dev/null | grep -c "^Inst" || true)

        if [ "$security_updates" -gt 0 ]; then
            warning "Found $security_updates security updates available"
            log "Run 'apt-get upgrade' to install security updates"
        else
            success "No security updates found"
        fi
    fi
}

# Health check
health_check() {
    log "Running health checks..."

    # Use the monitoring script for health checks
    if [ -f "./scripts/monitor.sh" ]; then
        if ./scripts/monitor.sh; then
            success "Health checks passed"
        else
            warning "Some health checks failed"
        fi
    else
        warning "Monitor script not found"
    fi
}

# Generate maintenance report
generate_report() {
    log "Generating maintenance report..."

    local report_file="./logs/maintenance_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$report_file" << EOF
ZaloPay Platform Maintenance Report
Generated: $(date)
==================================================

System Information:
$(uname -a)

Docker Version:
$(docker --version)

Docker Compose Version:
$(docker-compose --version)

Disk Usage:
$(df -h / | tail -1)

Memory Usage:
$(free -h | head -2)

Active Containers:
$(docker-compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No active containers")

Recent Logs:
$(find ./logs -name "*.log" -type f -mtime -1 | wc -l) log files in the last 24 hours

Backup Status:
$(find ./backups -name "*.tar.gz" -type f | wc -l) backup archives available

SSL Certificate Status:
$(if [ -f "./nginx/ssl/live/zalopaymerchan.com/cert.pem" ]; then
    echo "Valid until: $(openssl x509 -in ./nginx/ssl/live/zalopaymerchan.com/cert.pem -noout -enddate | cut -d'=' -f2)"
else
    echo "No SSL certificate found"
fi)

==================================================
Maintenance completed at: $(date)
EOF

    success "Maintenance report generated: $report_file"
}

# Main maintenance function
run_maintenance() {
    log "🔧 Starting ZaloPay Platform Maintenance"
    echo "=================================================="

    # Create logs directory
    mkdir -p logs

    # Run maintenance tasks
    rotate_logs
    clean_docker_resources
    update_docker_images
    optimize_databases
    security_updates
    health_check
    generate_report

    echo "=================================================="
    success "🎉 Maintenance completed successfully!"
    echo ""
    echo "📝 Maintenance logs: $LOG_FILE"
    echo "📊 Maintenance report: $(ls -t ./logs/maintenance_report_*.txt 2>/dev/null | head -1)"
}

# Scheduled maintenance mode
scheduled_maintenance() {
    log "Starting scheduled maintenance..."

    # Create maintenance flag
    touch .maintenance_mode

    # Put application in maintenance mode (if applicable)
    log "Putting application in maintenance mode..."

    # Run maintenance
    run_maintenance

    # Remove maintenance flag
    rm -f .maintenance_mode

    success "Scheduled maintenance completed"
}

# Main function
main() {
    local mode="normal"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --scheduled)
                mode="scheduled"
                shift
                ;;
            --help)
                echo "Usage: $0 [--scheduled] [--help]"
                echo ""
                echo "Options:"
                echo "  --scheduled  Run in scheduled maintenance mode"
                echo "  --help       Show this help message"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    case $mode in
        "scheduled")
            scheduled_maintenance
            ;;
        "normal")
            run_maintenance
            ;;
    esac
}

# Run main function
main "$@"