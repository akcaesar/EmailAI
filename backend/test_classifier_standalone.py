#!/usr/bin/env python3
"""
Standalone test script to verify email classification works correctly.
  Run this to test the classifier without the full Django setup.
"""

import sys
import os
import django
from pathlib import Path

  # Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

  # Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emailai.settings')
django.setup()

  # Now we can import Django modules
from api.services.email_classifier import EmailClassifier

def test_classifier():
      """Test the email classifier with sample emails."""

      print("🤖 Testing Email Classifier with Ollama AI")
      print("=" * 50)

      # Test emails for all 4 categories
      test_emails = [
          {
              "name": "German Rejection",
              "subject": "Re: Bewerbung Software Engineer",
              "body": """Sehr geehrter Herr Shewatkar,

  für Ihre Bewerbung und Ihr Interesse an einer Mitarbeit in unserem Hause danken wir Ihnen. Aufgrund der zahlreichen eingegangenen Bewerbungen mussten wir eine      
  Vorauswahl treffen. Leider konnten wir Sie nicht berücksichtigen.

  Für Ihre Zukunft wünschen wir Ihnen alles Gute und viel Erfolg.

  Mit freundlichen Grüßen
  Julia Sommer""",
              "expected": "rejection"
          },
          {
              "name": "English Interview",
              "subject": "Interview Invitation - Software Engineer Position",
              "body": """Dear Mr. Shewatkar,

  Thank you for your application for the Software Engineer position. We would like to invite you for an interview next Tuesday at 2:00 PM.

  Please confirm your availability and let us know if you need any special arrangements.

  Best regards,
  HR Team""",
              "expected": "interview"
          },
          {
              "name": "Application Confirmation",
              "subject": "Application Received - Developer Role",
              "body": """Dear Applicant,

  Thank you for your interest in the Developer position. We have successfully received your application and our hiring team will review it carefully.

  We will contact you within the next two weeks with an update.

  Kind regards,
  Recruitment Team""",
              "expected": "confirmation"
          },
          {
              "name": "Query for Information",
              "subject": "Additional Information Required",
              "body": """Hello,

  We are reviewing your application for the Software Engineer position. Could you please provide the following additional information:

  1. Your salary expectations
  2. Relevant certificates
  3. Available start date

  Please reply at your earliest convenience.

  Best regards,
  HR Department""",
              "expected": "query"
          }
      ]

      classifier = EmailClassifier()
      results = []

      for i, email in enumerate(test_emails, 1):
          print(f"\n📧 Test {i}: {email['name']}")
          print(f"Subject: {email['subject']}")
          print(f"Expected: {email['expected']}")

          try:
              # Test classification
              result = classifier.classify_email(email['body'], email['subject'])

              # Test summary
              summary = classifier.generate_summary(email['body'])

              actual_category = result['category']
              is_correct = actual_category == email['expected']

              print(f"Actual: {actual_category}")
              print(f"Confidence: {result['confidence']}")
              print(f"Reasoning: {result['reasoning']}")
              print(f"Summary: {summary}")
              print(f"✅ Correct" if is_correct else f"❌ Wrong")

              results.append({
                  'name': email['name'],
                  'expected': email['expected'],
                  'actual': actual_category,
                  'correct': is_correct,
                  'confidence': result['confidence'],
                  'summary': summary
              })

          except Exception as e:
              print(f"❌ Error: {e}")
              results.append({
                  'name': email['name'],
                  'expected': email['expected'],
                  'actual': 'ERROR',
                  'correct': False,
                  'confidence': 0.0,
                  'summary': f"Error: {e}"
              })

      # Summary
      print("\n" + "=" * 50)
      print("📊 CLASSIFICATION RESULTS SUMMARY")
      print("=" * 50)

      correct_count = sum(1 for r in results if r['correct'])
      total_count = len(results)
      accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0

      print(f"Total Tests: {total_count}")
      print(f"Correct: {correct_count}")
      print(f"Accuracy: {accuracy:.1f}%")

      print("\nDetailed Results:")
      for result in results:
          status = "✅" if result['correct'] else "❌"
          print(f"{status} {result['name']}: {result['expected']} → {result['actual']} ({result['confidence']:.2f})")

      return results

if __name__ == "__main__":
      try:
          results = test_classifier()
          print(f"\n🎯 Classification test completed!")

          # Check if all tests passed
          all_correct = all(r['correct'] for r in results)
          if all_correct:
              print("🎉 All tests passed! The classifier is working correctly.")
          else:
              print("⚠️  Some tests failed. Check the Ollama model and prompts.")

      except Exception as e:
          print(f"💥 Test failed with error: {e}")
          import traceback
          traceback.print_exc()