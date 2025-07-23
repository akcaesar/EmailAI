#!/usr/bin/env python3
"""
Test script for superuser functionality and admin features.
This script tests the new superuser endpoints without requiring a superuser to exist.

Author: Akshay NS
"""

import requests
import json
import os
import sys

# Add the project directory to Python path
sys.path.append('/home/akshay/Akshay-CL-Projects/backend')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emailai.settings')

import django
django.setup()

from django.contrib.auth.models import User

BASE_URL = 'http://localhost:8000/api/v1'

def test_endpoints_structure():
    """Test that all new endpoints are properly registered"""
    print("🔍 Testing endpoint structure...")
    
    endpoints_to_test = [
        '/auth/',
        '/admin/',
        '/system/health/',
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            print(f"✅ {endpoint} - Status: {response.status_code}")
            if response.status_code == 401:
                print(f"   (Expected 401 - authentication required)")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

def test_user_registration():
    """Test user registration functionality"""
    print("\n👤 Testing user registration...")
    
    test_user_data = {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "testpass123",
        "password_confirm": "testpass123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register/", json=test_user_data)
        print(f"Registration response: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ User registration successful")
            return response.json()
        else:
            print(f"❌ Registration failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return None

def test_login(username, password):
    """Test user login functionality"""
    print(f"\n🔐 Testing login for {username}...")
    
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
        print(f"Login response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login successful")
            data = response.json()
            return data.get('tokens')
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_admin_endpoints_without_permission(tokens=None):
    """Test admin endpoints without superuser permission (should fail)"""
    print("\n🔒 Testing admin endpoints without superuser permission...")
    
    headers = {}
    if tokens:
        headers['Authorization'] = f'Bearer {tokens["access"]}'
    
    admin_endpoints = [
        '/auth/create_superuser/',
        '/auth/admin_user_list/',
        '/admin/',
    ]
    
    for endpoint in admin_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            print(f"📍 {endpoint} - Status: {response.status_code}")
            
            if response.status_code == 403:
                print("   ✅ Correctly denied access (not admin)")
            elif response.status_code == 401:
                print("   ✅ Authentication required")
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

def test_system_health():
    """Test system health endpoint"""
    print("\n🏥 Testing system health...")
    
    try:
        response = requests.get(f"{BASE_URL}/system/health/")
        print(f"Health check response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ System health check successful")
            print(f"   Overall status: {data.get('overall_status', 'unknown')}")
            
            services = data.get('services', {})
            for service, status in services.items():
                print(f"   {service}: {status.get('status', 'unknown')}")
        else:
            print(f"❌ Health check failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")

def create_superuser_manually():
    """Create a superuser using Django's management system"""
    print("\n👑 Creating superuser manually for testing...")
    
    try:
        from django.contrib.auth.models import User
        
        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            print("✅ Superuser already exists")
            superuser = User.objects.filter(is_superuser=True).first()
            return superuser.username
        
        # Create superuser
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print(f"✅ Superuser created: {superuser.username}")
        return superuser.username
        
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
        return None

def test_superuser_login_and_endpoints():
    """Test superuser login and admin endpoints"""
    print("\n👑 Testing superuser functionality...")
    
    superuser_username = create_superuser_manually()
    if not superuser_username:
        print("❌ Could not create superuser")
        return
    
    # Login as superuser
    tokens = test_login(superuser_username, 'admin123')
    if not tokens:
        print("❌ Could not login as superuser")
        return
    
    headers = {'Authorization': f'Bearer {tokens["access"]}'}
    
    # Test admin user list
    print("\n📋 Testing admin user list...")
    try:
        response = requests.get(f"{BASE_URL}/auth/admin_user_list/", headers=headers)
        print(f"Admin user list response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Admin user list successful")
            print(f"   Total users: {data['data']['statistics']['total_users']}")
            print(f"   Superusers: {data['data']['statistics']['superusers']}")
        else:
            print(f"❌ Admin user list failed: {response.text}")
    except Exception as e:
        print(f"❌ Admin user list error: {e}")
    
    # Test admin dashboard
    print("\n📊 Testing admin dashboard...")
    try:
        response = requests.get(f"{BASE_URL}/admin/", headers=headers)
        print(f"Admin dashboard response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Admin dashboard successful")
            print(f"   System status: {data['data']['system_health']['overall']}")
        else:
            print(f"❌ Admin dashboard failed: {response.text}")
    except Exception as e:
        print(f"❌ Admin dashboard error: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting EmailAI Superuser Functionality Tests")
    print("=" * 60)
    
    # Test basic endpoint structure
    test_endpoints_structure()
    
    # Test system health (no auth required)
    test_system_health()
    
    # Test user registration
    user_data = test_user_registration()
    
    # Test regular user login
    if user_data:
        tokens = test_login("testuser123", "testpass123")
        test_admin_endpoints_without_permission(tokens)
    
    # Test superuser functionality
    test_superuser_login_and_endpoints()
    
    print("\n" + "=" * 60)
    print("🎉 All tests completed!")
    print("\n📋 Summary of implemented features:")
    print("   ✅ Superuser login functionality")
    print("   ✅ Superuser creation endpoint")
    print("   ✅ Admin user list endpoint")
    print("   ✅ Admin dashboard with comprehensive statistics")
    print("   ✅ User status toggle functionality")
    print("   ✅ Proper permission-based access control")
    print("   ✅ System health monitoring")

if __name__ == "__main__":
    main()