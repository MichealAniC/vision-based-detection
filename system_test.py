#!/usr/bin/env python3
"""
System Functionality Test Script
Tests all major endpoints and functionality of the Face Recognition Attendance System
"""

import requests
import time
import sys

def test_endpoint(url, endpoint, method='GET', expected_status=200, data=None):
    """Test a specific endpoint"""
    try:
        full_url = f"{url}{endpoint}"
        print(f"Testing {method} {full_url}...")
        
        if method == 'GET':
            response = requests.get(full_url, timeout=10)
        elif method == 'POST':
            response = requests.post(full_url, data=data, timeout=10)
        
        if response.status_code == expected_status:
            print(f"✅ {endpoint} - Status: {response.status_code}")
            return True
        else:
            print(f"❌ {endpoint} - Status: {response.status_code}, Expected: {expected_status}")
            return False
    except Exception as e:
        print(f"❌ {endpoint} - Error: {str(e)}")
        return False

def main():
    # Test against the deployed application
    base_url = "https://face-reg.onrender.com"
    
    print(f"🧪 Testing Face Recognition Attendance System at {base_url}")
    print("=" * 60)
    
    # Test basic endpoints
    endpoints_to_test = [
        ('/', 'GET', 200),
        ('/login', 'GET', 200),
        ('/register', 'GET', 200),
        ('/privacy', 'GET', 200),
        ('/help', 'GET', 200),
    ]
    
    all_passed = True
    
    for endpoint, method, expected_status in endpoints_to_test:
        result = test_endpoint(base_url, endpoint, method, expected_status)
        if not result:
            all_passed = False
        time.sleep(0.5)  # Small delay between requests
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("🎉 All basic endpoints are working correctly!")
        print("\n📋 System Status:")
        print("✅ Landing page accessible")
        print("✅ Login page accessible") 
        print("✅ Registration page accessible")
        print("✅ Privacy policy accessible")
        print("✅ Help page accessible")
        print("\n🚀 The system appears to be functioning properly!")
        print("📱 You can now test camera functionality in the browser")
    else:
        print("⚠️  Some endpoints failed. Please check the deployment.")
    
    print("\n📝 Next Steps:")
    print("1. Visit https://face-reg.onrender.com in your browser")
    print("2. Test the registration flow with camera access")
    print("3. Verify attendance marking functionality")
    print("4. Check that enhanced error handling works")

if __name__ == "__main__":
    main()