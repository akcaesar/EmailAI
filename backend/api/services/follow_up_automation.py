"""
Follow-up automation system for job application emails.
Handles scheduled follow-ups, reminders, and automated responses.

Author: Akshay NS
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.db.models import Q
from ..models import ProcessedEmail, FollowUpEmail, EmailAccount
from .reply_generator_improved import ImprovedReplyGenerator as ReplyGenerator
from .email_sender import EmailSender

logger = logging.getLogger(__name__)

class FollowUpAutomationService:
    """Service for managing automated follow-up emails."""
    
    def __init__(self):
        self.reply_generator = ReplyGenerator()
        # Note: EmailSender will be initialized with account when needed
    
    def generate_follow_up_schedule(self, email: ProcessedEmail) -> List[Dict[str, Any]]:
        """
        Generate a follow-up schedule based on email category and priority.
        """
        schedule = []
        base_date = email.processed_at or timezone.now()
        
        if email.category == 'confirmation':
            # Follow up after 1 week, then 2 weeks
            schedule.extend([
                {
                    'days_after': 7,
                    'follow_up_date': base_date + timedelta(days=7),
                    'type': 'status_inquiry',
                    'priority': 'medium'
                },
                {
                    'days_after': 14,
                    'follow_up_date': base_date + timedelta(days=14),
                    'type': 'gentle_reminder',
                    'priority': 'low'
                }
            ])
        
        elif email.category == 'interview':
            # Follow up 1 day after if no response
            schedule.append({
                'days_after': 1,
                'follow_up_date': base_date + timedelta(days=1),
                'type': 'interview_confirmation',
                'priority': 'high'
            })
        
        elif email.category == 'query':
            # Follow up 3 days after if no response
            schedule.append({
                'days_after': 3,
                'follow_up_date': base_date + timedelta(days=3),
                'type': 'query_reminder',
                'priority': 'medium'
            })
        
        elif email.category == 'rejection':
            # Optional follow-up after 1 month for future opportunities
            schedule.append({
                'days_after': 30,
                'follow_up_date': base_date + timedelta(days=30),
                'type': 'future_opportunity',
                'priority': 'low'
            })
        
        return schedule
    
    def create_follow_up_email(self, original_email: ProcessedEmail, follow_up_type: str, days_passed: int) -> str:
        """
        Create follow-up email content based on type and original email.
        """
        company_name = self.extract_company_name(original_email.from_address)
        
        follow_up_templates = {
            'status_inquiry': f"""Dear Hiring Manager,
            
I hope this email finds you well. I wanted to follow up on my application for the position that I submitted {days_passed} days ago.

I remain very interested in this opportunity and would appreciate any update on the status of my application or the next steps in the process.

Please let me know if you need any additional information from me.

Best regards,
Akshay Shewatkar""",
            
            'gentle_reminder': f"""Dear Hiring Manager,
            
I hope you're doing well. I wanted to follow up once more regarding my application submitted {days_passed} days ago.

I understand you may be busy with the selection process, and I wanted to reiterate my strong interest in this position and {company_name}.

I would be grateful for any update when it's convenient for you.

Best regards,
Akshay Shewatkar""",
            
            'interview_confirmation': f"""Dear Hiring Manager,
            
I wanted to confirm my availability for the interview opportunity you mentioned. I am very excited about the possibility of joining {company_name}.

Please let me know the preferred date and time, and I will make sure to be available.

Looking forward to hearing from you.

Best regards,
Akshay Shewatkar""",
            
            'query_reminder': f"""Dear Hiring Manager,
            
I hope this email finds you well. I wanted to follow up on the additional information you requested {days_passed} days ago.

I want to ensure I haven't missed anything and am ready to provide any additional details you may need.

Please let me know if there's anything else I can assist with.

Best regards,
Akshay Shewatkar""",
            
            'future_opportunity': f"""Dear Hiring Manager,
            
I hope you're doing well. While I understand the recent position has been filled, I wanted to reach out to express my continued interest in {company_name}.

I would be grateful if you could keep me in mind for any future opportunities that might be a good fit for my background and skills.

Thank you for your time and consideration.

