#!/bin/bash
# ZaloPay Merchant Phishing Platform - Comprehensive Analysis Runner
# Chạy toàn bộ quy trình phân tích dữ liệu và tạo báo cáo

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

success() {
    echo -e "${PURPLE}[SUCCESS] $1${NC}"
}

# Configuration
PROJECT_ROOT="/home/lucian/zalopay_phishing_platform"
VENV_PATH="/opt/zalopay/venv"
REPORTS_DIR="/opt/zalopay/reports"
BACKUP_DIR="/opt/zalopay/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create necessary directories
mkdir -p $REPORTS_DIR
mkdir -p $BACKUP_DIR

# Function to check system requirements
check_requirements() {
    log "🔍 Checking system requirements..."
    
    # Check if virtual environment exists
    if [[ ! -d "$VENV_PATH" ]]; then
        error "Virtual environment not found at $VENV_PATH"
    fi
    
    # Check if MongoDB is running
    if ! pgrep -x "mongod" > /dev/null; then
        error "MongoDB is not running"
    fi
    
    # Check if Redis is running
    if ! pgrep -x "redis-server" > /dev/null; then
        error "Redis is not running"
    fi
    
    # Check if InfluxDB is running
    if ! pgrep -x "influxd" > /dev/null; then
        error "InfluxDB is not running"
    fi
    
    # Check Python dependencies
    source $VENV_PATH/bin/activate
    python3 -c "import pymongo, redis, influxdb_client" 2>/dev/null || {
        error "Required Python packages not installed"
    }
    
    log "✅ System requirements check passed"
}

# Function to run database health check
run_database_health_check() {
    log "🏥 Running database health check..."
    
    source $VENV_PATH/bin/activate
    python3 $PROJECT_ROOT/scripts/monitor_database.py > $REPORTS_DIR/health_check_$TIMESTAMP.json
    
    if [[ $? -eq 0 ]]; then
        success "Database health check completed"
    else
        error "Database health check failed"
    fi
}

# Function to run data validation
run_data_validation() {
    log "🔍 Running comprehensive data validation..."
    
    source $VENV_PATH/bin/activate
    python3 $PROJECT_ROOT/scripts/data_validation_suite.py > $REPORTS_DIR/validation_results_$TIMESTAMP.json
    
    if [[ $? -eq 0 ]]; then
        success "Data validation completed"
    else
        warning "Data validation completed with issues"
    fi
}

# Function to generate comprehensive reports
generate_reports() {
    log "📊 Generating comprehensive reports..."
    
    source $VENV_PATH/bin/activate
    
    # Generate different types of reports
    report_types=("executive" "operational" "intelligence" "security" "data_quality" "performance" "full")
    
    for report_type in "${report_types[@]}"; do
        log "Generating $report_type report..."
        python3 $PROJECT_ROOT/scripts/comprehensive_reporting_system.py $report_type > $REPORTS_DIR/${report_type}_report_$TIMESTAMP.json
        
        if [[ $? -eq 0 ]]; then
            success "$report_type report generated"
        else
            warning "$report_type report generation failed"
        fi
    done
}

# Function to create data backup
create_backup() {
    log "💾 Creating data backup..."
    
    # Run backup script
    bash $PROJECT_ROOT/scripts/backup_database.sh
    
    if [[ $? -eq 0 ]]; then
        success "Data backup completed"
    else
        error "Data backup failed"
    fi
}

# Function to generate visualizations
generate_visualizations() {
    log "📈 Generating data visualizations..."
    
    source $VENV_PATH/bin/activate
    
    # Install visualization dependencies if not present
    pip install matplotlib seaborn plotly pandas numpy > /dev/null 2>&1
    
    # Generate visualizations
    python3 -c "
import sys
sys.path.append('$PROJECT_ROOT')
from scripts.comprehensive_reporting_system import ComprehensiveReportingSystem
import asyncio

async def generate_viz():
    reporter = ComprehensiveReportingSystem()
    reporter.generate_visualizations('$REPORTS_DIR')

asyncio.run(generate_viz())
"
    
    if [[ $? -eq 0 ]]; then
        success "Visualizations generated"
    else
        warning "Visualization generation failed"
    fi
}

