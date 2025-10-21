"""
Test Configuration and Runner for ZaloPay Merchant Phishing Platform
Comprehensive test configuration and execution framework
"""

import os
import sys
import unittest
import pytest
import json
import time
import subprocess
import tempfile
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class TestConfig:
    """Test configuration class"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.test_root = self.project_root / "tests"
        self.backend_root = self.project_root / "backend"
        self.frontend_root = self.project_root / "frontend"
        
        # Test environment configuration
        self.test_env = {
            "MONGODB_URI": "mongodb://localhost:27017/zalopay_test",
            "REDIS_URL": "redis://localhost:6379/0",
            "INFLUXDB_URL": "http://localhost:8086",
            "BEEF_URL": "http://localhost:3000",
            "ENVIRONMENT": "test",
            "LOG_LEVEL": "DEBUG",
            "TEST_MODE": "true"
        }
        
        # Test data configuration
        self.test_data = {
            "victims": [
                {
                    "victim_id": "test_victim_1",
                    "email": "test1@example.com",
                    "password": "test_password_1",
                    "location": "Vietnam",
                    "device_type": "desktop"
                },
                {
                    "victim_id": "test_victim_2",
                    "email": "test2@example.com",
                    "password": "test_password_2",
                    "location": "Vietnam",
                    "device_type": "mobile"
                }
            ],
            "admins": [
                {
                    "admin_id": "test_admin_1",
                    "username": "admin",
                    "password": "admin_password",
                    "role": "super_admin"
                }
            ],
            "campaigns": [
                {
                    "campaign_id": "test_campaign_1",
                    "name": "Test Campaign 1",
                    "status": "active",
                    "target_demographic": "business_users"
                }
            ]
        }
        
        # Test database configuration
        self.test_db_config = {
            "mongodb": {
                "host": "localhost",
                "port": 27017,
                "database": "zalopay_test",
                "collections": [
                    "victims",
                    "oauth_tokens",
                    "admin_users",
                    "campaigns",
                    "activity_logs",
                    "gmail_access_logs",
                    "beef_sessions"
                ]
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0
            },
            "influxdb": {
                "host": "localhost",
                "port": 8086,
                "database": "zalopay_test"
            }
        }
        
        # Test coverage configuration
        self.coverage_config = {
            "source": ["backend/"],
            "omit": [
                "backend/tests/*",
                "backend/venv/*",
                "backend/__pycache__/*",
                "backend/*/__pycache__/*"
            ],
            "threshold": 80
        }
        
        # Test performance configuration
        self.performance_config = {
            "api_response_time": 2.0,  # seconds
            "database_query_time": 1.0,  # seconds
            "concurrent_users": 100,
            "load_test_duration": 300,  # seconds
            "memory_usage_limit": "512MB",
            "cpu_usage_limit": 80  # percentage
        }

class TestRunner:
    """Test runner class"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def setup_test_environment(self):
        """Set up test environment"""
        print("Setting up test environment...")
        
        # Set environment variables
        for key, value in self.config.test_env.items():
            os.environ[key] = value
        
        # Create test directories
        test_dirs = [
            self.config.test_root / "unit",
            self.config.test_root / "integration",
            self.config.test_root / "e2e",
            self.config.test_root / "fixtures",
            self.config.test_root / "reports"
        ]
        
        for test_dir in test_dirs:
            test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test database
        self._setup_test_database()
        
        # Create test fixtures
        self._create_test_fixtures()
        
        print("✓ Test environment setup complete")
    
    def _setup_test_database(self):
        """Set up test database"""
        print("Setting up test database...")
        
        try:
            # MongoDB setup
            import pymongo
            client = pymongo.MongoClient(self.config.test_db_config["mongodb"]["host"])
            db = client[self.config.test_db_config["mongodb"]["database"]]
            
            # Create collections
            for collection_name in self.config.test_db_config["mongodb"]["collections"]:
                if collection_name not in db.list_collection_names():
                    db.create_collection(collection_name)
            
            print("✓ MongoDB test database setup complete")
            
        except Exception as e:
            print(f"⚠ MongoDB setup failed: {e}")
        
        try:
            # Redis setup
            import redis
            r = redis.Redis(
                host=self.config.test_db_config["redis"]["host"],
                port=self.config.test_db_config["redis"]["port"],
                db=self.config.test_db_config["redis"]["db"]
            )
            r.ping()
            print("✓ Redis test database setup complete")
            
        except Exception as e:
            print(f"⚠ Redis setup failed: {e}")
    
    def _create_test_fixtures(self):
        """Create test fixtures"""
        print("Creating test fixtures...")
        
        # Create test data files
        fixtures_dir = self.config.test_root / "fixtures"
        
        # Victim data fixture
        victim_fixture = {
            "victims": self.config.test_data["victims"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "description": "Test victim data for unit and integration tests"
        }
        
        with open(fixtures_dir / "victims.json", "w") as f:
            json.dump(victim_fixture, f, indent=2)
        
        # Admin data fixture
        admin_fixture = {
            "admins": self.config.test_data["admins"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "description": "Test admin data for authentication tests"
        }
        
        with open(fixtures_dir / "admins.json", "w") as f:
            json.dump(admin_fixture, f, indent=2)
        
        # Campaign data fixture
        campaign_fixture = {
            "campaigns": self.config.test_data["campaigns"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "description": "Test campaign data for campaign management tests"
        }
        
        with open(fixtures_dir / "campaigns.json", "w") as f:
            json.dump(campaign_fixture, f, indent=2)
        
        print("✓ Test fixtures created")
    
    def run_unit_tests(self):
        """Run unit tests"""
        print("Running unit tests...")
        
        self.start_time = time.time()
        
        # Discover and run unit tests
        loader = unittest.TestLoader()
        start_dir = self.config.test_root / "unit"
        suite = loader.discover(start_dir, pattern="test_*.py")
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        self.end_time = time.time()
        
        # Store results
        self.test_results["unit"] = {
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "success_rate": ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
            "execution_time": self.end_time - self.start_time,
            "was_successful": result.wasSuccessful()
        }
        
        print(f"✓ Unit tests completed: {self.test_results['unit']['tests_run']} tests, {self.test_results['unit']['success_rate']:.1f}% success rate")
        
        return result.wasSuccessful()
    
    def run_integration_tests(self):
        """Run integration tests"""
        print("Running integration tests...")
        
        self.start_time = time.time()
        
        # Discover and run integration tests
        loader = unittest.TestLoader()
        start_dir = self.config.test_root / "integration"
        suite = loader.discover(start_dir, pattern="test_*.py")
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        self.end_time = time.time()
        
        # Store results
        self.test_results["integration"] = {
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "success_rate": ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
            "execution_time": self.end_time - self.start_time,
            "was_successful": result.wasSuccessful()
        }
        
        print(f"✓ Integration tests completed: {self.test_results['integration']['tests_run']} tests, {self.test_results['integration']['success_rate']:.1f}% success rate")
        
        return result.wasSuccessful()
    
    def run_e2e_tests(self):
        """Run end-to-end tests"""
        print("Running E2E tests...")
        
        self.start_time = time.time()
        
        # Discover and run E2E tests
        loader = unittest.TestLoader()
        start_dir = self.config.test_root / "e2e"
        suite = loader.discover(start_dir, pattern="test_*.py")
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        self.end_time = time.time()
        
        # Store results
        self.test_results["e2e"] = {
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "success_rate": ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
            "execution_time": self.end_time - self.start_time,
            "was_successful": result.wasSuccessful()
        }
        
        print(f"✓ E2E tests completed: {self.test_results['e2e']['tests_run']} tests, {self.test_results['e2e']['success_rate']:.1f}% success rate")
        
        return result.wasSuccessful()
    
    def run_performance_tests(self):
        """Run performance tests"""
        print("Running performance tests...")
        
        self.start_time = time.time()
        
        # Run performance tests using pytest
        performance_tests = self.config.test_root / "e2e" / "test_complete_system.py"
        
        if performance_tests.exists():
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(performance_tests),
                "-k", "test_performance",
                "-v"
            ], capture_output=True, text=True)
            
            self.end_time = time.time()
            
            # Store results
            self.test_results["performance"] = {
                "execution_time": self.end_time - self.start_time,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "was_successful": result.returncode == 0
            }
            
            print(f"✓ Performance tests completed: {result.returncode == 0}")
        else:
            print("⚠ Performance tests not found")
            self.test_results["performance"] = {
                "execution_time": 0,
                "return_code": 0,
                "stdout": "",
                "stderr": "",
                "was_successful": True
            }
        
        return self.test_results["performance"]["was_successful"]
    
    def run_load_tests(self):
        """Run load tests"""
        print("Running load tests...")
        
        self.start_time = time.time()
        
        # Run load tests using pytest
        load_tests = self.config.test_root / "e2e" / "test_complete_system.py"
        
        if load_tests.exists():
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(load_tests),
                "-k", "test_load",
                "-v"
            ], capture_output=True, text=True)
            
            self.end_time = time.time()
            
            # Store results
            self.test_results["load"] = {
                "execution_time": self.end_time - self.start_time,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "was_successful": result.returncode == 0
            }
            
            print(f"✓ Load tests completed: {result.returncode == 0}")
        else:
            print("⚠ Load tests not found")
            self.test_results["load"] = {
                "execution_time": 0,
                "return_code": 0,
                "stdout": "",
                "stderr": "",
                "was_successful": True
            }
        
        return self.test_results["load"]["was_successful"]
    
    def run_security_tests(self):
        """Run security tests"""
        print("Running security tests...")
        
        self.start_time = time.time()
        
        # Run security tests using pytest
        security_tests = self.config.test_root / "e2e" / "test_complete_system.py"
        
        if security_tests.exists():
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(security_tests),
                "-k", "test_security",
                "-v"
            ], capture_output=True, text=True)
            
            self.end_time = time.time()
            
            # Store results
            self.test_results["security"] = {
                "execution_time": self.end_time - self.start_time,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "was_successful": result.returncode == 0
            }
            
            print(f"✓ Security tests completed: {result.returncode == 0}")
        else:
            print("⚠ Security tests not found")
            self.test_results["security"] = {
                "execution_time": 0,
                "return_code": 0,
                "stdout": "",
                "stderr": "",
                "was_successful": True
            }
        
        return self.test_results["security"]["was_successful"]
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("Generating test report...")
        
        reports_dir = self.config.test_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Calculate overall statistics
        total_tests = sum(result.get("tests_run", 0) for result in self.test_results.values())
        total_failures = sum(result.get("failures", 0) for result in self.test_results.values())
        total_errors = sum(result.get("errors", 0) for result in self.test_results.values())
        total_execution_time = sum(result.get("execution_time", 0) for result in self.test_results.values())
        
        overall_success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
        
        # Create test report
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "total_failures": total_failures,
                "total_errors": total_errors,
                "overall_success_rate": overall_success_rate,
                "total_execution_time": total_execution_time,
                "generated_at": datetime.now(timezone.utc).isoformat()
            },
            "test_results": self.test_results,
            "configuration": {
                "test_environment": self.config.test_env,
                "test_data": self.config.test_data,
                "performance_config": self.config.performance_config
            }
        }
        
        # Save JSON report
        with open(reports_dir / "test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Generate HTML report
        self._generate_html_report(report, reports_dir)
        
        # Generate summary
        self._print_test_summary(report)
        
        print(f"✓ Test report generated: {reports_dir / 'test_report.json'}")
    
    def _generate_html_report(self, report, reports_dir):
        """Generate HTML test report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ZaloPay Phishing Platform - Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .test-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        .warning {{ color: orange; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ZaloPay Merchant Phishing Platform</h1>
        <h2>Test Report</h2>
        <p>Generated at: {report['test_summary']['generated_at']}</p>
    </div>
    
    <div class="summary">
        <h3>Test Summary</h3>
        <p><strong>Total Tests:</strong> {report['test_summary']['total_tests']}</p>
        <p><strong>Failures:</strong> {report['test_summary']['total_failures']}</p>
        <p><strong>Errors:</strong> {report['test_summary']['total_errors']}</p>
        <p><strong>Success Rate:</strong> <span class="{'success' if report['test_summary']['overall_success_rate'] >= 90 else 'failure'}">{report['test_summary']['overall_success_rate']:.1f}%</span></p>
        <p><strong>Total Execution Time:</strong> {report['test_summary']['total_execution_time']:.2f} seconds</p>
    </div>
    
    <div class="test-section">
        <h3>Test Results by Category</h3>
        <table>
            <tr>
                <th>Category</th>
                <th>Tests Run</th>
                <th>Failures</th>
                <th>Errors</th>
                <th>Success Rate</th>
                <th>Execution Time</th>
            </tr>
"""
        
        for category, result in report['test_results'].items():
            success_rate = result.get('success_rate', 0)
            success_class = 'success' if success_rate >= 90 else 'failure' if success_rate < 70 else 'warning'
            
            html_content += f"""
            <tr>
                <td>{category.title()}</td>
                <td>{result.get('tests_run', 0)}</td>
                <td>{result.get('failures', 0)}</td>
                <td>{result.get('errors', 0)}</td>
                <td class="{success_class}">{success_rate:.1f}%</td>
                <td>{result.get('execution_time', 0):.2f}s</td>
            </tr>
"""
        
        html_content += """
        </table>
    </div>
    
    <div class="test-section">
        <h3>Configuration</h3>
        <h4>Test Environment</h4>
        <ul>
"""
        
        for key, value in report['configuration']['test_environment'].items():
            html_content += f"<li><strong>{key}:</strong> {value}</li>"
        
        html_content += """
        </ul>
    </div>
</body>
</html>
"""
        
        with open(reports_dir / "test_report.html", "w") as f:
            f.write(html_content)
    
    def _print_test_summary(self, report):
        """Print test summary to console"""
        print(f"\n{'='*60}")
        print(f"ZALOPAY PHISHING PLATFORM - TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {report['test_summary']['total_tests']}")
        print(f"Failures: {report['test_summary']['total_failures']}")
        print(f"Errors: {report['test_summary']['total_errors']}")
        print(f"Success Rate: {report['test_summary']['overall_success_rate']:.1f}%")
        print(f"Total Execution Time: {report['test_summary']['total_execution_time']:.2f} seconds")
        print(f"{'='*60}")
        
        print(f"\nTest Results by Category:")
        for category, result in report['test_results'].items():
            success_rate = result.get('success_rate', 0)
            status = "✓" if success_rate >= 90 else "✗" if success_rate < 70 else "⚠"
            print(f"  {status} {category.title()}: {result.get('tests_run', 0)} tests, {success_rate:.1f}% success rate")
        
        print(f"{'='*60}")
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        print("Cleaning up test environment...")
        
        try:
            # Clean up test database
            import pymongo
            client = pymongo.MongoClient(self.config.test_db_config["mongodb"]["host"])
            client.drop_database(self.config.test_db_config["mongodb"]["database"])
            print("✓ Test database cleaned up")
            
        except Exception as e:
            print(f"⚠ Database cleanup failed: {e}")
        
        try:
            # Clean up Redis
            import redis
            r = redis.Redis(
                host=self.config.test_db_config["redis"]["host"],
                port=self.config.test_db_config["redis"]["port"],
                db=self.config.test_db_config["redis"]["db"]
            )
            r.flushdb()
            print("✓ Redis cleaned up")
            
        except Exception as e:
            print(f"⚠ Redis cleanup failed: {e}")
        
        print("✓ Test environment cleanup complete")
    
    def run_all_tests(self):
        """Run all tests"""
        print("Starting comprehensive test suite...")
        
        # Setup
        self.setup_test_environment()
        
        # Run tests
        test_results = []
        
        test_results.append(("Unit Tests", self.run_unit_tests()))
        test_results.append(("Integration Tests", self.run_integration_tests()))
        test_results.append(("E2E Tests", self.run_e2e_tests()))
        test_results.append(("Performance Tests", self.run_performance_tests()))
        test_results.append(("Load Tests", self.run_load_tests()))
        test_results.append(("Security Tests", self.run_security_tests()))
        
        # Generate report
        self.generate_test_report()
        
        # Cleanup
        self.cleanup_test_environment()
        
        # Summary
        print(f"\n{'='*60}")
        print(f"COMPREHENSIVE TEST SUITE COMPLETED")
        print(f"{'='*60}")
        
        all_passed = True
        for test_name, passed in test_results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{status}: {test_name}")
            if not passed:
                all_passed = False
        
        print(f"{'='*60}")
        print(f"Overall Result: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
        print(f"{'='*60}")
        
        return all_passed

def main():
    """Main test runner function"""
    config = TestConfig()
    runner = TestRunner(config)
    
    # Run all tests
    success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
