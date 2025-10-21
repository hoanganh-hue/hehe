#!/bin/bash

# ZaloPay Merchant Platform - Routing Test Script
# Tests the routing logic for merchant, admin, and backend interfaces

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="${1:-zalopaymerchan.com}"
PROTOCOL="${2:-http}"
BASE_URL="${PROTOCOL}://${DOMAIN}"

echo "========================================"
echo "ZaloPay Routing Test Suite"
echo "========================================"
echo ""
echo -e "${BLUE}Testing: ${BASE_URL}${NC}"
echo ""

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=$3
    local description=$4
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Testing ${name}... "
    
    # Make request and get status code
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -L "${url}" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" == "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (${HTTP_CODE})"
        [ -n "$description" ] && echo "  └─ ${description}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: ${expected_code}, Got: ${HTTP_CODE})"
        [ -n "$description" ] && echo "  └─ ${description}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Test content type
test_content_type() {
    local name=$1
    local url=$2
    local expected_type=$3
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Testing ${name} content-type... "
    
    CONTENT_TYPE=$(curl -s -I "${url}" 2>/dev/null | grep -i "content-type:" | cut -d' ' -f2- | tr -d '\r\n')
    
    if [[ "$CONTENT_TYPE" == *"$expected_type"* ]]; then
        echo -e "${GREEN}✓ PASS${NC} (${CONTENT_TYPE})"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: ${expected_type}, Got: ${CONTENT_TYPE})"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Test response contains text
test_response_contains() {
    local name=$1
    local url=$2
    local search_text=$3
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Testing ${name} contains '${search_text}'... "
    
    RESPONSE=$(curl -s "${url}" 2>/dev/null)
    
    if echo "$RESPONSE" | grep -q "$search_text"; then
        echo -e "${GREEN}✓ PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Text not found)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

echo -e "${BLUE}=== Basic Connectivity Tests ===${NC}"
echo ""

test_endpoint "Root Router" "${BASE_URL}/" "200" "Landing/router page should be accessible"
test_endpoint "Merchant Portal" "${BASE_URL}/merchant/" "200" "Customer-facing interface"
test_endpoint "Admin Portal" "${BASE_URL}/admin/" "200" "Management dashboard"

echo ""
echo -e "${BLUE}=== API Endpoint Tests ===${NC}"
echo ""

test_endpoint "API Health Check" "${BASE_URL}/api/health" "200" "Backend health endpoint"
test_endpoint "API Docs (if enabled)" "${BASE_URL}/api/docs" "200|404" "API documentation"

echo ""
echo -e "${BLUE}=== BeEF Framework Tests ===${NC}"
echo ""

test_endpoint "BeEF Endpoint" "${BASE_URL}/beef/" "200|301|302" "BeEF framework proxy"

echo ""
echo -e "${BLUE}=== Static Asset Tests ===${NC}"
echo ""

test_endpoint "Favicon" "${BASE_URL}/favicon.ico" "200|404" "Site favicon"
test_endpoint "CSS Assets" "${BASE_URL}/css/merchant.css" "200|404" "CSS stylesheets"
test_endpoint "JS Assets" "${BASE_URL}/js/merchant.js" "200|404" "JavaScript files"

echo ""
echo -e "${BLUE}=== Routing Parameter Tests ===${NC}"
echo ""

test_endpoint "Route to Merchant" "${BASE_URL}/?route=merchant" "200" "URL param routing to merchant"
test_endpoint "Route to Admin" "${BASE_URL}/?route=admin" "200" "URL param routing to admin"

echo ""
echo -e "${BLUE}=== Content Type Tests ===${NC}"
echo ""

test_content_type "Root HTML" "${BASE_URL}/" "text/html"
test_content_type "Merchant HTML" "${BASE_URL}/merchant/" "text/html"
test_content_type "Admin HTML" "${BASE_URL}/admin/" "text/html"

echo ""
echo -e "${BLUE}=== Content Validation Tests ===${NC}"
echo ""

test_response_contains "Root Router Content" "${BASE_URL}/" "ZaloPay Merchant"
test_response_contains "Merchant Portal Card" "${BASE_URL}/" "Merchant Portal"
test_response_contains "Admin Portal Card" "${BASE_URL}/" "Admin Portal"

echo ""
echo -e "${BLUE}=== Security Header Tests ===${NC}"
echo ""

# Check for security headers
echo -n "Testing X-Content-Type-Options... "
HEADER=$(curl -s -I "${BASE_URL}/" 2>/dev/null | grep -i "x-content-type-options:")
if [ -n "$HEADER" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ NOT SET${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo -n "Testing X-Frame-Options... "
HEADER=$(curl -s -I "${BASE_URL}/" 2>/dev/null | grep -i "x-frame-options:")
if [ -n "$HEADER" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ NOT SET${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo -e "${BLUE}=== Docker Service Tests ===${NC}"
echo ""

# Check if docker compose is available
if command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
    echo "Checking Docker services..."
    
    # Get service status
    SERVICES=("nginx" "frontend" "backend" "mongodb-primary" "redis-primary")
    
    for service in "${SERVICES[@]}"; do
        echo -n "  ${service}... "
        STATUS=$(docker compose ps -q "$service" 2>/dev/null)
        if [ -n "$STATUS" ]; then
            RUNNING=$(docker inspect -f '{{.State.Running}}' $(docker compose ps -q "$service") 2>/dev/null)
            if [ "$RUNNING" == "true" ]; then
                echo -e "${GREEN}✓ Running${NC}"
            else
                echo -e "${RED}✗ Stopped${NC}"
            fi
        else
            echo -e "${YELLOW}⚠ Not found${NC}"
        fi
    done
else
    echo -e "${YELLOW}Docker not available - skipping service checks${NC}"
fi

echo ""
echo "========================================"
echo "Test Results Summary"
echo "========================================"
echo ""
echo -e "Total Tests:  ${BLUE}${TOTAL_TESTS}${NC}"
echo -e "Passed:       ${GREEN}${PASSED_TESTS}${NC}"
echo -e "Failed:       ${RED}${FAILED_TESTS}${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some tests failed.${NC}"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check if all Docker containers are running: docker compose ps"
    echo "2. Check nginx logs: docker compose logs nginx"
    echo "3. Check frontend logs: docker compose logs frontend"
    echo "4. Check backend logs: docker compose logs backend"
    echo "5. Verify nginx configuration: docker compose exec nginx nginx -t"
    exit 1
fi
