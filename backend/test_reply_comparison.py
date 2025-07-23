"""
Test script to compare original vs improved reply generator.
Run this to see the difference in output quality.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/akshay/Akshay-CL-Projects/backend')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emailai.settings')
django.setup()

from api.services.reply_generator import ReplyGenerator
from api.services.reply_generator_improved import ImprovedReplyGenerator

def test_reply_generators():
    # Test emails for different categories
    test_emails = {
        'query_form': "Please fill out the attached application form and return it by Friday.",
        'query_documents': "Could you please send us your updated resume and salary certificate?",
        'query_salary': "What are your salary expectations for this position?",
        'interview': "We would like to invite you for an interview on Monday at 2 PM in our office.",
        'confirmation': "Thank you for your application. We have received it and will review it shortly.",
        'rejection': "Thank you for your interest. Unfortunately, we have decided to move forward with other candidates."
    }
    
    print("=== REPLY GENERATOR COMPARISON ===\n")
    
    original_generator = ReplyGenerator()
    improved_generator = ImprovedReplyGenerator()
    
    for category, email_content in test_emails.items():
        print(f"--- {category.upper()} EMAIL ---")
        print(f"Input: {email_content}\n")
        
        # Determine category
        if category.startswith('query'):
            cat = 'query'
        elif category == 'interview':
            cat = 'interview'
        elif category == 'confirmation':
            cat = 'confirmation'
        elif category == 'rejection':
            cat = 'rejection'
        else:
            cat = 'query'
        
        print("ORIGINAL GENERATOR:")
        try:
            original_reply = original_generator.generate_reply(email_content, cat, "HR Manager")
            print(original_reply)
        except Exception as e:
            print(f"Error: {e}")
        
        print("\nIMPROVED GENERATOR:")
        try:
            improved_reply = improved_generator.generate_reply(email_content, cat, "HR Manager")
            print(improved_reply)
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test_reply_generators()