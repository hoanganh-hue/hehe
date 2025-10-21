#!/bin/bash

# Security Script for ZaloPay Platform
# This script implements security best practices and checks

set -euo pipefail

# Configuration
LOG_FILE="./logs/security_$(date +%Y%m%d_%H%M%S).log"
SECURITY_REPORT="./logs/security_report_$(date +%Y%m%d_%H%M%S).txt"

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

# Check file permissions
check_file_permissions() {
    log "Checking file permissions..."

    local issues=0

    # Check secrets directory
    if [ -d "secrets" ]; then
        local secrets_perms=$(stat -c "%a" secrets)
        if [ "$secrets_perms" != "700" ]; then
            warning "Secrets directory permissions are $secrets_perms, should be 700"
            ((issues++))
        fi

        # Check individual secret files
        find secrets -type f -exec stat -c "%a %n" {} \; | while read perms file; do
            if [ "$perms" != "600" ]; then
                warning "Secret file $file has permissions $perms, should be 600"
                ((issues++))
            fi
        done
    fi

    # Check script permissions
    find scripts -name "*.sh" -type f -exec stat -c "%a %n" {} \; | while read perms file; do
        if [ "$perms" != "755" ] && [ "$perms" != "700" ]; then
            warning "Script $file has permissions $perms, should be 755 or 700"
            ((issues++))
        fi
    done

    if [ $issues -eq 0 ]; then
        success "File permissions are correct"
    else
        warning "Found $issues file permission issues"
    fi
}

# Check Docker security
check_docker_security() {
    log "Checking Docker security..."

    local issues=0

    # Check if Docker daemon is using secure configuration
    if docker info 2>/dev/null | grep -q "root"; then
        warning "Docker daemon might be running as root"
        ((issues++))
    fi

    # Check for privileged containers
    if docker-compose ps -q | xargs docker inspect 2>/dev/null | jq -r '.[] | select(.HostConfig.Privileged == true) | .Name' | grep -q .; then
        error "Found privileged containers running"
        ((issues++))
    fi

    # Check for containers running as root
    docker-compose ps -q | xargs docker inspect 2>/dev/null | jq -r '.[] | select(.Config.User == "") | .Name' | while read container; do
        if [ -n "$container" ]; then
            warning "Container $container is running as root user"
            ((issues++))
        fi
    done

    if [ $issues -eq 0 ]; then
        success "Docker security checks passed"
    else
        warning "Found $issues Docker security issues"
    fi
}

# Check SSL/TLS configuration
check_ssl_configuration() {
    log "Checking SSL/TLS configuration..."

    if [ -f "./nginx/ssl/live/zalopaymerchan.com/cert.pem" ]; then
        # Check certificate validity
        if ! openssl x509 -in "./nginx/ssl/live/zalopaymerchan.com/cert.pem" -noout -checkend 0 &> /dev/null; then
            error "SSL certificate has expired"
        else
            local days_valid=$(openssl x509 -in "./nginx/ssl/live/zalopaymerchan.com/cert.pem" -noout -dates | openssl x509 -noout -checkend $((30*24*3600)) && echo "30" || echo "0")
            if [ "$days_valid" -lt 30 ]; then
                warning "SSL certificate expires in $days_valid days"
            else
                success "SSL certificate is valid"
            fi
        fi

        # Check SSL configuration
        if grep -q "ssl_protocols" nginx/conf.d/default.conf; then
            success "SSL protocols are configured"
        else
            warning "SSL protocols may not be properly configured"
        fi
    else
        warning "SSL certificate not found"
    fi
}

# Check firewall configuration
check_firewall() {
    log "Checking firewall configuration..."

    # Check UFW status
    if command -v ufw &> /dev/null; then
        if ufw status | grep -q "Status: active"; then
            success "UFW firewall is active"

            # Check for required open ports
            if ufw status | grep -q "80/tcp"; then
                success "Port 80 is open for HTTP"
            else
                warning "Port 80 (HTTP) is not open"
            fi

            if ufw status | grep -q "443/tcp"; then
                success "Port 443 is open for HTTPS"
            else
                warning "Port 443 (HTTPS) is not open"
            fi
        else
            warning "UFW firewall is not active"
        fi
    else
        warning "UFW firewall not available"
    fi
}

# Check for security updates
check_security_updates() {
    log "Checking for security updates..."

    if command -v apt-get &> /dev/null; then
        # Update package lists
        apt-get update &> /dev/null

        # Check for security updates
        local security_updates=$(apt list --upgradable 2>/dev/null | grep -c security || true)

        if [ "$security_updates" -gt 0 ]; then
            warning "Found $security_updates security updates available"
        else
            success "No security updates found"
        fi
    fi
}

