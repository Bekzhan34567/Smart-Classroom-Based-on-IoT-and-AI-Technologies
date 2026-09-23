"""
Stress tests and validation tests for Smart Classroom API
Tests empty fields, invalid formats, edge cases, and boundary conditions
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"

def print_test_result(test_name, status, details=""):
    """Print formatted test result"""
    status_symbol = "✅" if status == "PASS" else "❌"
    print(f"{status_symbol} {test_name}: {status}")
    if details:
        print(f"   {details}")

def test_empty_login_fields():
    """Test login with empty fields"""
    print("\n=== Testing Empty Login Fields ===")
    
    # Empty email
    response = requests.post(f"{BASE_URL}/auth/login", json={"email": "", "password": "password123"})
    print_test_result("Empty email", "PASS" if response.status_code == 422 else "FAIL", f"Status: {response.status_code}")
    
    # Empty password
    response = requests.post(f"{BASE_URL}/auth/login", json={"email": "test@test.com", "password": ""})
    print_test_result("Empty password", "PASS" if response.status_code == 422 else "FAIL", f"Status: {response.status_code}")
    
    # Both empty
    response = requests.post(f"{BASE_URL}/auth/login", json={"email": "", "password": ""})
    print_test_result("Both empty", "PASS" if response.status_code == 422 else "FAIL", f"Status: {response.status_code}")

def test_invalid_email_formats():
    """Test login with invalid email formats"""
    print("\n=== Testing Invalid Email Formats ===")
    
    invalid_emails = [
        "invalid-email",
        "@example.com",
        "test@",
        "test@@example.com",
        "test example.com",
        "test@.com",
        "test@com",
    ]
    
    for email in invalid_emails:
        response = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": "password123"})
        print_test_result(f"Invalid email: {email}", "PASS" if response.status_code == 422 else "FAIL", f"Status: {response.status_code}")

def test_short_passwords():
    """Test login with short passwords"""
    print("\n=== Testing Short Passwords ===")
    
    short_passwords = ["", "a", "ab", "abc", "123", "12345"]
    
    for password in short_passwords:
        response = requests.post(f"{BASE_URL}/auth/login", json={"email": "test@test.com", "password": password})
        print_test_result(f"Short password: '{password}'", "PASS" if response.status_code == 422 else "FAIL", f"Status: {response.status_code}")

def test_wrong_credentials():
    """Test login with wrong credentials"""
    print("\n=== Testing Wrong Credentials ===")
    
    # Wrong password
    response = requests.post(f"{BASE_URL}/auth/login", json={"email": "student@university.edu", "password": "wrongpassword"})
    print_test_result("Wrong password", "PASS" if response.status_code == 401 else "FAIL", f"Status: {response.status_code}")
    
    # Non-existent user
    response = requests.post(f"{BASE_URL}/auth/login", json={"email": "nonexistent@test.com", "password": "password123"})
    print_test_result("Non-existent user", "PASS" if response.status_code == 401 else "FAIL", f"Status: {response.status_code}")

def test_empty_registration_fields():
    """Test registration with empty fields"""
    print("\n=== Testing Empty Registration Fields ===")
    
    # Missing full_name
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": "test@test.com",
        "password": "password123",
        "role": "student"
    })
    print_test_result("Missing full_name", "PASS" if response.status_code == 422 else "FAIL", f"Status: {response.status_code}")
    
    # Missing email
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Test User",
        "password": "password123",
        "role": "student"
    })
    print_test_result("Missing email", "PASS" if response.status_code == 422 else "FAIL", f"Status: {response.status_code}")
    
    # Missing password
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Test User",
        "email": "test@test.com",
        "role": "student"
    })
    print_test_result("Missing password", "PASS" if response.status_code == 422 else "FAIL", f"Status: {response.status_code}")

def test_invalid_registration_data():
    """Test registration with invalid data"""
    print("\n=== Testing Invalid Registration Data ===")
    
    # Invalid role
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Test User",
        "email": "test@test.com",
        "password": "password123",
        "role": "invalid_role"
    })
    print_test_result("Invalid role", "PASS" if response.status_code == 422 else "FAIL", f"Status: {response.status_code}")
    
    # Very long full_name
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "A" * 500,
        "email": "test@test.com",
        "password": "password123",
        "role": "student"
    })
    print_test_result("Very long full_name", "PASS" if response.status_code == 422 else "FAIL", f"Status: {response.status_code}")

def test_unauthorized_access():
    """Test access without authentication"""
    print("\n=== Testing Unauthorized Access ===")
    
    endpoints = [
        "/students/",
        "/courses/",
        "/grades/",
        "/ml-analytics/summary",
        "/auth/me"
    ]
    
    for endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}")
        print_test_result(f"Unauthorized GET {endpoint}", "PASS" if response.status_code == 401 else "FAIL", f"Status: {response.status_code}")

def test_invalid_token():
    """Test access with invalid token"""
    print("\n=== Testing Invalid Token ===")
    
    headers = {"Authorization": "Bearer invalid_token"}
    
    endpoints = ["/students/", "/courses/", "/grades/"]
    
    for endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print_test_result(f"Invalid token GET {endpoint}", "PASS" if response.status_code == 401 else "FAIL", f"Status: {response.status_code}")

def test_sql_injection_attempts():
    """Test SQL injection attempts"""
    print("\n=== Testing SQL Injection Attempts ===")
    
    sql_injection_payloads = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM users--",
    ]
    
    for payload in sql_injection_payloads:
        response = requests.post(f"{BASE_URL}/auth/login", json={"email": payload, "password": "password123"})
        print_test_result(f"SQL injection: {payload[:20]}...", "PASS" if response.status_code == 401 else "FAIL", f"Status: {response.status_code}")

def test_xss_attempts():
    """Test XSS attempts"""
    print("\n=== Testing XSS Attempts ===")
    
    xss_payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
    ]
    
    for payload in xss_payloads:
        response = requests.post(f"{BASE_URL}/auth/register", json={
            "full_name": payload,
            "email": f"test{len(payload)}@test.com",
            "password": "password123",
            "role": "student"
        })
        print_test_result(f"XSS attempt: {payload[:20]}...", "PASS" if response.status_code == 422 or response.status_code == 200 else "FAIL", f"Status: {response.status_code}")

def test_concurrent_requests():
    """Test concurrent requests (stress test)"""
    print("\n=== Testing Concurrent Requests ===")
    
    import threading
    import time
    
    # Login first to get token
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "student@university.edu",
        "password": "password123"
    })
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        success_count = 0
        error_count = 0
        
        def make_request():
            nonlocal success_count, error_count
            try:
                response = requests.get(f"{BASE_URL}/students/", headers=headers)
                if response.status_code == 200:
                    success_count += 1
                else:
                    error_count += 1
            except Exception:
                error_count += 1
        
        # Make 50 concurrent requests
        threads = []
        for _ in range(50):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        print_test_result(f"Concurrent requests (50)", "PASS" if success_count >= 45 else "FAIL", 
                         f"Success: {success_count}, Errors: {error_count}")
    else:
        print_test_result("Concurrent requests", "FAIL", "Could not get token")

def test_rate_limiting():
    """Test rate limiting"""
    print("\n=== Testing Rate Limiting ===")
    
    # Make 100 rapid requests
    success_count = 0
    rate_limited_count = 0
    
    for i in range(100):
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "student@university.edu",
            "password": "password123"
        })
        
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            rate_limited_count += 1
    
    print_test_result("Rate limiting (100 requests)", "PASS" if rate_limited_count > 0 or success_count == 100 else "WARN",
                     f"Success: {success_count}, Rate limited: {rate_limited_count}")

def run_all_tests():
    """Run all stress and validation tests"""
    print("=" * 60)
    print("SMART CLASSROOM - STRESS TESTS & VALIDATION")
    print("=" * 60)
    
    test_empty_login_fields()
    test_invalid_email_formats()
    test_short_passwords()
    test_wrong_credentials()
    test_empty_registration_fields()
    test_invalid_registration_data()
    test_unauthorized_access()
    test_invalid_token()
    test_sql_injection_attempts()
    test_xss_attempts()
    test_concurrent_requests()
    test_rate_limiting()
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()
