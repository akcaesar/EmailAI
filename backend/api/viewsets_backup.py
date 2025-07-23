"""
Django REST Framework ViewSets for EmailAI API endpoints.
Provides a more concise and organized approach to API development using ModelViewSets.

Author: Akshay NS
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import logging
from typing import Dict, Any
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes

from .models import ProcessedEmail, EmailAccount, FollowUpEmail
from .serializers import (
    EmailAccountSerializer, EmailAccountCreateSerializer,
    ProcessedEmailSerializer, FollowUpEmailSerializer,
    EmailProcessingSerializer, BatchEmailProcessingSerializer,
    FetchEmailsSerializer, FollowUpDraftSerializer, ReplyGenerationSerializer,
    EmailReprocessingSerializer, BatchReprocessingSerializer, SummaryRewriteSerializer
)
from .services.email_processing_service import EmailProcessingService
from .services.follow_up_automation import FollowUpAutomationService
from .services.ollama_service import OllamaService

logger = logging.getLogger(__name__)


class EmailAccountViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet for managing user email accounts with full CRUD operations.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return email accounts for the authenticated user only."""
        return EmailAccount.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return EmailAccountCreateSerializer
        return EmailAccountSerializer
    
    def perform_create(self, serializer):
        """Set the user when creating a new email account."""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def fetch_all_emails(self, request):
        """Fetch emails for all accounts of the authenticated user."""
        accounts = self.get_queryset()
        max_emails_per_account = request.data.get('max_emails', 40)
        results = []
        
        from .services.email_fetching_service import fetch_emails_sync

        for account in accounts:
            try:
                result = fetch_emails_sync(account.id, max_emails_per_account)
                results.append({
                    'account_id': account.id,
                    'email': account.email,
                    'result': result
                })
            except Exception as e:
                logger.error(f"Failed to fetch emails for account {account.id}: {e}")
                results.append({
                    'account_id': account.id,
                    'email': account.email,
                    'error': str(e)
                })
                
        return Response({
            'status': 'success',
            'message': 'Batch email fetch process initiated.',
            'data': results
        })

    @extend_schema(
        summary="Fetch emails from account",
        description="Fetch emails from a specific email account",
        request=FetchEmailsSerializer
    )
    @action(detail=True, methods=['post'])
    def fetch_emails(self, request, pk: int = None):
        """Fetch emails from a specific account."""
        serializer = FetchEmailsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            account = self.get_object()
            max_emails = serializer.validated_data['max_emails']
            
            # Import here to avoid circular imports
            from .services.email_fetching_service import fetch_emails_sync
            
            # Fetch emails
            result = fetch_emails_sync(account.id, max_emails)
            
            return Response({
                'status': 'success',
                'message': f'Fetched {result.get("fetched_count", 0)} emails',
                'data': result
            })
            
        except Exception as e:
            logger.error(f"Fetch emails failed: {e}")
            return Response(
                {'error': f'Failed to fetch emails: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessedEmailViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet for processed emails with filtering and custom actions.
    """
    serializer_class = ProcessedEmailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return processed emails for the authenticated user only."""
        queryset = ProcessedEmail.objects.filter(account__user=self.request.user)
        
        # Add filtering
        category = self.request.query_params.get('category', None)
        status_filter = self.request.query_params.get('status', None)
        needs_reply = self.request.query_params.get('needs_reply', None)
        
        if category:
            queryset = queryset.filter(category=category)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if needs_reply:
            queryset = queryset.filter(needs_reply=needs_reply.lower() == 'true')
        
        return queryset.order_by('-received_at')
    
    @extend_schema(
        summary="Generate email reply",
        description="Generate an AI-powered reply for a specific email",
        request=ReplyGenerationSerializer
    )
    @action(detail=True, methods=['post'])
    def generate_reply(self, request, pk: int = None):
        """Generate a reply for a specific email."""
        serializer = ReplyGenerationSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            email = self.get_object()
            model = serializer.validated_data['model']
            
            from .services.reply_generator_improved import ImprovedReplyGenerator as ReplyGenerator
            reply_generator = ReplyGenerator()
            
            reply = reply_generator.generate_reply(
                email_body=email.raw_body,
                category=email.category,
                sender_name=email.from_name or '',
                model=model
            )
            
            # Save the suggested reply
            email.suggested_reply = reply
            email.save()
            
            return Response({
                'status': 'success',
                'reply': reply,
                'message': 'Reply generated successfully'
            })
            
        except Exception as e:
            logger.error(f"Generate reply failed: {e}")
            return Response(
                {'error': f'Failed to generate reply: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Reprocess email",
        description="Completely reprocess an email (classification, summary, reply)",
        request=EmailReprocessingSerializer
    )
    @action(detail=True, methods=['post'])
    def reprocess_email(self, request, pk: int = None):
        """Reprocess a specific email completely (classification, summary, reply)."""
        serializer = EmailReprocessingSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            email = self.get_object()
            
            # Use the comprehensive processing service
            processor = EmailProcessingService()
            
            # Prepare email data for processing
            email_data = {
                'subject': email.subject,
                'body': email.raw_body,
                'sender_name': email.from_name or ''
            }
            
            # Process the email
            result = processor.process_email_complete(email_data)
            
            if result['processing_status'] == 'success':
                # Update the email with new processing results
                if 'classification' in result:
                    classification = result['classification']
                    email.category = classification.get('category')
                    email.priority = classification.get('priority', 0)
                    email.needs_reply = classification.get('needs_reply', False)
                
                if 'summary' in result:
                    email.summary = result['summary']
                
                if 'suggested_reply' in result and result['suggested_reply']:
                    email.suggested_reply = result['suggested_reply']
                
                # Update processing status and reprocessing history
                email.status = 'processed'
                if email.processed_at is None:
                    email.processed_at = timezone.now()
                email.reprocessed_at = timezone.now()
                email.reprocessing_count += 1
                email.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Email reprocessed successfully',
                    'data': {
                        'email_id': email.id,
                        'category': email.category,
                        'priority': email.priority,
                        'needs_reply': email.needs_reply,
                        'summary': email.summary,
                        'suggested_reply': email.suggested_reply,
                        'processing_result': result
                    }
                })
            else:
                return Response(
                    {'error': f'Reprocessing failed: {", ".join(result.get("errors", []))}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            logger.error(f"Email reprocessing failed: {e}")
            return Response(
                {'error': f'Failed to reprocess email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Rewrite email summary",
        description="Regenerate only the summary for a specific email",
        request=SummaryRewriteSerializer
    )
    @action(detail=True, methods=['post'])
    def rewrite_summary(self, request, pk: int = None):
        """Regenerate only the summary for a specific email."""
        serializer = SummaryRewriteSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            email = self.get_object()
            
            # Use the classifier to generate a new summary
            from .services.email_classifier import EmailClassifier
            classifier = EmailClassifier()
            
            new_summary = classifier.generate_summary(email.raw_body)
            
            # Update the email with new summary
            email.summary = new_summary
            email.save()
            
            return Response({
                'status': 'success',
                'message': 'Summary rewritten successfully',
                'data': {
                    'email_id': email.id,
                    'new_summary': new_summary
                }
            })
            
        except Exception as e:
            logger.error(f"Summary rewriting failed: {e}")
            return Response(
                {'error': f'Failed to rewrite summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailProcessingViewSet(viewsets.ViewSet):
    """
    ViewSet for email processing operations.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def process_comprehensive(self, request):
        """Process a single email comprehensively using Celery."""
        try:
            email_data = request.data
            
            # Validate required fields
            if not email_data.get('subject') or not email_data.get('body'):
                return Response(
                    {'error': 'Subject and body are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # For existing emails, queue for processing
            email_id = email_data.get('email_id')
            if email_id:
                from ..services.email_processor import process_single_email
                task = process_single_email.delay(email_id)
                
                return Response({
                    'status': 'success',
                    'message': 'Email queued for processing',
                    'task_id': task.id,
                    'email_id': email_id
                })
            
            # For new emails, process directly
            processor = EmailProcessingService()
            result = processor.process_email_complete(email_data)
            
            return Response({
                'status': 'success',
                'data': result,
                'message': 'Email processed successfully'
            })
            
        except Exception as e:
            logger.error(f"Comprehensive email processing failed: {e}")
            return Response(
                {'error': f'Processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def batch_process(self, request):
        """Process multiple emails in batch using Celery."""
        try:
            email_ids = request.data.get('email_ids', [])
            
            if not email_ids:
                return Response(
                    {'error': 'No email IDs provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Queue emails for processing using Celery
            from ..services.email_processor import batch_process_emails_task
            task = batch_process_emails_task.delay(email_ids)
            
            return Response({
                'status': 'success',
                'message': f'Queued {len(email_ids)} emails for processing',
                'task_id': task.id,
                'email_count': len(email_ids)
            })
            
        except Exception as e:
            logger.error(f"Batch email processing failed: {e}")
            return Response(
                {'error': f'Batch processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def batch_reprocess(self, request):
        """Reprocess multiple emails in batch."""
        serializer = BatchReprocessingSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            email_ids = serializer.validated_data['email_ids']
            
            # Get emails that belong to the user
            user_emails = ProcessedEmail.objects.filter(
                id__in=email_ids,
                account__user=request.user
            )
            
            if not user_emails.exists():
                return Response(
                    {'error': 'No valid emails found for reprocessing'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Process each email
            processor = EmailProcessingService()
            results = []
            
            for email in user_emails:
                try:
                    # Prepare email data for processing
                    email_data = {
                        'subject': email.subject,
                        'body': email.raw_body,
                        'sender_name': email.from_name or ''
                    }
                    
                    # Process the email
                    result = processor.process_email_complete(email_data)
                    
                    if result['processing_status'] == 'success':
                        # Update the email with new processing results
                        if 'classification' in result:
                            classification = result['classification']
                            email.category = classification.get('category')
                            email.priority = classification.get('priority', 0)
                            email.needs_reply = classification.get('needs_reply', False)
                        
                        if 'summary' in result:
                            email.summary = result['summary']
                        
                        if 'suggested_reply' in result and result['suggested_reply']:
                            email.suggested_reply = result['suggested_reply']
                        
                        # Update processing status and reprocessing history
                        email.status = 'processed'
                        if email.processed_at is None:
                            email.processed_at = timezone.now()
                        email.reprocessed_at = timezone.now()
                        email.reprocessing_count += 1
                        email.save()
                        
                        results.append({
                            'email_id': email.id,
                            'status': 'success',
                            'category': email.category,
                            'priority': email.priority,
                            'needs_reply': email.needs_reply
                        })
                    else:
                        results.append({
                            'email_id': email.id,
                            'status': 'error',
                            'errors': result.get('errors', [])
                        })
                        
                except Exception as e:
                    logger.error(f"Reprocessing email {email.id} failed: {e}")
                    results.append({
                        'email_id': email.id,
                        'status': 'error',
                        'errors': [str(e)]
                    })
            
            # Calculate summary statistics
            successful = sum(1 for r in results if r['status'] == 'success')
            failed = len(results) - successful
            
            return Response({
                'status': 'success',
                'message': f'Batch reprocessing completed: {successful} successful, {failed} failed',
                'data': {
                    'total_emails': len(results),
                    'successful': successful,
                    'failed': failed,
                    'results': results
                }
            })
            
        except Exception as e:
            logger.error(f"Batch reprocessing failed: {e}")
            return Response(
                {'error': f'Batch reprocessing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get email processing statistics for the user."""
        try:
            user = request.user
            
            # Get all emails for the user
            all_emails = ProcessedEmail.objects.filter(account__user=user)
            
            # Calculate statistics
            total_emails = all_emails.count()
            pending_emails = all_emails.filter(status='pending').count()
            processed_emails = all_emails.filter(status='processed').count()
            error_emails = all_emails.filter(status='error').count()
            
            # Category distribution
            categories = all_emails.values('category').annotate(count=Count('category'))
            category_stats = {cat['category']: cat['count'] for cat in categories if cat['category']}
            
            # Priority distribution
            priorities = all_emails.values('priority').annotate(count=Count('priority'))
            priority_stats = {str(p['priority']): p['count'] for p in priorities}
            
            return Response({
                'status': 'success',
                'data': {
                    'total_emails': total_emails,
                    'pending_emails': pending_emails,
                    'processed_emails': processed_emails,
                    'error_emails': error_emails,
                    'category_distribution': category_stats,
                    'priority_distribution': priority_stats
                }
            })
            
        except Exception as e:
            logger.error(f"Get email statistics failed: {e}")
            return Response(
                {'error': f'Failed to get statistics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def send_demo_reply(self, request):
        """Send a demo reply (for testing email processing workflow)."""
        try:
            to_email = request.data.get('to_email')
            subject = request.data.get('subject')
            content = request.data.get('content')
            
            if not all([to_email, subject, content]):
                return Response(
                    {'error': 'to_email, subject, and content are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # In demo mode, just simulate sending
            logger.info(f"Demo reply prepared - To: {to_email}, Subject: {subject}")
            
            return Response({
                'status': 'success',
                'message': 'Demo reply prepared successfully',
                'data': {
                    'to_email': to_email,
                    'subject': subject,
                    'content_length': len(content),
                    'demo_mode': True
                }
            })
            
        except Exception as e:
            logger.error(f"Send demo reply failed: {e}")
            return Response(
                {'error': f'Failed to send demo reply: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FollowUpEmailViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet for follow-up emails with full CRUD operations.
    """
    serializer_class = FollowUpEmailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return follow-up emails for the authenticated user only."""
        return FollowUpEmail.objects.filter(
            original_email__account__user=self.request.user
        ).order_by('-created_at')
    
    @extend_schema(
        summary="Send follow-up email",
        description="Send a follow-up email"
    )
    @action(detail=True, methods=['post'])
    def send(self, request, pk: int = None):
        """Send a follow-up email."""
        try:
            follow_up = self.get_object()
            
            # Send follow-up email
            follow_up_service = FollowUpAutomationService()
            success = follow_up_service.send_follow_up_email(follow_up)
            
            if success:
                return Response({
                    'status': 'success',
                    'message': 'Follow-up email sent successfully',
                    'follow_up': self.get_serializer(follow_up).data
                })
            else:
                return Response(
                    {'error': 'Failed to send follow-up email'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            logger.error(f"Send follow-up email failed: {e}")
            return Response(
                {'error': f'Failed to send email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FollowUpViewSet(viewsets.ViewSet):
    """
    ViewSet for follow-up automation operations.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def candidates(self, request):
        """Get emails that are candidates for follow-up."""
        try:
            user = request.user
            follow_up_service = FollowUpAutomationService()
            
            # Get emails needing follow-up
            candidates = follow_up_service.get_emails_needing_follow_up(user.id)
            
            candidates_data = []
            for email in candidates:
                base_date = email.processed_at or email.received_at
                days_passed = (timezone.now() - base_date).days
                
                candidates_data.append({
                    'email_id': email.id,
                    'subject': email.subject,
                    'from_address': email.from_address,
                    'category': email.category,
                    'priority': email.priority,
                    'received_at': email.received_at.isoformat(),
                    'days_passed': days_passed,
                    'recommended_action': 'follow_up'
                })
            
            return Response({
                'status': 'success',
                'data': candidates_data,
                'total_candidates': len(candidates_data)
            })
            
        except Exception as e:
            logger.error(f"Get follow-up candidates failed: {e}")
            return Response(
                {'error': f'Failed to get candidates: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def create_draft(self, request):
        """Create a draft follow-up email."""
        try:
            user = request.user
            email_id = request.data.get('email_id')
            
            if not email_id:
                return Response(
                    {'error': 'email_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the original email (ensure it belongs to the user)
            try:
                original_email = ProcessedEmail.objects.get(
                    id=email_id,
                    account__user=user
                )
            except ProcessedEmail.DoesNotExist:
                return Response(
                    {'error': 'Email not found or access denied'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create follow-up draft
            follow_up_service = FollowUpAutomationService()
            follow_up = follow_up_service.create_follow_up_draft(original_email)
            
            return Response({
                'status': 'success',
                'message': 'Follow-up draft created successfully',
                'follow_up': {
                    'id': follow_up.id,
                    'content': follow_up.content,
                    'status': follow_up.status,
                    'created_at': follow_up.created_at.isoformat(),
                    'original_email_id': original_email.id,
                    'original_subject': original_email.subject
                }
            })
            
        except Exception as e:
            logger.error(f"Create follow-up draft failed: {e}")
            return Response(
                {'error': f'Failed to create draft: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send a follow-up email."""
        try:
            user = request.user
            
            # Get the follow-up email (ensure it belongs to the user)
            try:
                follow_up = FollowUpEmail.objects.get(
                    id=pk,
                    original_email__account__user=user
                )
            except FollowUpEmail.DoesNotExist:
                return Response(
                    {'error': 'Follow-up email not found or access denied'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Send follow-up email
            follow_up_service = FollowUpAutomationService()
            success = follow_up_service.send_follow_up_email(follow_up)
            
            if success:
                return Response({
                    'status': 'success',
                    'message': 'Follow-up email sent successfully',
                    'follow_up': {
                        'id': follow_up.id,
                        'status': follow_up.status,
                        'sent_at': follow_up.sent_at.isoformat() if follow_up.sent_at else None
                    }
                })
            else:
                return Response(
                    {'error': 'Failed to send follow-up email'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            logger.error(f"Send follow-up email failed: {e}")
            return Response(
                {'error': f'Failed to send email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def process_automated(self, request):
        """Process all automated follow-ups for the user."""
        try:
            user = request.user
            follow_up_service = FollowUpAutomationService()
            
            # Process automated follow-ups
            results = follow_up_service.process_automated_follow_ups(user.id)
            
            return Response({
                'status': 'success',
                'message': 'Automated follow-ups processed successfully',
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Process automated follow-ups failed: {e}")
            return Response(
                {'error': f'Failed to process follow-ups: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get follow-up statistics for the user."""
        try:
            user = request.user
            follow_up_service = FollowUpAutomationService()
            
            # Get statistics
            stats = follow_up_service.get_follow_up_statistics(user.id)
            
            return Response({
                'status': 'success',
                'data': stats
            })
            
        except Exception as e:
            logger.error(f"Get follow-up statistics failed: {e}")
            return Response(
                {'error': f'Failed to get statistics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def drafts(self, request):
        """Get all follow-up drafts for the user."""
        try:
            user = request.user
            
            # Get all follow-up emails (drafts, sent, error)
            follow_ups = FollowUpEmail.objects.filter(
                original_email__account__user=user
            ).order_by('-created_at')
            
            drafts_data = []
            for follow_up in follow_ups:
                drafts_data.append({
                    'id': follow_up.id,
                    'content': follow_up.content,
                    'status': follow_up.status,
                    'created_at': follow_up.created_at.isoformat(),
                    'sent_at': follow_up.sent_at.isoformat() if follow_up.sent_at else None,
                    'original_email_id': follow_up.original_email.id,
                    'original_subject': follow_up.original_email.subject,
                    'original_from_address': follow_up.original_email.from_address,
                    'error_message': follow_up.error_message
                })
            
            return Response({
                'status': 'success',
                'data': drafts_data
            })
            
        except Exception as e:
            logger.error(f"Get follow-up drafts failed: {e}")
            return Response(
                {'error': f'Failed to get drafts: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for user dashboard operations.
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get comprehensive dashboard data for the authenticated user."""
        try:
            user = request.user
            
            # Get user's email accounts
            accounts = EmailAccount.objects.filter(user=user)
            
            # Get all emails for the user
            all_emails = ProcessedEmail.objects.filter(account__user=user)
            
            # Calculate statistics
            total_emails = all_emails.count()
            pending_emails = all_emails.filter(status='pending').count()
            processed_emails = all_emails.filter(status='processed').count()
            error_emails = all_emails.filter(status='error').count()
            
            # Category distribution
            categories = all_emails.values('category').annotate(count=Count('category'))
            category_stats = {cat['category']: cat['count'] for cat in categories if cat['category']}
            
            # Priority distribution
            priorities = all_emails.values('priority').annotate(count=Count('priority'))
            priority_stats = {str(p['priority']): p['count'] for p in priorities}
            
            # Recent emails (last 10)
            recent_emails = all_emails.order_by('-received_at')[:10]
            recent_emails_data = []
            
            for email in recent_emails:
                recent_emails_data.append({
                    'id': email.id,
                    'subject': email.subject,
                    'from_address': email.from_address,
                    'category': email.category,
                    'priority': email.priority,
                    'status': email.status,
                    'needs_reply': email.needs_reply,
                    'received_at': email.received_at.isoformat(),
                    'processed_at': email.processed_at.isoformat() if email.processed_at else None
                })
            
            # Emails needing reply
            emails_needing_reply = all_emails.filter(needs_reply=True, status='processed').count()
            
            return Response({
                'status': 'success',
                'data': {
                    'user_info': {
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    },
                    'statistics': {
                        'total_accounts': accounts.count(),
                        'total_emails': total_emails,
                        'pending_emails': pending_emails,
                        'processed_emails': processed_emails,
                        'error_emails': error_emails,
                        'emails_needing_reply': emails_needing_reply,
                        'category_distribution': category_stats,
                        'priority_distribution': priority_stats
                    },
                    'recent_emails': recent_emails_data
                }
            })
            
        except Exception as e:
            logger.error(f"Get user dashboard failed: {e}")
            return Response(
                {'error': f'Failed to get dashboard: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SystemViewSet(viewsets.ViewSet):
    """
    ViewSet for system-level operations.
    """
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """Comprehensive health check for all services."""
        health_status = {
            'timestamp': timezone.now().isoformat(),
            'services': {}
        }
        
        # Check Ollama service
        try:
            ollama = OllamaService()
            test_response = ollama.generate("Hello", options={'num_predict': 5})
            health_status['services']['ollama'] = {
                'status': 'healthy',
                'response_time': 'fast',
                'test_response': test_response[:50] + '...' if len(test_response) > 50 else test_response
            }
        except Exception as e:
            health_status['services']['ollama'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Check database
        try:
            email_count = ProcessedEmail.objects.count()
            account_count = EmailAccount.objects.count()
            health_status['services']['database'] = {
                'status': 'healthy',
                'email_count': email_count,
                'account_count': account_count
            }
        except Exception as e:
            health_status['services']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Overall health
        all_healthy = all(
            service.get('status') == 'healthy' 
            for service in health_status['services'].values()
        )
        
        health_status['overall_status'] = 'healthy' if all_healthy else 'unhealthy'
        
        return Response(health_status)