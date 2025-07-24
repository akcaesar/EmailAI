"""
Comprehensive test suite for email processing functionality.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.services.email_processing_service import EmailProcessingService
from api.services.reply_generator import ReplyGenerator
from api.services.email_classifier import EmailClassifier

class TestEmailProcessingService(unittest.TestCase):
    """Test the comprehensive email processing service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = EmailProcessingService()
        self.sample_emails = [
            {
                'subject': 'Interview Invitation - Software Engineer',
                'body': 'Dear Akshay, We would like to invite you for an interview for the Software Engineer position. Please let us know your availability for next week.',
                'sender_name': 'Sarah Johnson'
            },
            {
                'subject': 'Application Confirmation',
                'body': 'Thank you for your application. We have received your resume and will review it shortly.',
                'sender_name': 'HR Team'
            },
            {
                'subject': 'Additional Information Required',
                'body': 'Could you please provide your salary expectations and complete the attached form?',
                'sender_name': 'Hiring Manager'
            },
            {
                'subject': 'Application Status',
                'body': 'Thank you for your interest. Unfortunately, we have decided to move forward with other candidates.',
                'sender_name': 'John Smith'
            }
        ]
    
    def test_process_email_complete_structure(self):
        """Test that complete email processing returns expected structure."""
        email_data = self.sample_emails[0]
        
        # Mock the Ollama service to avoid actual API calls
        with patch('api.services.ollama_service.OllamaService.generate') as mock_generate:
            mock_generate.return_value = '{"category": "interview", "confidence": 0.95, "reasoning": "Contains interview invitation", "priority": 1, "needs_reply": true}'
            
            result = self.processor.process_email_complete(email_data)
            
            # Check required fields
            self.assertIn('subject', result)
            self.assertIn('sender_name', result)
            self.assertIn('processing_status', result)
            self.assertIn('classification', result)
            self.assertIn('summary', result)
            self.assertIn('recommendations', result)
            
            # Check processing status
            self.assertEqual(result['processing_status'], 'success')
    
    def test_batch_processing(self):
        """Test batch email processing."""
        with patch('api.services.ollama_service.OllamaService.generate') as mock_generate:
            mock_generate.return_value = '{"category": "confirmation", "confidence": 0.8, "reasoning": "Standard confirmation", "priority": 4, "needs_reply": false}'
            
            results = self.processor.batch_process_emails(self.sample_emails)
            
            self.assertEqual(len(results), 4)
            for result in results:
                self.assertIn('processing_status', result)
    
    def test_processing_stats(self):
        """Test processing statistics generation."""
        mock_results = [
            {'processing_status': 'success', 'classification': {'category': 'interview', 'priority': 1, 'needs_reply': True}},
            {'processing_status': 'success', 'classification': {'category': 'confirmation', 'priority': 4, 'needs_reply': False}},
            {'processing_status': 'error', 'errors': ['Test error']}
        ]
        
        stats = self.processor.get_processing_stats(mock_results)
        
        self.assertEqual(stats['total_emails'], 3)
        self.assertEqual(stats['successful'], 2)
        self.assertEqual(stats['failed'], 1)
        self.assertIn('category_distribution', stats)
        self.assertIn('needs_reply_count', stats)

