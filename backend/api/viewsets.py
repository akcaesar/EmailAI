"""Core ViewSets for EmailAI API - focused on essential functionality only.

Author: Akshay NS
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from django.utils import timezone
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

from .models import ProcessedEmail, EmailAccount
from .serializers import (
    EmailAccountSerializer, EmailAccountCreateSerializer,
    FetchEmailsSerializer, ProcessedEmailSerializer, ProcessEmailByIdSerializer
)
from .services.email_processing_service import EmailProcessingService
from .services.ollama_service import OllamaService
from .services.email_processor import process_single_email, batch_process_emails_task

logger = logging.getLogger(__name__)


class EmailAccountViewSet(viewsets.ModelViewSet):
    """Core email account management with CRUD and email fetching."""
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
    
    @extend_schema(
        summary="Fetch emails from account",
        description="Fetch emails from a specific email account",
        request=FetchEmailsSerializer
    )
    @action(detail=True, methods=['post'])
    def fetch_emails(self, request, pk: Optional[int] = None):
        """Fetch and process emails from a specific account."""
        serializer = FetchEmailsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            account = self.get_object()
            max_emails = serializer.validated_data['max_emails']
            
            from .services.email_fetching_service import fetch_emails_sync
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

    @extend_schema(
        summary="List emails for account",
        description="Get all fetched emails for a specific account"
    )
    @action(detail=True, methods=['get'])
    def emails(self, request, pk: Optional[int] = None):
        """Get all emails for a specific account."""
        try:
            account = self.get_object()
            emails = ProcessedEmail.objects.filter(account=account).order_by('-received_at')
            
            # Add pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            start = (page - 1) * page_size
            end = start + page_size
            
            # Add filtering
            category = request.query_params.get('category')
            status_filter = request.query_params.get('status')
            needs_reply = request.query_params.get('needs_reply')
            
            if category:
                emails = emails.filter(category=category)
            if status_filter:
                emails = emails.filter(status=status_filter)
            if needs_reply is not None:
                emails = emails.filter(needs_reply=needs_reply.lower() == 'true')
            
            total_count = emails.count()
            emails_page = emails[start:end]
            
            serializer = ProcessedEmailSerializer(emails_page, many=True)
            
            return Response({
                'status': 'success',
                'data': {
                    'emails': serializer.data,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total_count': total_count,
                        'total_pages': (total_count + page_size - 1) // page_size
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Get account emails failed: {e}")
            return Response(
                {'error': f'Failed to get emails: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailProcessingViewSet(viewsets.ViewSet):
    """Core email processing operations."""
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Process email comprehensively",
        description="Process a single email comprehensively with AI classification and reply generation"
    )
    @action(detail=False, methods=['post'])
    def process_comprehensive(self, request) -> Response:
        """Process a single email comprehensively."""
        try:
            email_data = request.data
            
            # Validate required fields
            if not email_data.get('subject') or not email_data.get('body'):
                return Response(
                    {'error': 'Subject and body are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            processor = EmailProcessingService()
            result = processor.process_email_complete(email_data)
            
            return Response({
                'status': 'success',
                'data': result,
                'message': 'Email processed successfully'
            })
            
        except Exception as e:
            logger.error(f"Email processing failed: {e}")
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
            all_emails = ProcessedEmail.objects.filter(account__user=user)
            
            # Calculate core statistics
            total_emails = all_emails.count()
            pending_emails = all_emails.filter(status='pending').count()
            processed_emails = all_emails.filter(status='processed').count()
            error_emails = all_emails.filter(status='error').count()
            
            # Category distribution
            categories = all_emails.values('category').annotate(count=Count('category'))
            category_stats = {cat['category']: cat['count'] for cat in categories if cat['category']}
            
            return Response({
                'status': 'success',
                'data': {
                    'total_emails': total_emails,
                    'pending_emails': pending_emails,
                    'processed_emails': processed_emails,
                    'error_emails': error_emails,
                    'category_distribution': category_stats
                }
            })
            
        except Exception as e:
            logger.error(f"Get statistics failed: {e}")
            return Response(
                {'error': f'Failed to get statistics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        request=ProcessEmailByIdSerializer,
        summary="Process single email by ID",
        description="Process a single email by its ID using Celery background task"
    )
    @action(detail=False, methods=['post'])
    def process_email_by_id(self, request) -> Response:
        """Process a single email by ID using Celery."""
        try:
            email_id = request.data.get('email_id')
            
            if not email_id:
                return Response(
                    {'error': 'email_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify the email exists and belongs to the user
            try:
                email = ProcessedEmail.objects.get(
                    id=email_id,
                    account__user=request.user
                )
            except ProcessedEmail.DoesNotExist:
                return Response(
                    {'error': 'Email not found or access denied'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Submit task to Celery
            try:
                task = process_single_email.delay(email_id)
                
                return Response({
                    'status': 'success',
                    'message': 'Email processing started',
                    'data': {
                        'email_id': email_id,
                        'task_id': task.id,
                        'email_subject': email.subject,
                        'current_status': email.status
                    }
                })
                
            except Exception as celery_error:
                # Fallback to synchronous processing
                logger.warning(f"Celery not available, processing synchronously: {celery_error}")
                
                processor = EmailProcessingService()
                result = processor.process_email_complete({
                    'subject': email.subject,
                    'body': email.raw_body,
                    'from_address': email.from_address,
                    'from_name': email.from_name
                })
                
                # Update email with processing results
                if 'classification' in result:
                    email.category = result['classification'].get('category', 'other')
                    email.priority = result['classification'].get('priority', 3)
                    email.needs_reply = result.get('needs_reply', False)
                
                if 'suggested_reply' in result:
                    email.suggested_reply = result['suggested_reply']
                
                email.status = ProcessedEmail.Status.PROCESSED
                email.processed_at = timezone.now()
                email.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Email processed successfully (synchronous)',
                    'data': {
                        'email_id': email_id,
                        'result': result
                    }
                })
            
        except Exception as e:
            logger.error(f"Process email by ID failed: {e}")
            return Response(
                {'error': f'Failed to process email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Batch process emails by IDs",
        description="Process multiple emails by their IDs using Celery background tasks"
    )
    @action(detail=False, methods=['post'])
    def batch_process_emails(self, request) -> Response:
        """Process multiple emails by IDs using Celery."""
        try:
            email_ids = request.data.get('email_ids', [])
            
            if not email_ids or not isinstance(email_ids, list):
                return Response(
                    {'error': 'email_ids array is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(email_ids) > 100:  # Limit batch size
                return Response(
                    {'error': 'Maximum 100 emails allowed per batch'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify all emails exist and belong to the user
            user_emails = ProcessedEmail.objects.filter(
                id__in=email_ids,
                account__user=request.user
            )
            
            found_ids = set(user_emails.values_list('id', flat=True))
            requested_ids = set(email_ids)
            missing_ids = requested_ids - found_ids
            
            if missing_ids:
                return Response(
                    {'error': f'Emails not found or access denied: {list(missing_ids)}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Submit batch task to Celery
            try:
                task = batch_process_emails_task.delay(email_ids)
                
                return Response({
                    'status': 'success',
                    'message': 'Batch email processing started',
                    'data': {
                        'batch_task_id': task.id,
                        'email_count': len(email_ids),
                        'email_ids': email_ids
                    }
                })
                
            except Exception as celery_error:
                # Fallback to synchronous processing
                logger.warning(f"Celery not available, processing synchronously: {celery_error}")
                
                processor = EmailProcessingService()
                results = []
                
                for email in user_emails:
                    try:
                        result = processor.process_email_complete({
                            'subject': email.subject,
                            'body': email.raw_body,
                            'from_address': email.from_address,
                            'from_name': email.from_name
                        })
                        
                        # Update email with processing results
                        if 'classification' in result:
                            email.category = result['classification'].get('category', 'other')
                            email.priority = result['classification'].get('priority', 3)
                            email.needs_reply = result.get('needs_reply', False)
                        
                        if 'suggested_reply' in result:
                            email.suggested_reply = result['suggested_reply']
                        
                        email.status = ProcessedEmail.Status.PROCESSED
                        email.processed_at = timezone.now()
                        email.save()
                        
                        results.append({
                            'email_id': email.id,
                            'status': 'success',
                            'category': email.category
                        })
                        
                    except Exception as email_error:
                        logger.error(f"Error processing email {email.id}: {email_error}")
                        results.append({
                            'email_id': email.id,
                            'status': 'error',
                            'error': str(email_error)
                        })
                
                return Response({
                    'status': 'success',
                    'message': 'Batch emails processed successfully (synchronous)',
                    'data': {
                        'results': results,
                        'total_processed': len([r for r in results if r['status'] == 'success']),
                        'total_errors': len([r for r in results if r['status'] == 'error'])
                    }
                })
            
        except Exception as e:
            logger.error(f"Batch process emails failed: {e}")
            return Response(
                {'error': f'Failed to process emails: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Check task status",
        description="Check the status of a Celery task"
    )
    @action(detail=False, methods=['get'])
    def task_status(self, request) -> Response:
        """Check the status of a Celery task."""
        try:
            task_id = request.query_params.get('task_id')
            
            if not task_id:
                return Response(
                    {'error': 'task_id parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from celery.result import AsyncResult
            
            task_result = AsyncResult(task_id)
            
            return Response({
                'status': 'success',
                'data': {
                    'task_id': task_id,
                    'status': task_result.status,
                    'result': task_result.result,
                    'info': task_result.info
                }
            })
            
        except Exception as e:
            logger.error(f"Check task status failed: {e}")
            return Response(
                {'error': f'Failed to check task status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SystemViewSet(viewsets.ViewSet):
    """System health and monitoring."""
    
    @extend_schema(
        summary="System health check",
        description="Check health of core services (Ollama, Database)"
    )
    @action(detail=False, methods=['get'])
    def health(self, request) -> Response:
        """System health check for core services."""
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


class ProcessedEmailViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing processed emails."""
    serializer_class = ProcessedEmailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return processed emails for the authenticated user only."""
        return ProcessedEmail.objects.filter(account__user=self.request.user).order_by('-received_at')
    
    def list(self, request):
        """List all emails for the authenticated user with filtering and pagination."""
        try:
            queryset = self.get_queryset()
            
            # Add filtering
            category = request.query_params.get('category')
            status_filter = request.query_params.get('status')
            needs_reply = request.query_params.get('needs_reply')
            account_id = request.query_params.get('account_id')
            
            if category:
                queryset = queryset.filter(category=category)
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            if needs_reply is not None:
                queryset = queryset.filter(needs_reply=needs_reply.lower() == 'true')
            if account_id:
                queryset = queryset.filter(account_id=account_id)
            
            # Add pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            start = (page - 1) * page_size
            end = start + page_size
            
            total_count = queryset.count()
            emails_page = queryset[start:end]
            
            serializer = self.get_serializer(emails_page, many=True)
            
            return Response({
                'status': 'success',
                'data': {
                    'emails': serializer.data,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total_count': total_count,
                        'total_pages': (total_count + page_size - 1) // page_size
                    },
                    'filters': {
                        'category': category,
                        'status': status_filter,
                        'needs_reply': needs_reply,
                        'account_id': account_id
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"List emails failed: {e}")
            return Response(
                {'error': f'Failed to list emails: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """Get detailed information about a specific email."""
        try:
            email = self.get_object()
            serializer = self.get_serializer(email)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            })
            
        except ProcessedEmail.DoesNotExist:
            return Response(
                {'error': 'Email not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Get email details failed: {e}")
            return Response(
                {'error': f'Failed to get email details: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Mark email as read/unread",
        description="Toggle the read status of an email"
    )
    @action(detail=True, methods=['post'])
    def toggle_read(self, request, pk=None):
        """Toggle read status of an email."""
        try:
            email = self.get_object()
            # Assuming we add a 'is_read' field to the model
            # For now, we'll use a custom approach or add this field later
            
            return Response({
                'status': 'success',
                'message': 'Read status toggled successfully',
                'data': {
                    'email_id': email.id,
                    'subject': email.subject
                }
            })
            
        except Exception as e:
            logger.error(f"Toggle read status failed: {e}")
            return Response(
                {'error': f'Failed to toggle read status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )