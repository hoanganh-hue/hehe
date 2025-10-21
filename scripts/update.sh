#!/bin/bash
# ZaloPay Platform Update Script
# Automated update and deployment script

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
NAMESPACE="${NAMESPACE:-zalopay-platform}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-zalopay}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
UPDATE_TYPE="${1:-rolling}"

# Logging functions
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "Namespace $NAMESPACE does not exist"
        exit 1
    fi
    
    log_success "Prerequisites check completed"
}

# Create backup before update
create_backup() {
    log_info "Creating backup before update..."
    
    if [ -f "$SCRIPT_DIR/backup.sh" ]; then
        "$SCRIPT_DIR/backup.sh"
        log_success "Backup created successfully"
    else
        log_warning "Backup script not found - skipping backup"
    fi
}

# Build new images
build_images() {
    log_info "Building new images..."
    
    # Build backend image
    log_info "Building backend image..."
    docker build -t "$DOCKER_REGISTRY/backend:$IMAGE_TAG" "$PROJECT_ROOT/backend"
    log_success "Backend image built: $DOCKER_REGISTRY/backend:$IMAGE_TAG"
    
    # Build frontend image
    log_info "Building frontend image..."
    docker build -t "$DOCKER_REGISTRY/frontend:$IMAGE_TAG" "$PROJECT_ROOT/frontend"
    log_success "Frontend image built: $DOCKER_REGISTRY/frontend:$IMAGE_TAG"
    
    # Build BeEF image
    log_info "Building BeEF image..."
    docker build -t "$DOCKER_REGISTRY/beef:$IMAGE_TAG" "$PROJECT_ROOT/beef_framework"
    log_success "BeEF image built: $DOCKER_REGISTRY/beef:$IMAGE_TAG"
}

# Push images to registry
push_images() {
    if [ "$DOCKER_REGISTRY" != "zalopay" ]; then
        log_info "Pushing images to registry: $DOCKER_REGISTRY"
        
        docker push "$DOCKER_REGISTRY/backend:$IMAGE_TAG"
        docker push "$DOCKER_REGISTRY/frontend:$IMAGE_TAG"
        docker push "$DOCKER_REGISTRY/beef:$IMAGE_TAG"
        
        log_success "Images pushed to registry"
    else
        log_warning "Using local images - skipping push"
    fi
}

# Update backend deployment
update_backend() {
    log_info "Updating backend deployment..."
    
    # Update image in deployment
    kubectl set image deployment/zalopay-backend \
        zalopay-backend="$DOCKER_REGISTRY/backend:$IMAGE_TAG" \
        -n "$NAMESPACE"
    
    # Wait for rollout to complete
    kubectl rollout status deployment/zalopay-backend -n "$NAMESPACE" --timeout=300s
    
    log_success "Backend deployment updated"
}

# Update frontend deployment
update_frontend() {
    log_info "Updating frontend deployment..."
    
    # Update image in deployment
    kubectl set image deployment/zalopay-frontend \
        zalopay-frontend="$DOCKER_REGISTRY/frontend:$IMAGE_TAG" \
        -n "$NAMESPACE"
    
    # Wait for rollout to complete
    kubectl rollout status deployment/zalopay-frontend -n "$NAMESPACE" --timeout=300s
    
    log_success "Frontend deployment updated"
}

# Update BeEF deployment
update_beef() {
    log_info "Updating BeEF deployment..."
    
    # Update image in deployment
    kubectl set image deployment/beef \
        beef="$DOCKER_REGISTRY/beef:$IMAGE_TAG" \
        -n "$NAMESPACE"
    
    # Wait for rollout to complete
    kubectl rollout status deployment/beef -n "$NAMESPACE" --timeout=300s
    
    log_success "BeEF deployment updated"
}

# Rolling update
rolling_update() {
    log_info "Performing rolling update..."
    
    update_backend
    update_frontend
    update_beef
    
    log_success "Rolling update completed"
}

