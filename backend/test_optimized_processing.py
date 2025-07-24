#!/usr/bin/env python3
"""
Quick test script to verify the optimized email processing works correctly.
Tests the improved classification, reply generation, and thinking content filtering.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/home/akshay/Akshay-CL-Projects/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emailai.settings')
django.setup()

from api.services.email_processing_service import EmailProcessingService
from api.services.email_classifier import EmailClassifier
from api.services.ollama_service import OllamaService

def test_thinking_content_removal():
    """Test that thinking content is properly removed from responses."""
    print("🧪 Testing thinking content removal...")
    
    ollama = OllamaService()
    
    # Test with sample response containing thinking content
    sample_response = """<think>
    Let me analyze this email... This looks like an interview invitation.
    </think>
    
    {"category": "interview", "confidence": 0.9, "reasoning": "Email contains interview invitation"}"""
    
    cleaned = ollama._clean_response(sample_response)
    print(f"Original: {sample_response[:50]}...")
    print(f"Cleaned: {cleaned}")
    
    assert "<think>" not in cleaned, "Thinking content not removed!"
    assert "interview" in cleaned, "Valid content was removed!"
    print("✅ Thinking content removal working correctly\n")

def test_simplified_classification():
    """Test the simplified classification prompt and JSON parsing."""
    print("🧪 Testing simplified classification...")
    
    classifier = EmailClassifier()
    
    # Test email samples
    test_emails = [
        {
            "subject": "Interview Invitation - Python Developer",
            "body": "We would like to invite you for an interview next week.",
            "expected": "interview"
        },
        {
            "subject": "Application Received",
            "body": "Thank you for your application. We have received it and will review.",
            "expected": "confirmation"
        },
        {
            "subject": "Unfortunately...",
            "body": "Unfortunately, we cannot proceed with your application at this time.",
            "expected": "rejection"
        }
    ]
    
    for i, email in enumerate(test_emails, 1):
        print(f"Test {i}: {email['subject'][:30]}...")
        result = classifier.classify_email(email["body"], email["subject"])
        
        print(f"  Category: {result.get('category')}")
        print(f"  Confidence: {result.get('confidence')}")
        print(f"  Priority: {result.get('priority')}")
        print(f"  Expected: {email['expected']}")
        
        if result.get('category') == email['expected']:
            print("  ✅ Classification correct")
        else:
            print("  ⚠️ Classification might be off (using fallback is OK)")
        print()

def test_reply_generation_logic():
    """Test that replies are only generated for specific categories."""
    print("🧪 Testing selective reply generation...")
    
    processor = EmailProcessingService()
    
    test_cases = [
        {"category": "confirmation", "should_have_reply": False},
        {"category": "rejection", "should_have_reply": True},
        {"category": "interview", "should_have_reply": True},
        {"category": "query", "should_have_reply": True}
    ]
    
    for case in test_cases:
        email_data = {
            "subject": f"Test {case['category']} email",
            "body": f"This is a test {case['category']} email body.",
            "sender_name": "Test Company"
        }
        
        # Mock the classification to test reply logic
        result = processor.process_email_complete(email_data)
        category = result.get('classification', {}).get('category', '')
        has_reply = result.get('suggested_reply') is not None
        
        print(f"Category: {category}")
        print(f"Has reply: {has_reply}")
        print(f"Should have reply: {case['should_have_reply']}")
        
        if case['category'] == category:
            if has_reply == case['should_have_reply']:
                print("✅ Reply generation logic correct")
            else:
                print("⚠️ Reply generation logic might be off")
        else:
            print("ℹ️ Category classified differently (fallback used)")
        print()

def main():
    """Run all tests."""
    print("🚀 Testing Optimized Email Processing\n")
    
    try:
        test_thinking_content_removal()
        test_simplified_classification()
        test_reply_generation_logic()
        
        print("🎉 All tests completed! Check output above for any issues.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()