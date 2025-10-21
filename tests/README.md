# Testing Documentation for ZaloPay Merchant Phishing Platform

## Overview

This document provides comprehensive information about the testing framework for the ZaloPay Merchant Phishing Platform. The testing suite includes unit tests, integration tests, end-to-end tests, performance tests, load tests, and security tests.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   └── test_core_modules.py
├── integration/             # Integration tests for workflows
│   └── test_workflows.py
├── e2e/                     # End-to-end tests for complete system
│   └── test_complete_system.py
├── fixtures/                # Test data and fixtures
│   ├── victims.json
│   ├── admins.json
│   └── campaigns.json
├── reports/                 # Test reports and coverage
│   ├── test_report.json
│   ├── test_report.html
│   └── coverage_html/
├── requirements.txt         # Test dependencies
└── test_runner.py          # Main test runner
```

## Test Categories

### 1. Unit Tests

**Purpose**: Test individual components in isolation

**Location**: `tests/unit/`

**Coverage**:
- Proxy management system
- Device fingerprinting engine
- Encryption manager
- OAuth services (Google, Apple, Facebook)
- Credential validation pipeline
- Gmail API client
- BeEF API client
- WebSocket manager
- Machine learning components
- Advanced exploitation modules

**Example**:
```python
def test_proxy_assignment(self):
    """Test proxy assignment for victim"""
    victim_id = "test_victim_1"
    assigned_proxy = self.proxy_manager.assign_proxy_for_victim(victim_id)
    
    self.assertIsNotNone(assigned_proxy)
    self.assertIn("proxy_id", assigned_proxy)
    self.assertIn("host", assigned_proxy)
    self.assertIn("port", assigned_proxy)
```

### 2. Integration Tests

**Purpose**: Test component interactions and workflows

**Location**: `tests/integration/`

**Coverage**:
- Victim capture workflow
- OAuth flow integration
- Gmail exploitation workflow
- BeEF exploitation workflow
- WebSocket real-time workflow
- Machine learning workflow
- Advanced exploitation workflow
- End-to-end workflow

**Example**:
```python
def test_complete_victim_capture_workflow(self):
    """Test complete victim capture workflow"""
    victim_id = self.test_victim_data["victim_id"]
    
    # Step 1: Assign proxy for victim
    proxy = self.proxy_manager.assign_proxy_for_victim(victim_id)
    self.assertIsNotNone(proxy)
    
    # Step 2: Process device fingerprint
    fingerprint_result = self.fingerprint_engine.process_fingerprint_data(
        self.test_victim_data["fingerprint_data"]
    )
    self.assertIsNotNone(fingerprint_result)
    
    # Step 3: Validate credentials
    validation_result = self.validation_pipeline.validate_credential(credential_data)
    self.assertIsNotNone(validation_result)
    
    # Step 4: Encrypt and store victim data
    encrypted_data = self.encryption_manager.encrypt_data(sensitive_data)
    self.assertIsNotNone(encrypted_data)
```

### 3. End-to-End Tests

**Purpose**: Test complete system functionality from user perspective

**Location**: `tests/e2e/`

**Coverage**:
- Victim landing page functionality
- OAuth flow end-to-end
- Admin dashboard end-to-end
- Victim database end-to-end
- Campaign management end-to-end
- API endpoints end-to-end
- WebSocket real-time functionality
- Security features end-to-end
- Performance end-to-end

**Example**:
```python
def test_victim_landing_page(self):
    """Test victim landing page functionality"""
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
        
        # Check for key elements
        login_form = self.driver.find_element(By.ID, "loginForm")
        self.assertIsNotNone(login_form)
```

### 4. Performance Tests

**Purpose**: Test system performance under various conditions

**Coverage**:
- API response times
- Database query performance
- Concurrent request handling
- Memory usage
- CPU usage
- Load testing

**Example**:
```python
def test_performance_e2e(self):
    """Test performance end-to-end"""
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
```

### 5. Load Tests

**Purpose**: Test system behavior under high load

**Coverage**:
- Concurrent victim captures
- API load testing
- Database load testing
- WebSocket load testing
- Memory and CPU usage under load

**Example**:
```python
def test_concurrent_victim_captures(self):
    """Test concurrent victim captures"""
    import concurrent.futures
    
    def capture_victim(victim_id):
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
    print(f"  - Success rate: {(successful_captures/num_victims)*100:.1f}%")
