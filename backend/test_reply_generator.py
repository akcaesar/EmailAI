"""
Test script for reply generator improvements.
Tests the enhanced reply generation with better AI response cleaning.
"""

import sys
import os
sys.path.append('/home/akshay/Akshay-CL-Projects/backend')

from api.services.reply_generator import ReplyGenerator
from api.services.ollama_service import OllamaService

def test_reply_generation():
    """Test reply generation with various email scenarios."""
    
    print("🧪 Testing Enhanced Reply Generator")
    print("=" * 50)
    
    # Initialize the reply generator
    reply_gen = ReplyGenerator()
    
    # Test cases for different email categories
    test_cases = [
        {
            "category": "interview",
            "email_body": "Dear Akshay, We would like to invite you for an interview for the Software Engineer position. Please let us know your availability for next week.",
            "sender_name": "Sarah Johnson",
            "expected_keywords": ["interview", "available", "thank you"]
        },
        {
            "category": "query",
            "email_body": "Hello, Could you please provide your salary expectations for this position? Also, we need you to fill out this form.",
            "sender_name": "HR Team",
            "expected_keywords": ["salary", "form", "provide"]
        },
        {
            "category": "confirmation",
            "email_body": "Thank you for your application. We have received your resume and will review it shortly.",
            "sender_name": "Hiring Manager",
            "expected_keywords": ["thank you", "application", "received"]
        },
        {
            "category": "rejection",
            "email_body": "Thank you for your interest in our company. Unfortunately, we have decided to move forward with other candidates.",
            "sender_name": "John Smith",
            "expected_keywords": ["thank you", "decided", "other candidates"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📧 Test Case {i}: {test_case['category'].upper()}")
        print("-" * 30)
        
        # Generate reply
        reply = reply_gen.generate_reply(
            email_body=test_case['email_body'],
            category=test_case['category'],
            sender_name=test_case['sender_name']
        )
        
        print(f"📝 Generated Reply:")
        print(reply)
        
        # Validate reply quality
        print(f"\n✅ Quality Checks:")
        print(f"   - Length: {len(reply)} characters")
        print(f"   - Has greeting: {'✓' if reply.lower().startswith(('dear', 'hello', 'hi')) else '✗'}")
        print(f"   - Has closing: {'✓' if any(closing in reply.lower() for closing in ['regards', 'sincerely']) else '✗'}")
        print(f"   - Has name: {'✓' if 'Akshay Shewatkar' in reply else '✗'}")
        print(f"   - No duplicates: {'✓' if reply.lower().count('dear') <= 1 else '✗'}")
        print(f"   - Complete sentences: {'✓' if not reply.endswith(('...', ' and', ' or')) else '✗'}")

def test_ollama_connection():
    """Test Ollama service connection."""
    
    print("\n🔗 Testing Ollama Connection")
    print("=" * 50)
    
    ollama = OllamaService()
    
    try:
        # Test simple generation
        response = ollama.generate(
            prompt="Say 'Hello, Ollama is working!'",
            model="deepseek-r1:1.5b",
            options={'temperature': 0.1, 'num_predict': 20}
        )
        print(f"✅ Ollama Response: {response}")
        return True
    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        return False

if __name__ == "__main__":
    # Test Ollama connection first
    if test_ollama_connection():
        # Run reply generation tests
        test_reply_generation()
    else:
        print("❌ Ollama connection failed. Please check your setup.")