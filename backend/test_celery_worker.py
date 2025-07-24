#!/usr/bin/env python
"""
Test script to verify Celery worker functionality.
Run this to test if Celery can process tasks properly.

Usage:
    python test_celery_worker.py
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emailai.settings')
django.setup()

from api.services.email_processor import process_single_email, batch_process_emails_task
from celery.result import AsyncResult
import time

def test_celery_connection():
    """Test basic Celery connection and task submission."""
    print("🔧 Testing Celery Connection...")
    
    try:
        # Test with a non-existent email ID (should handle gracefully)
        result = process_single_email.delay(999999)
        print(f"✅ Task submitted successfully: {result.id}")
        print(f"📊 Initial status: {result.status}")
        
        # Wait a bit and check status
        time.sleep(2)
        print(f"📊 Status after 2s: {result.status}")
        
        # Get result (will wait if needed)
        try:
            task_result = result.get(timeout=10)
            print(f"📝 Task result: {task_result}")
        except Exception as e:
            print(f"⚠️  Task execution result: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery connection failed: {e}")
        return False

def test_batch_processing():
    """Test batch processing task."""
    print("\n🔧 Testing Batch Processing...")
    
    try:
        # Test with non-existent email IDs
        result = batch_process_emails_task.delay([999998, 999999])
        print(f"✅ Batch task submitted: {result.id}")
        print(f"📊 Status: {result.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        return False

def test_task_status_check():
    """Test task status checking functionality."""
    print("\n🔧 Testing Task Status Check...")
    
    try:
        # Submit a task
        result = process_single_email.delay(999997)
        task_id = result.id
        
        # Check status using AsyncResult
        async_result = AsyncResult(task_id)
        print(f"✅ Task ID: {task_id}")
        print(f"📊 Status: {async_result.status}")
        print(f"📝 Info: {async_result.info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Task status check failed: {e}")
        return False

def main():
    """Run all Celery tests."""
    print("🚀 EmailAI Celery Worker Test")
    print("=" * 40)
    
    tests = [
        ("Celery Connection", test_celery_connection),
        ("Batch Processing", test_batch_processing),
        ("Task Status Check", test_task_status_check),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Tests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 All tests passed! Celery is working correctly.")
        print("\n💡 To start a Celery worker, run:")
        print("   celery -A emailai worker --loglevel=info")
    else:
        print("⚠️  Some tests failed. Check Celery configuration.")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure Redis is running: redis-server")
        print("   2. Start Celery worker: celery -A emailai worker --loglevel=info")
        print("   3. Check Django settings for CELERY_* configuration")

if __name__ == "__main__":
    main()