```

### 6. Security Tests

**Purpose**: Test security features and vulnerabilities

**Coverage**:
- Encryption/decryption functionality
- Authentication mechanisms
- Authorization controls
- Input validation
- SQL injection prevention
- XSS prevention
- CSRF protection
- Rate limiting
- Security headers

**Example**:
```python
def test_security_features_e2e(self):
    """Test security features end-to-end"""
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
        
        # Test decryption
        decrypt_response = requests.post(
            f"{self.base_url}/api/security/decrypt",
            json=encrypted_data
        )
        
        if decrypt_response.status_code == 200:
            decrypted_data = decrypt_response.json()
            self.assertEqual(decrypted_data["data"], test_data)
```

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
pip install -r tests/requirements.txt
```

2. Set up test environment:
```bash
export MONGODB_URI="mongodb://localhost:27017/zalopay_test"
export REDIS_URL="redis://localhost:6379/0"
export INFLUXDB_URL="http://localhost:8086"
export BEEF_URL="http://localhost:3000"
export ENVIRONMENT="test"
export LOG_LEVEL="DEBUG"
export TEST_MODE="true"
```

3. Start required services:
```bash
# MongoDB
mongod --dbpath /path/to/test/db

# Redis
redis-server

# InfluxDB
influxd

# BeEF (optional for E2E tests)
cd beef_framework && ./beef
```

### Running All Tests

```bash
# Run comprehensive test suite
python tests/test_runner.py

# Or using pytest
pytest tests/ -v --tb=short
```

### Running Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v

# Performance tests only
pytest tests/e2e/ -k "test_performance" -v

# Load tests only
pytest tests/e2e/ -k "test_load" -v

# Security tests only
pytest tests/e2e/ -k "test_security" -v
```

### Running with Coverage

```bash
# Run tests with coverage
pytest tests/ --cov=backend --cov-report=html --cov-report=term

# Generate coverage badge
coverage-badge -o tests/reports/coverage.svg
```

### Running in Parallel

```bash
# Run tests in parallel
pytest tests/ -n auto

# Run with specific number of workers
pytest tests/ -n 4
```

## Test Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017/zalopay_test` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `INFLUXDB_URL` | InfluxDB connection string | `http://localhost:8086` |
| `BEEF_URL` | BeEF framework URL | `http://localhost:3000` |
| `ENVIRONMENT` | Environment name | `test` |
| `LOG_LEVEL` | Logging level | `DEBUG` |
| `TEST_MODE` | Enable test mode | `true` |

### Test Data

Test data is stored in `tests/fixtures/` directory:

- `victims.json`: Test victim data
- `admins.json`: Test admin data
- `campaigns.json`: Test campaign data

### Performance Thresholds

| Metric | Threshold | Description |
|--------|-----------|-------------|
| API Response Time | < 2.0s | Maximum API response time |
| Database Query Time | < 1.0s | Maximum database query time |
| Concurrent Users | 100 | Maximum concurrent users |
| Memory Usage | < 512MB | Maximum memory usage |
| CPU Usage | < 80% | Maximum CPU usage |

## Test Reports

### JSON Report

Comprehensive test results in JSON format:
```json
{
  "test_summary": {
    "total_tests": 150,
    "total_failures": 2,
    "total_errors": 1,
    "overall_success_rate": 98.0,
    "total_execution_time": 45.2,
    "generated_at": "2024-01-15T10:30:00Z"
  },
  "test_results": {
    "unit": {
      "tests_run": 50,
      "failures": 0,
      "errors": 0,
      "success_rate": 100.0,
      "execution_time": 12.5
    },
    "integration": {
      "tests_run": 40,
      "failures": 1,
      "errors": 0,
      "success_rate": 97.5,
      "execution_time": 18.3
    },
    "e2e": {
      "tests_run": 30,
      "failures": 1,
      "errors": 1,
      "success_rate": 93.3,
      "execution_time": 14.4
    }
  }
}
```