Best regards,
Akshay Shewatkar"""
        }
        
        return follow_up_templates.get(follow_up_type, follow_up_templates['status_inquiry'])
    
    def extract_company_name(self, email_address: str) -> str:
        """
        Extract company name from email address.
        """
        try:
            domain = email_address.split('@')[1]
            # Remove common prefixes and suffixes
            company = domain.split('.')[0]
            return company.capitalize()
        except:
            return "the company"
    
    def get_emails_needing_follow_up(self, user_id: Optional[int] = None) -> List[ProcessedEmail]:
        """
        Get emails that need follow-up based on time elapsed and category.
        """
        try:
            # Base query
            query = ProcessedEmail.objects.filter(
                status='processed',
                category__in=['confirmation', 'interview', 'query']
            )
            
            # Filter by user if specified
            if user_id:
                query = query.filter(account__user_id=user_id)
            
            # Filter by time criteria
            now = timezone.now()
            follow_up_candidates = []
            
            for email in query:
                base_date = email.processed_at or email.received_at
                days_passed = (now - base_date).days
                
                # Check if follow-up is needed based on category and time
                needs_follow_up = False
                
                if email.category == 'confirmation' and days_passed >= 7:
                    needs_follow_up = True
                elif email.category == 'interview' and days_passed >= 1:
                    needs_follow_up = True
                elif email.category == 'query' and days_passed >= 3:
                    needs_follow_up = True
                
                # Check if follow-up already exists
                if needs_follow_up:
                    existing_follow_up = FollowUpEmail.objects.filter(
                        original_email=email,
                        status__in=['sent', 'draft']
                    ).exists()
                    
                    if not existing_follow_up:
                        follow_up_candidates.append(email)
            
            return follow_up_candidates
            
        except Exception as e:
            logger.error(f"Error getting emails needing follow-up: {e}")
            return []
    
    def create_follow_up_draft(self, original_email: ProcessedEmail) -> FollowUpEmail:
        """
        Create a draft follow-up email for the given original email.
        """
        try:
            base_date = original_email.processed_at or original_email.received_at
            days_passed = (timezone.now() - base_date).days
            
            # Determine follow-up type
            if original_email.category == 'confirmation':
                follow_up_type = 'status_inquiry' if days_passed < 14 else 'gentle_reminder'
            elif original_email.category == 'interview':
                follow_up_type = 'interview_confirmation'
            elif original_email.category == 'query':
                follow_up_type = 'query_reminder'
            else:
                follow_up_type = 'status_inquiry'
            
            # Generate follow-up content
            follow_up_content = self.create_follow_up_email(
                original_email, follow_up_type, days_passed
            )
            
            # Create follow-up email record
            follow_up = FollowUpEmail.objects.create(
                original_email=original_email,
                content=follow_up_content,
                status='draft'
            )
            
            return follow_up
            
        except Exception as e:
            logger.error(f"Error creating follow-up draft: {e}")
            raise
    
    def send_follow_up_email(self, follow_up: FollowUpEmail) -> bool:
        """
        Send a follow-up email.
        """
        try:
            original_email = follow_up.original_email
            
            # Initialize EmailSender with the account
            email_sender = EmailSender(original_email.account)
            
            # Send the email using the reply method
            result = email_sender.send_reply(
                original_email=original_email,
                reply_content=follow_up.content,
                subject_override=f"Re: {original_email.subject}"
            )
            
            success = result.get('success', False)
            
            if success:
                follow_up.status = 'sent'
                follow_up.sent_at = timezone.now()
                follow_up.save()
                
                logger.info(f"Follow-up sent successfully for email {original_email.id}")
                return True
            else:
                follow_up.status = 'error'
                follow_up.error_message = "Failed to send email"
                follow_up.save()
                return False
                
        except Exception as e:
            logger.error(f"Error sending follow-up email: {e}")
            follow_up.status = 'error'
            follow_up.error_message = str(e)
            follow_up.save()
            return False
    
    def process_automated_follow_ups(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Process all automated follow-ups for a user or all users.
        """
        try:
            # Get emails needing follow-up
            emails_needing_follow_up = self.get_emails_needing_follow_up(user_id)
            
            results = {
                'total_candidates': len(emails_needing_follow_up),
                'drafts_created': 0,
                'emails_sent': 0,
                'errors': []
            }
            
            for email in emails_needing_follow_up:
                try:
                    # Create draft follow-up
                    follow_up = self.create_follow_up_draft(email)
                    results['drafts_created'] += 1
                    
                    # Optionally send immediately (based on configuration)
                    # For now, we'll just create drafts
                    logger.info(f"Created follow-up draft for email {email.id}")
                    
                except Exception as e:
                    error_msg = f"Error processing email {email.id}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing automated follow-ups: {e}")
            return {
                'total_candidates': 0,
                'drafts_created': 0,
                'emails_sent': 0,
                'errors': [str(e)]
            }
    
    def get_follow_up_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get statistics about follow-up emails.
        """
        try:
            # Base query
            query = FollowUpEmail.objects.all()
            
            # Filter by user if specified
            if user_id:
                query = query.filter(original_email__account__user_id=user_id)
            
            total_follow_ups = query.count()
            sent_follow_ups = query.filter(status='sent').count()
            draft_follow_ups = query.filter(status='draft').count()
            error_follow_ups = query.filter(status='error').count()
            
            # Follow-ups by category
            category_stats = {}
            for category in ['confirmation', 'interview', 'query', 'rejection']:
                count = query.filter(original_email__category=category).count()
                category_stats[category] = count
            
            return {
                'total_follow_ups': total_follow_ups,
                'sent_follow_ups': sent_follow_ups,
                'draft_follow_ups': draft_follow_ups,
                'error_follow_ups': error_follow_ups,
                'success_rate': (sent_follow_ups / total_follow_ups * 100) if total_follow_ups > 0 else 0,
                'category_distribution': category_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting follow-up statistics: {e}")
            return {
                'total_follow_ups': 0,
                'sent_follow_ups': 0,
                'draft_follow_ups': 0,
                'error_follow_ups': 0,
                'success_rate': 0,
                'category_distribution': {}
            }