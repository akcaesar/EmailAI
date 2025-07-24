#!/usr/bin/env python3
"""
Test with the actual German email from the log to see if improvements work.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/home/akshay/Akshay-CL-Projects/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emailai.settings')
django.setup()

from api.services.email_processing_service import EmailProcessingService

def test_german_email():
    """Test with the actual German email from the worker log."""
    
    # The actual email from the log
    email_data = {
        "subject": "Deine Bewerbung bei Py-T GmbH",
        "body": """Hallo Akshay,

Vielen Dank für deine Bewerbung für die Position Python / Django Entwickler.

Ihre Bewerbung wurde sorgfältig geprüft und Ihre Qualifikationen berücksichtigt. Wir sind aufgrund des spezifischen Profils und der Anzahl anderer qualifizierter Kandidaten zu diesem Zeitpunkt nicht in der Lage, mit Ihrem Anliegen fortzufahren. Wir wünschen Ihnen weiterhin viel Erfolg bei Ihrer Suche nach einer neuen Herausforderung.

Mit freundlichen Grüßen
Py-T GmbH""",
        "sender_name": "Py-T GmbH"
    }
    
    print("🧪 Testing with real German rejection email...\n")
    
    processor = EmailProcessingService()
    result = processor.process_email_complete(email_data)
    
    print(f"Subject: {result.get('subject')}")
    print(f"Classification: {result.get('classification', {})}")
    print(f"Summary: {result.get('summary', 'N/A')}")
    print(f"Has suggested reply: {result.get('suggested_reply') is not None}")
    print(f"Processing status: {result.get('processing_status')}")
    
    if result.get('errors'):
        print(f"Errors: {result.get('errors')}")
    
    # Check if classification looks correct
    classification = result.get('classification', {})
    if classification.get('category') == 'rejection':
        print("\n✅ Classification appears correct - detected as rejection")
    else:
        print(f"\n⚠️ Classification might be off - got: {classification.get('category')}")
    
    # Check if summary is concise and meaningful
    summary = result.get('summary', '')
    if summary and len(summary) < 200 and 'think' not in summary.lower():
        print("✅ Summary looks good - concise and clean")
    else:
        print(f"⚠️ Summary issues - length: {len(summary)}, contains thinking: {'think' in summary.lower()}")
    
    # Check reply generation logic
    has_reply = result.get('suggested_reply') is not None
    should_have_reply = classification.get('category') in ['rejection', 'interview', 'query']
    
    if has_reply == should_have_reply:
        print("✅ Reply generation logic working correctly")
    else:
        print(f"⚠️ Reply logic issue - has_reply: {has_reply}, should_have: {should_have_reply}")

if __name__ == "__main__":
    test_german_email()