### HTML Report

Visual test report with charts and detailed results:
- Test summary dashboard
- Results by category
- Performance metrics
- Coverage information
- Configuration details

### Coverage Report

Code coverage analysis:
- Line coverage
- Branch coverage
- Function coverage
- Class coverage
- HTML coverage report
- Coverage badge

## Continuous Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mongodb:
        image: mongo:4.4
        ports:
          - 27017:27017
      redis:
        image: redis:6.2
        ports:
          - 6379:6379
      influxdb:
        image: influxdb:1.8
        ports:
          - 8086:8086
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r tests/requirements.txt
    
    - name: Run tests
      run: python tests/test_runner.py
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: tests/reports/coverage.xml
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pip install -r tests/requirements.txt'
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh 'pytest tests/unit/ -v --cov=backend --cov-report=xml'
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh 'pytest tests/integration/ -v'
            }
        }
        
        stage('E2E Tests') {
            steps {
                sh 'pytest tests/e2e/ -v'
            }
        }
        
        stage('Performance Tests') {
            steps {
                sh 'pytest tests/e2e/ -k "test_performance" -v'
            }
        }
        
        stage('Security Tests') {
            steps {
                sh 'pytest tests/e2e/ -k "test_security" -v'
            }
        }
    }
    
    post {
        always {
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'tests/reports',
                reportFiles: 'test_report.html',
                reportName: 'Test Report'
            ])
        }
    }
}
```

## Best Practices

### Test Writing

1. **Test Naming**: Use descriptive test names that explain what is being tested
2. **Test Structure**: Follow Arrange-Act-Assert pattern
3. **Test Isolation**: Each test should be independent and not rely on other tests
4. **Test Data**: Use realistic test data that reflects production scenarios
5. **Mocking**: Mock external dependencies to ensure test reliability

### Test Maintenance

1. **Regular Updates**: Keep tests updated with code changes
2. **Test Coverage**: Maintain high test coverage (>80%)
3. **Performance Monitoring**: Monitor test execution time and optimize slow tests
4. **Test Data Management**: Keep test data clean and up-to-date
5. **Documentation**: Document test scenarios and expected behavior

### Test Execution

1. **Parallel Execution**: Use parallel test execution for faster feedback
2. **Test Selection**: Run relevant tests based on code changes
3. **Environment Management**: Use isolated test environments
4. **Resource Cleanup**: Clean up test resources after execution
5. **Error Handling**: Handle test failures gracefully

## Troubleshooting

### Common Issues

1. **Database Connection Issues**:
   - Ensure MongoDB, Redis, and InfluxDB are running
   - Check connection strings and ports
   - Verify database permissions

2. **WebDriver Issues**:
   - Install ChromeDriver or use webdriver-manager
   - Check browser compatibility
   - Verify headless mode configuration

3. **Test Timeout Issues**:
   - Increase timeout values for slow tests
   - Optimize test performance
   - Use test markers to categorize slow tests

4. **Memory Issues**:
   - Monitor memory usage during tests
   - Clean up test data and resources
   - Use smaller test datasets

5. **Network Issues**:
   - Check network connectivity
   - Verify service URLs and ports
   - Use mock services for external dependencies

### Debug Mode

Enable debug mode for detailed test information:

```bash
export LOG_LEVEL=DEBUG
export TEST_MODE=true
pytest tests/ -v -s --tb=long
```

### Test Logs

Test logs are available in:
- Console output during test execution
- `tests/reports/test_report.json` for structured results
- `tests/reports/test_report.html` for visual reports

## Conclusion

The comprehensive testing framework for the ZaloPay Merchant Phishing Platform provides:

- **Complete Coverage**: Unit, integration, E2E, performance, load, and security tests
- **Automated Execution**: Automated test runner with comprehensive reporting
- **CI/CD Integration**: Ready for continuous integration and deployment
- **Performance Monitoring**: Performance thresholds and load testing
- **Security Validation**: Security feature testing and vulnerability assessment
- **Documentation**: Comprehensive documentation and best practices

This testing framework ensures the platform's reliability, performance, and security while providing developers with fast feedback on code changes.
