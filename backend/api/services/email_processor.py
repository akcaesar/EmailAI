"""
Author: Akshay NS
Contains: Background email processing service using Celery.
"""

from celery import shared_task
from django.utils import timezone
from ..models import ProcessedEmail, EmailAccount
from .email_classifier import EmailClassifier
from .reply_generator_improved import ImprovedReplyGenerator as ReplyGenerator
import logging
import json

logger = logging.getLogger(__name__)

@shared_task
def process_email_batch(account_id: int, email_uids: list):
      """Process a batch of emails for classification and reply generation."""

      try:
          account = EmailAccount.objects.get(id=account_id)
          classifier = EmailClassifier()
          reply_generator = ReplyGenerator()

          processed_count = 0

          for uid in email_uids:
              try:
                  email = ProcessedEmail.objects.get(account=account, uid=uid)

                  if email.status != ProcessedEmail.Status.PENDING:
                      continue

                  # Classify email
                  classification_result = classifier.classify_email(
                      email.raw_body,
                      email.subject
                  )

                  # Generate summary
                  summary = classifier.generate_summary(email.raw_body)

                  # Update email with classification results
                  email.category = classification_result.get('category', 'other')
                  email.priority = classification_result.get('priority', 3)
                  email.needs_reply = classification_result.get('needs_reply', False)
                  email.summary = summary

                  # Generate reply if needed
                  if email.needs_reply and email.category in ['interview', 'offer', 'follow_up']:
                      suggested_reply = reply_generator.generate_reply(
                          email.raw_body,
                          email.category,
                          email.from_name or email.from_address.split('@')[0]
                      )
                      email.suggested_reply = suggested_reply

                  email.status = ProcessedEmail.Status.PROCESSED
                  email.processed_at = timezone.now()
                  email.save()

                  processed_count += 1

              except ProcessedEmail.DoesNotExist:
                  logger.warning(f"Email with UID {uid} not found")
                  continue
              except Exception as e:
                  logger.error(f"Error processing email {uid}: {e}")
                  continue

          logger.info(f"Processed {processed_count} emails for account {account_id}")
          return {'processed': processed_count, 'total': len(email_uids)}

      except EmailAccount.DoesNotExist:
          logger.error(f"Email account {account_id} not found")
          return {'error': 'Account not found'}
      except Exception as e:
          logger.error(f"Batch processing error: {e}")
          return {'error': str(e)}

@shared_task
def process_single_email(email_id: int):
    """Process a single email for classification and reply generation."""
    
    try:
        email = ProcessedEmail.objects.get(id=email_id)
        
        if email.status != ProcessedEmail.Status.PENDING:
            return {'error': 'Email already processed'}
        
        classifier = EmailClassifier()
        reply_generator = ReplyGenerator()
        
        # Classify email
        classification_result = classifier.classify_email(
            email.raw_body,
            email.subject
        )
        
        # Generate summary
        summary = classifier.generate_summary(email.raw_body)
        
        # Update email with classification results
        email.category = classification_result.get('category', 'other')
        email.priority = classification_result.get('priority', 3)
        email.needs_reply = classification_result.get('needs_reply', False)
        email.summary = summary
        
        # Generate reply if needed
        if email.needs_reply and email.category in ['interview', 'offer', 'follow_up']:
            suggested_reply = reply_generator.generate_reply(
                email.raw_body,
                email.category,
                email.from_name or email.from_address.split('@')[0]
            )
            email.suggested_reply = suggested_reply
        
        email.status = ProcessedEmail.Status.PROCESSED
        email.processed_at = timezone.now()
        email.save()
        
        logger.info(f"Successfully processed email {email_id}")
        return {'success': True, 'email_id': email_id}
        
    except ProcessedEmail.DoesNotExist:
        logger.error(f"Email {email_id} not found")
        return {'error': 'Email not found'}
    except Exception as e:
        logger.error(f"Error processing email {email_id}: {e}")
        return {'error': str(e)}

@shared_task
def batch_process_emails_task(email_ids: list):
    """Process multiple emails in batch using Celery."""
    
    try:
        results = []
        
        for email_id in email_ids:
            result = process_single_email.delay(email_id)
            results.append({
                'email_id': email_id,
                'task_id': result.id
            })
        
        logger.info(f"Queued {len(email_ids)} emails for processing")
        return {
            'success': True,
            'queued_count': len(email_ids),
            'task_results': results
        }
        
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        return {'error': str(e)}

@shared_task
def generate_follow_ups():
      """Generate follow-up emails for pending replies."""

      try:
          from datetime import timedelta

          # Find emails that need follow-up (older than 3 days, no reply sent)
          cutoff_date = timezone.now() - timedelta(days=3)

          pending_emails = ProcessedEmail.objects.filter(
              needs_reply=True,
              processed_at__lt=cutoff_date,
              followups__isnull=True,
              category__in=['interview', 'offer', 'follow_up']
          )

          reply_generator = ReplyGenerator()
          follow_up_count = 0

          for email in pending_emails:
              try:
                  follow_up_content = reply_generator.generate_follow_up(
                      email.raw_body,
                      (timezone.now() - email.processed_at).days
                  )

                  # Create FollowUpEmail record
                  from ..models import FollowUpEmail
                  FollowUpEmail.objects.create(
                      original_email=email,
                      content=follow_up_content,
                      status='draft'
                  )

                  follow_up_count += 1

              except Exception as e:
                  logger.error(f"Error generating follow-up for email {email.id}: {e}")
                  continue

          logger.info(f"Generated {follow_up_count} follow-up emails")
          return {'generated': follow_up_count}

      except Exception as e:
          logger.error(f"Follow-up generation error: {e}")
          return {'error': str(e)}