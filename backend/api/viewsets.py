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
from typing import Optional

# Optional drf-spectacular imports for API documentation
try:
    from drf_spectacular.utils import extend_schema
except ImportError:
    def extend_schema(**kwargs):
        def decorator(func):
            return func
        return decorator

from .models import ProcessedEmail, EmailAccount, FollowUpEmail
from .serializers import (
    EmailAccountSerializer, EmailAccountCreateSerializer,
    ProcessedEmailSerializer, FollowUpEmailSerializer,
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
    def fetch_emails(self, request, pk: Optional[int] = None):
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
    def generate_reply(self, request, pk: Optional[int] = None):
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


class EmailProcessingViewSet(viewsets.ViewSet):
    """
    ViewSet for email processing operations.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Process email comprehensively",
        description="Process a single email comprehensively using Celery"
    )
    @action(detail=False, methods=['post'])
    def process_comprehensive(self, request) -> Response:
        """Process a single email comprehensively using Celery."""
        try:
            email_data = request.data
            
            # Validate required fields
            if not email_data.get('subject') or not email_data.get('body'):
                return Response(
                    {'error': 'Subject and body are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
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
    
    @extend_schema(
        summary="Get processing statistics",
        description="Get email processing statistics for the authenticated user"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request) -> Response:
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


class FollowUpViewSet(viewsets.ViewSet):
    """
    ViewSet for follow-up automation operations.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Get follow-up candidates",
        description="Get emails that are candidates for follow-up"
    )
    @action(detail=False, methods=['get'])
    def candidates(self, request) -> Response:
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
    
    @extend_schema(
        summary="Create follow-up draft",
        description="Create a draft follow-up email",
        request=FollowUpDraftSerializer
    )
    @action(detail=False, methods=['post'])
    def create_draft(self, request) -> Response:
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

    @extend_schema(
        summary="Get follow-up statistics",
        description="Get follow-up statistics for the authenticated user"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request) -> Response:
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


class UserDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for user dashboard operations.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get user dashboard",
        description="Get comprehensive dashboard data for the authenticated user"
    )
    def list(self, request) -> Response:
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
    
    @extend_schema(
        summary="System health check",
        description="Comprehensive health check for all services"
    )
    @action(detail=False, methods=['get'])
    def health(self, request) -> Response:
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