# Blue-green deployment
blue_green_update() {
    log_info "Performing blue-green deployment..."
    
    # Get current deployment status
    CURRENT_BACKEND_REPLICAS=$(kubectl get deployment zalopay-backend -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    CURRENT_FRONTEND_REPLICAS=$(kubectl get deployment zalopay-frontend -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    
    # Scale down current deployments
    kubectl scale deployment zalopay-backend --replicas=0 -n "$NAMESPACE"
    kubectl scale deployment zalopay-frontend --replicas=0 -n "$NAMESPACE"
    
    # Wait for pods to terminate
    kubectl wait --for=delete pod -l app=zalopay-backend -n "$NAMESPACE" --timeout=60s
    kubectl wait --for=delete pod -l app=zalopay-frontend -n "$NAMESPACE" --timeout=60s
    
    # Update images
    update_backend
    update_frontend
    update_beef
    
    # Scale back up
    kubectl scale deployment zalopay-backend --replicas="$CURRENT_BACKEND_REPLICAS" -n "$NAMESPACE"
    kubectl scale deployment zalopay-frontend --replicas="$CURRENT_FRONTEND_REPLICAS" -n "$NAMESPACE"
    
    log_success "Blue-green deployment completed"
}

# Canary deployment
canary_update() {
    log_info "Performing canary deployment..."
    
    # Deploy canary version with 10% traffic
    kubectl patch deployment zalopay-backend -n "$NAMESPACE" -p '{"spec":{"template":{"spec":{"containers":[{"name":"zalopay-backend","image":"'$DOCKER_REGISTRY'/backend:'$IMAGE_TAG'"}]}}}}'
    
    # Wait for canary to be ready
    kubectl rollout status deployment/zalopay-backend -n "$NAMESPACE" --timeout=300s
    
    # Monitor canary for 5 minutes
    log_info "Monitoring canary deployment for 5 minutes..."
    sleep 300
    
    # Check canary health
    if kubectl exec -n "$NAMESPACE" deployment/zalopay-backend -- curl -f http://localhost:8000/health &> /dev/null; then
        log_success "Canary deployment healthy - proceeding with full rollout"
        
        # Full rollout
        kubectl patch deployment zalopay-frontend -n "$NAMESPACE" -p '{"spec":{"template":{"spec":{"containers":[{"name":"zalopay-frontend","image":"'$DOCKER_REGISTRY'/frontend:'$IMAGE_TAG'"}]}}}}'
        kubectl rollout status deployment/zalopay-frontend -n "$NAMESPACE" --timeout=300s
        
        log_success "Canary deployment completed"
    else
        log_error "Canary deployment unhealthy - rolling back"
        kubectl rollout undo deployment/zalopay-backend -n "$NAMESPACE"
        exit 1
    fi
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Check backend health
    if kubectl exec -n "$NAMESPACE" deployment/zalopay-backend -- curl -f http://localhost:8000/health &> /dev/null; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
        return 1
    fi
    
    # Check frontend health
    if kubectl exec -n "$NAMESPACE" deployment/zalopay-frontend -- curl -f http://localhost:80 &> /dev/null; then
        log_success "Frontend health check passed"
    else
        log_error "Frontend health check failed"
        return 1
    fi
    
    # Check BeEF health
    if kubectl exec -n "$NAMESPACE" deployment/beef -- curl -f http://localhost:3000 &> /dev/null; then
        log_success "BeEF health check passed"
    else
        log_error "BeEF health check failed"
        return 1
    fi
    
    log_success "All health checks passed"
}

# Rollback deployment
rollback_deployment() {
    log_info "Rolling back deployment..."
    
    # Rollback backend
    kubectl rollout undo deployment/zalopay-backend -n "$NAMESPACE"
    kubectl rollout status deployment/zalopay-backend -n "$NAMESPACE" --timeout=300s
    
    # Rollback frontend
    kubectl rollout undo deployment/zalopay-frontend -n "$NAMESPACE"
    kubectl rollout status deployment/zalopay-frontend -n "$NAMESPACE" --timeout=300s
    
    # Rollback BeEF
    kubectl rollout undo deployment/beef -n "$NAMESPACE"
    kubectl rollout status deployment/beef -n "$NAMESPACE" --timeout=300s
    
    log_success "Rollback completed"
}

# Display update information
display_update_info() {
    log_info "Update completed successfully!"
    echo
    echo "=== Update Information ==="
    echo "Update Type: $UPDATE_TYPE"
    echo "Namespace: $NAMESPACE"
    echo "Image Tag: $IMAGE_TAG"
    echo "Docker Registry: $DOCKER_REGISTRY"
    echo
    echo "=== Deployment Status ==="
    kubectl get deployments -n "$NAMESPACE"
    echo
    echo "=== Pod Status ==="
    kubectl get pods -n "$NAMESPACE"
    echo
    echo "=== Service Status ==="
    kubectl get services -n "$NAMESPACE"
}

# Main update function
main() {
    log_info "Starting ZaloPay Platform update..."
    log_info "Update type: $UPDATE_TYPE"
    log_info "Namespace: $NAMESPACE"
    log_info "Docker Registry: $DOCKER_REGISTRY"
    log_info "Image Tag: $IMAGE_TAG"
    echo
    
    check_prerequisites
    create_backup
    build_images
    push_images
    
    # Perform update based on type
    case "$UPDATE_TYPE" in
        "rolling")
            rolling_update
            ;;
        "blue-green")
            blue_green_update
            ;;
        "canary")
            canary_update
            ;;
        *)
            log_error "Invalid update type: $UPDATE_TYPE"
            log_info "Valid options: rolling, blue-green, canary"
            exit 1
            ;;
    esac
    
    # Run health checks
    if run_health_checks; then
        display_update_info
        log_success "ZaloPay Platform update completed successfully!"
    else
        log_error "Health checks failed - rolling back"
        rollback_deployment
        exit 1
    fi
}

# Error handling
trap 'log_error "Update failed at line $LINENO"; rollback_deployment; exit 1' ERR

# Run main function
main "$@"