# Function to create summary report
create_summary_report() {
    log "📋 Creating summary report..."
    
    cat > $REPORTS_DIR/analysis_summary_$TIMESTAMP.md << EOF
# ZaloPay Phishing Platform - Analysis Summary

**Generated**: $(date)
**Analysis ID**: $TIMESTAMP

## Overview
This comprehensive analysis was performed on the ZaloPay Merchant Phishing Platform to assess data quality, system performance, and intelligence insights.

## Files Generated
- Health Check: health_check_$TIMESTAMP.json
- Validation Results: validation_results_$TIMESTAMP.json
- Executive Report: executive_report_$TIMESTAMP.json
- Operational Report: operational_report_$TIMESTAMP.json
- Intelligence Report: intelligence_report_$TIMESTAMP.json
- Security Report: security_report_$TIMESTAMP.json
- Data Quality Report: data_quality_report_$TIMESTAMP.json
- Performance Report: performance_report_$TIMESTAMP.json
- Full Report: full_report_$TIMESTAMP.json

## Visualizations
- Geographic Distribution: geographic_distribution.png
- Campaign Status: campaign_status.png
- Hourly Patterns: hourly_patterns.png

## Backup
- Database Backup: backup_$TIMESTAMP.tar.gz

## Next Steps
1. Review all generated reports
2. Address any critical issues identified
3. Implement recommendations
4. Schedule regular analysis runs

## Contact
For questions about this analysis, contact the development team.
EOF

    success "Summary report created"
}

# Function to send notifications
send_notifications() {
    log "📧 Sending notifications..."
    
    # This would typically send email notifications or webhooks
    # For now, just log the completion
    
    info "Analysis completed successfully"
    info "Reports available in: $REPORTS_DIR"
    info "Backup available in: $BACKUP_DIR"
}

# Function to cleanup old files
cleanup_old_files() {
    log "🧹 Cleaning up old files..."
    
    # Keep only last 10 analysis runs
    find $REPORTS_DIR -name "*.json" -type f -mtime +30 -delete 2>/dev/null || true
    find $REPORTS_DIR -name "*.png" -type f -mtime +30 -delete 2>/dev/null || true
    find $BACKUP_DIR -name "backup_*.tar.gz" -type f -mtime +7 -delete 2>/dev/null || true
    
    success "Cleanup completed"
}

# Main execution function
main() {
    log "🚀 Starting ZaloPay Phishing Platform Comprehensive Analysis"
    log "Timestamp: $TIMESTAMP"
    log "Reports Directory: $REPORTS_DIR"
    
    # Check requirements
    check_requirements
    
    # Run analysis steps
    run_database_health_check
    run_data_validation
    generate_reports
    create_backup
    generate_visualizations
    create_summary_report
    
    # Cleanup and notifications
    cleanup_old_files
    send_notifications
    
    # Final summary
    log "🎉 Comprehensive analysis completed successfully!"
    log "📊 Reports generated: $(ls -1 $REPORTS_DIR/*_$TIMESTAMP.* | wc -l)"
    log "💾 Backup created: backup_$TIMESTAMP.tar.gz"
    log "📁 All files saved to: $REPORTS_DIR"
    
    success "Analysis completed successfully!"
}

# Handle command line arguments
case "${1:-}" in
    "health")
        check_requirements
        run_database_health_check
        ;;
    "validation")
        check_requirements
        run_data_validation
        ;;
    "reports")
        check_requirements
        generate_reports
        ;;
    "backup")
        create_backup
        ;;
    "visualizations")
        check_requirements
        generate_visualizations
        ;;
    "full")
        main
        ;;
    *)
        echo "Usage: $0 {health|validation|reports|backup|visualizations|full}"
        echo ""
        echo "Options:"
        echo "  health        - Run database health check only"
        echo "  validation    - Run data validation only"
        echo "  reports       - Generate reports only"
        echo "  backup        - Create backup only"
        echo "  visualizations - Generate visualizations only"
        echo "  full          - Run complete analysis (default)"
        exit 1
        ;;
esac