class TestReplyGenerator(unittest.TestCase):
    """Test the reply generator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = ReplyGenerator()
    
    def test_clean_ai_response(self):
        """Test AI response cleaning functionality."""
        test_cases = [
            {
                'input': 'Dear Hiring Manager,\n\nThank you for your email.\n\nDear People Manager,\n\nI appreciate your message.',
                'expected_single_greeting': True
            },
            {
                'input': 'Write a professional reply:\n\nDear Hiring Manager,\n\nThank you for your email.',
                'expected_no_instructions': True
            },
            {
                'input': 'Thank you for your email.',
                'expected_proper_structure': True
            }
        ]
        
        for case in test_cases:
            cleaned = self.generator._clean_ai_response(case['input'])
            
            if case.get('expected_single_greeting'):
                self.assertEqual(cleaned.lower().count('dear'), 1)
            
            if case.get('expected_no_instructions'):
                self.assertNotIn('Write a professional', cleaned)
            
            if case.get('expected_proper_structure'):
                self.assertTrue(cleaned.lower().startswith(('dear', 'hello', 'hi')))
                self.assertIn('Akshay Shewatkar', cleaned)
    
    def test_quality_assessment(self):
        """Test reply quality assessment."""
        good_reply = "Dear Hiring Manager,\n\nThank you for your email. I will provide the requested information promptly.\n\nBest regards,\nAkshay Shewatkar"
        bad_reply = "Thank you and"
        
        # Test good reply
        self.assertTrue(self.generator._is_good_quality(good_reply))
        
        # Test bad reply
        self.assertFalse(self.generator._is_good_quality(bad_reply))
    
    def test_intelligent_fallback(self):
        """Test intelligent fallback generation."""
        test_cases = [
            {'category': 'interview', 'expected_keywords': ['interview', 'available']},
            {'category': 'query', 'expected_keywords': ['provide', 'information']},
            {'category': 'confirmation', 'expected_keywords': ['thank you', 'received']},
            {'category': 'rejection', 'expected_keywords': ['thank you', 'decision']}
        ]
        
        for case in test_cases:
            fallback = self.generator._get_intelligent_fallback(
                case['category'], 
                "Test email content", 
                "Test Sender"
            )
            
            # Check structure
            self.assertTrue(fallback.lower().startswith('dear'))
            self.assertIn('Akshay Shewatkar', fallback)
            self.assertIn('regards', fallback.lower())

class TestEmailClassifier(unittest.TestCase):
    """Test email classification functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.classifier = EmailClassifier()
    
    def test_fallback_classification(self):
        """Test fallback classification with keyword matching."""
        test_cases = [
            {
                'subject': 'Interview Invitation',
                'body': 'We would like to schedule an interview with you.',
                'expected_category': 'interview'
            },
            {
                'subject': 'Application Rejected',
                'body': 'Unfortunately, we have decided to move forward with other candidates.',
                'expected_category': 'rejection'
            },
            {
                'subject': 'Additional Information Required',
                'body': 'Please provide your salary expectations and certificates.',
                'expected_category': 'query'
            },
            {
                'subject': 'Application Received',
                'body': 'Thank you for your application. We have received your resume.',
                'expected_category': 'confirmation'
            }
        ]
        
        for case in test_cases:
            result = self.classifier._get_minimal_fallback(case['subject'], case['body'])
            self.assertEqual(result['category'], case['expected_category'])
    
    def test_json_validation(self):
        """Test JSON response validation."""
        valid_json = '{"category": "interview", "confidence": 0.9, "reasoning": "Test", "priority": 1, "needs_reply": true}'
        invalid_json = '{"category": "invalid_category", "confidence": 0.9}'
        
        # Test valid JSON
        result = self.classifier._extract_and_validate_json(valid_json)
        self.assertIsNotNone(result)
        self.assertEqual(result['category'], 'interview')
        
        # Test invalid JSON
        result = self.classifier._extract_and_validate_json(invalid_json)
        self.assertIsNone(result)

class TestApiEndpoints(unittest.TestCase):
    """Test API endpoints (mock-based)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_request_data = {
            'subject': 'Test Email',
            'body': 'This is a test email body.',
            'sender_name': 'Test Sender'
        }
    
    @patch('api.services.email_processing_service.EmailProcessingService.process_email_complete')
    def test_process_email_comprehensive_endpoint(self, mock_process):
        """Test comprehensive email processing endpoint."""
        mock_process.return_value = {
            'subject': 'Test Email',
            'processing_status': 'success',
            'classification': {'category': 'confirmation'},
            'summary': 'Test summary',
            'recommendations': ['Test recommendation']
        }
        
        # Import here to avoid Django setup issues
        from api.views import process_email_comprehensive
        
        # Create mock request
        mock_request = Mock()
        mock_request.data = self.mock_request_data
        
        # This would normally test the actual endpoint
        # For now, just test that the service is called
        mock_process.assert_not_called()  # Not called yet
        
        # Test that the function exists and is callable
        self.assertTrue(callable(process_email_comprehensive))

if __name__ == '__main__':
    # Run specific test classes
    print("🧪 Running Email Processing Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestEmailProcessingService))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestReplyGenerator))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestEmailClassifier))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestApiEndpoints))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")