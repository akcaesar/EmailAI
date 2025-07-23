"""
Comprehensive email processing service that coordinates classification, 
reply generation, and quality checks.

Author: Akshay NS
"""

import logging
from typing import Dict, Any, Optional, List
from .email_classifier import EmailClassifier
from .reply_generator_improved import ImprovedReplyGenerator as ReplyGenerator
from .ollama_service import OllamaService

logger = logging.getLogger(__name__)

class EmailProcessingService:
    """Service that handles the complete email processing pipeline."""
    
    def __init__(self):
        self.classifier = EmailClassifier()
        self.reply_generator = ReplyGenerator()
        self.ollama = OllamaService()
    
    def process_email_complete(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete email processing pipeline:
        1. Classify email
        2. Generate summary
        3. Generate reply if needed
        4. Return comprehensive result
        """
        
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        sender_name = email_data.get('sender_name', '')
        
        logger.info(f"Processing email: {subject[:50]}...")
        
        result = {
            'subject': subject,
            'sender_name': sender_name,
            'processing_status': 'success',
            'errors': []
        }
        
        try:
            # Step 1: Classify email
            classification = self.classifier.classify_email(body, subject)
            result['classification'] = classification
            
            # Step 2: Generate summary
            try:
                summary = self.classifier.generate_summary(body)
                result['summary'] = summary
            except Exception as e:
                logger.warning(f"Summary generation failed: {e}")
                result['summary'] = self._generate_fallback_summary(body)
            
            # Step 3: Generate reply if needed
            if classification.get('needs_reply', False):
                try:
                    reply = self.reply_generator.generate_reply(
                        email_body=body,
                        category=classification['category'],
                        sender_name=sender_name
                    )
                    result['suggested_reply'] = reply
                    result['reply_quality'] = self._assess_reply_quality(reply)
                except Exception as e:
                    logger.error(f"Reply generation failed: {e}")
                    result['errors'].append(f"Reply generation failed: {str(e)}")
                    result['suggested_reply'] = None
            else:
                result['suggested_reply'] = None
                result['reply_quality'] = None
            
            # Step 4: Set processing recommendations
            result['recommendations'] = self._generate_recommendations(classification, result)
            
        except Exception as e:
            logger.error(f"Email processing failed: {e}")
            result['processing_status'] = 'error'
            result['errors'].append(f"Processing failed: {str(e)}")
        
        return result
    
    def _generate_fallback_summary(self, body: str) -> str:
        """Generate a simple fallback summary when AI fails."""
        sentences = body.split('.')
        if sentences and len(sentences[0]) < 150:
            return sentences[0].strip() + '.'
        else:
            return body[:120].strip() + '...'
    
    def _assess_reply_quality(self, reply: str) -> Dict[str, Any]:
        """Assess the quality of a generated reply."""
        quality_score = 0
        issues = []
        
        # Check length
        if len(reply) < 50:
            issues.append("Reply too short")
        elif len(reply) > 800:
            issues.append("Reply too long")
        else:
            quality_score += 20
        
        # Check structure
        if reply.lower().startswith(('dear', 'hello', 'hi')):
            quality_score += 20
        else:
            issues.append("Missing proper greeting")
        
        if any(closing in reply.lower() for closing in ['regards', 'sincerely']):
            quality_score += 20
        else:
            issues.append("Missing proper closing")
        
        if 'Akshay Shewatkar' in reply:
            quality_score += 20
        else:
            issues.append("Missing sender name")
        
        # Check for duplicates
        if reply.lower().count('dear') > 1:
            issues.append("Duplicate greetings")
        else:
            quality_score += 10
        
        # Check for completeness
        if reply.endswith(('...', ' and', ' or')):
            issues.append("Incomplete sentences")
        else:
            quality_score += 10
        
        return {
            'score': quality_score,
            'max_score': 100,
            'issues': issues,
            'quality_level': 'excellent' if quality_score >= 90 else 
                           'good' if quality_score >= 70 else 
                           'fair' if quality_score >= 50 else 'poor'
        }
    
    def _generate_recommendations(self, classification: Dict[str, Any], result: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on processing results."""
        recommendations = []
        
        category = classification.get('category', '')
        confidence = classification.get('confidence', 0)
        
        # Classification-based recommendations
        if category == 'interview':
            recommendations.append("🎯 HIGH PRIORITY: Schedule interview response immediately")
            recommendations.append("📅 Check calendar availability before responding")
        elif category == 'query':
            recommendations.append("📋 Action required: Prepare requested documents/information")
            recommendations.append("⏰ Respond within 24 hours to show professionalism")
        elif category == 'rejection':
            recommendations.append("📝 Consider sending a brief thank-you note")
            recommendations.append("🔄 Optional: Ask for feedback or future opportunities")
        elif category == 'confirmation':
            recommendations.append("👍 No immediate action required")
            recommendations.append("📊 Continue monitoring for follow-up communications")
        
        # Confidence-based recommendations
        if confidence < 0.7:
            recommendations.append("⚠️ Low confidence classification - manual review recommended")
        
        # Quality-based recommendations
        if result.get('reply_quality') and result['reply_quality']['score'] < 70:
            recommendations.append("✏️ Review and edit suggested reply before sending")
        
        return recommendations
    
    def batch_process_emails(self, email_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple emails in batch."""
        results = []
        
        for email_data in email_list:
            try:
                result = self.process_email_complete(email_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch processing failed for email: {e}")
                results.append({
                    'subject': email_data.get('subject', 'Unknown'),
                    'processing_status': 'error',
                    'errors': [f"Processing failed: {str(e)}"]
                })
        
        return results
    
    def get_processing_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate processing statistics from batch results."""
        total = len(results)
        successful = sum(1 for r in results if r.get('processing_status') == 'success')
        failed = total - successful
        
        # Category distribution
        categories = {}
        for result in results:
            if result.get('classification'):
                cat = result['classification'].get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1
        
        # Priority distribution
        priorities = {}
        for result in results:
            if result.get('classification'):
                priority = result['classification'].get('priority', 4)
                priorities[priority] = priorities.get(priority, 0) + 1
        
        return {
            'total_emails': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'category_distribution': categories,
            'priority_distribution': priorities,
            'needs_reply_count': sum(1 for r in results 
                                   if r.get('classification', {}).get('needs_reply', False))
        }