# Check password strength
check_password_strength() {
    log "Checking password strength..."

    # Check if passwords meet minimum requirements
    if [ -f "secrets/mongodb_root_password.txt" ]; then
        local password=$(cat "secrets/mongodb_root_password.txt")
        local score=0

        # Length check
        [ ${#password} -ge 12 ] && ((score++))
        # Uppercase check
        [[ "$password" =~ [A-Z] ]] && ((score++))
        # Lowercase check
        [[ "$password" =~ [a-z] ]] && ((score++))
        # Number check
        [[ "$password" =~ [0-9] ]] && ((score++))
        # Special character check
        [[ "$password" =~ [^A-Za-z0-9] ]] && ((score++))

        if [ $score -ge 4 ]; then
            success "Strong passwords configured"
        else
            warning "Weak passwords detected (score: $score/5)"
        fi
    fi
}

# Generate security report
generate_security_report() {
    log "Generating security report..."

    cat > "$SECURITY_REPORT" << EOF
ZaloPay Platform Security Report
Generated: $(date)
==================================================

File Permissions:
$(find secrets -type f -exec stat -c "%a %n" {} \; 2>/dev/null | wc -l) secret files checked

Docker Security:
$(docker-compose ps -q | wc -l) containers running
$(docker-compose ps -q | xargs docker inspect 2>/dev/null | jq -r '.[] | select(.HostConfig.Privileged == true) | .Name' | wc -l) privileged containers
$(docker-compose ps -q | xargs docker inspect 2>/dev/null | jq -r '.[] | select(.Config.User == "") | .Name' | wc -l) root containers

SSL/TLS Status:
$(if [ -f "./nginx/ssl/live/zalopaymerchan.com/cert.pem" ]; then
    echo "Certificate valid until: $(openssl x509 -in ./nginx/ssl/live/zalopaymerchan.com/cert.pem -noout -enddate | cut -d'=' -f2)"
else
    echo "No SSL certificate found"
fi)

Firewall Status:
$(ufw status | grep "Status:" | awk '{print $2}' || echo "UFW not available")

Security Updates:
$(apt list --upgradable 2>/dev/null | grep -c security || echo "0") security updates available

Password Strength:
$(if [ -f "secrets/mongodb_root_password.txt" ]; then
    password=$(cat "secrets/mongodb_root_password.txt")
    score=0
    [ ${#password} -ge 12 ] && ((score++))
    [[ "$password" =~ [A-Z] ]] && ((score++))
    [[ "$password" =~ [a-z] ]] && ((score++))
    [[ "$password" =~ [0-9] ]] && ((score++))
    [[ "$password" =~ [^A-Za-z0-9] ]] && ((score++))
    echo "$score/5"
else
    echo "Cannot check"
fi)

==================================================
Security scan completed at: $(date)
EOF

    success "Security report generated: $SECURITY_REPORT"
}

# Harden Docker configuration
harden_docker() {
    log "Hardening Docker configuration..."

    # Create Docker daemon configuration if it doesn't exist
    if [ ! -f "/etc/docker/daemon.json" ]; then
        warning "Docker daemon configuration not found"
        return 0
    fi

    # Check for security settings in daemon.json
    if ! grep -q "no-new-privileges" /etc/docker/daemon.json; then
        warning "Consider adding no-new-privileges to Docker daemon config"
    fi

    if ! grep -q "userns-remap" /etc/docker/daemon.json; then
        warning "Consider enabling user namespace remapping"
    fi

    success "Docker hardening check completed"
}

# Main security function
run_security_check() {
    log "🔒 Starting ZaloPay Platform Security Check"
    echo "=================================================="

    # Create logs directory
    mkdir -p logs

    # Run security checks
    check_file_permissions
    check_docker_security
    check_ssl_configuration
    check_firewall
    check_security_updates
    check_password_strength
    harden_docker
    generate_security_report

    echo "=================================================="
    success "🎉 Security check completed!"
    echo ""
    echo "📊 Security report: $SECURITY_REPORT"
    echo "📝 Security logs: $LOG_FILE"
}

# Apply security fixes
apply_security_fixes() {
    log "🔧 Applying security fixes..."

    # Fix secrets directory permissions
    if [ -d "secrets" ]; then
        chmod 700 secrets
        find secrets -type f -exec chmod 600 {} \;
        success "Fixed secrets directory permissions"
    fi

    # Fix script permissions
    find scripts -name "*.sh" -type f -exec chmod 755 {} \;
    success "Fixed script permissions"

    # Generate secure passwords if needed
    if [ ! -f "secrets/mongodb_root_password.txt" ]; then
        openssl rand -base64 32 > "secrets/mongodb_root_password.txt"
        chmod 600 "secrets/mongodb_root_password.txt"
        success "Generated secure MongoDB password"
    fi

    if [ ! -f "secrets/redis_password.txt" ]; then
        openssl rand -base64 32 > "secrets/redis_password.txt"
        chmod 600 "secrets/redis_password.txt"
        success "Generated secure Redis password"
    fi

    success "Security fixes applied"
}

# Main function
main() {
    local action="check"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --fix)
                action="fix"
                shift
                ;;
            --help)
                echo "Usage: $0 [--fix] [--help]"
                echo ""
                echo "Options:"
                echo "  --fix    Apply security fixes automatically"
                echo "  --help   Show this help message"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    case $action in
        "check")
            run_security_check
            ;;
        "fix")
            apply_security_fixes
            run_security_check
            ;;
    esac
}

# Run main function
main "$@"