#!/bin/bash

# Monitoring Script for ZaloPay Platform
# This script monitors the health and performance of all services

set -euo pipefail

# Configuration
LOG_FILE="./logs/monitor_$(date +%Y%m%d_%H%M%S).log"
ALERT_EMAIL="${ALERT_EMAIL:-admin@zalopaymerchan.com}"
CHECK_INTERVAL="${CHECK_INTERVAL:-60}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"

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

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
}

# Send alert function
send_alert() {
    local message="$1"
    local priority="${2:-warning}"

    log "ALERT [$priority]: $message"

    # Email alert (if configured)
    if command -v mail &> /dev/null && [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "ZaloPay Platform Alert [$priority]" "$ALERT_EMAIL"
    fi

    # Slack alert (if webhook configured)
    if [ -n "$SLACK_WEBHOOK" ]; then
        local color=""
        case $priority in
            "error")
                color="danger"
                ;;
            "warning")
                color="warning"
                ;;
            *)
                color="good"
                ;;
        esac

        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"title\":\"ZaloPay Platform Alert\",\"text\":\"$message\",\"ts\":$(date +%s)}]}" \
            "$SLACK_WEBHOOK" &> /dev/null
    fi
}

# Check service health
check_service_health() {
    local service="$1"
    local url="$2"
    local expected_response="${3:-}"

    if curl -f -s --max-time 10 "$url" &> /dev/null; then
        success "$service is responding"
        return 0
    else
        error "$service is not responding at $url"
        return 1
    fi
}

# Check Docker service status
check_docker_service() {
    local service="$1"

    if docker-compose ps -q "$service" &> /dev/null; then
        local status=$(docker-compose ps --format "{{.Status}}" "$service")
        success "$service is running: $status"
        return 0
    else
        error "$service is not running"
        return 1
    fi
}

# Check system resources
check_system_resources() {
    log "Checking system resources..."

    # Memory usage
    local mem_usage=$(free | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
    log "Memory usage: $mem_usage"

    if echo "$mem_usage" | awk -F'%' '{if($1 > 90) print 1}'; then
        warning "High memory usage: $mem_usage"
        send_alert "High memory usage detected: $mem_usage" "warning"
    fi

    # Disk usage
    local disk_usage=$(df / | awk 'NR==2{printf "%.2f%%", $5}')
    log "Disk usage: $disk_usage"

    if echo "$disk_usage" | awk -F'%' '{if($1 > 85) print 1}'; then
        warning "High disk usage: $disk_usage"
        send_alert "High disk usage detected: $disk_usage" "warning"
    fi

    # Load average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}')
    log "Load average: $load_avg"

    success "System resources check completed"
}

# Check SSL certificate expiry
check_ssl_certificates() {
    log "Checking SSL certificate expiry..."

    if [ -f "./nginx/ssl/live/zalopaymerchan.com/cert.pem" ]; then
        local expiry_date=$(openssl x509 -in "./nginx/ssl/live/zalopaymerchan.com/cert.pem" -noout -enddate | cut -d'=' -f2)
        local days_until_expiry=$(openssl x509 -in "./nginx/ssl/live/zalopaymerchan.com/cert.pem" -noout -dates | openssl x509 -noout -checkend $((30*24*3600)) && echo "30" || echo "0")

        log "SSL certificate expires: $expiry_date"

        if [ "$days_until_expiry" -lt 30 ]; then
            warning "SSL certificate expires in $days_until_expiry days"
            send_alert "SSL certificate expires in $days_until_expiry days" "warning"
        else
            success "SSL certificate is valid ($days_until_expiry days remaining)"
        fi
    else
        warning "SSL certificate not found"
    fi
}

# Check database connectivity
check_database_connectivity() {
    log "Checking database connectivity..."

    # MongoDB connectivity
    if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
        success "MongoDB is accessible"
    else
        error "MongoDB is not accessible"
        send_alert "MongoDB connectivity failed" "error"
        return 1
    fi

    # Redis connectivity
    if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
        success "Redis is accessible"
    else
        error "Redis is not accessible"
        send_alert "Redis connectivity failed" "error"
        return 1
    fi

    return 0
}

# Main monitoring function
run_monitoring() {
    log "🔍 Starting ZaloPay Platform Monitoring"
    echo "=================================================="

    local errors=0

    # Check Docker services
    log "Checking Docker services..."
    local services=("nginx" "backend" "beef" "mongodb" "redis" "filebeat")

    for service in "${services[@]}"; do
        if ! check_docker_service "$service"; then
            ((errors++))
        fi
    done

    # Check service health endpoints
    log "Checking service health endpoints..."

    check_service_health "Nginx" "http://localhost/health" && ((errors--)) || ((errors++))
    check_service_health "Backend API" "http://localhost:8000/health" && ((errors--)) || ((errors++))
    check_service_health "BeEF API" "http://localhost:3000/api/hooks" && ((errors--)) || ((errors++))

    # Check system resources
    check_system_resources

    # Check SSL certificates
    check_ssl_certificates

    # Check database connectivity
    if ! check_database_connectivity; then
        ((errors++))
    fi

    # Summary
    echo "=================================================="

    if [ $errors -eq 0 ]; then
        success "All checks passed"
        return 0
    else
        error "$errors check(s) failed"
        send_alert "$errors monitoring check(s) failed" "error"
        return 1
    fi
}

# Continuous monitoring mode
continuous_monitoring() {
    log "Starting continuous monitoring (interval: $CHECK_INTERVAL seconds)..."

    while true; do
        if ! run_monitoring; then
            warning "Monitoring detected issues"
        fi

        sleep "$CHECK_INTERVAL"
    done
}

# Main function
main() {
    # Create logs directory
    mkdir -p logs

    # Parse arguments
    local continuous=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --continuous)
                continuous=true
                shift
                ;;
            --interval)
                CHECK_INTERVAL="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [--continuous] [--interval SECONDS] [--help]"
                echo ""
                echo "Options:"
                echo "  --continuous  Run continuous monitoring"
                echo "  --interval    Set check interval in seconds (default: 60)"
                echo "  --help        Show this help message"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    if $continuous; then
        continuous_monitoring
    else
        run_monitoring
    fi
}

# Run main function
main "$@"
