"""
User authentication and authorization for EmailAI system.

Author: Akshay NS
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .serializers import (
    UserRegistrationSerializer, LoginSerializer, LogoutSerializer, UserSerializer, 
    DeleteUserSerializer, DeleteAllUsersSerializer, SuperuserCreationSerializer, AdminUserListSerializer
)
from drf_spectacular.utils import extend_schema
import logging

logger = logging.getLogger(__name__)

class AuthViewSet(viewsets.ViewSet):
    """
    simmple viewest for differnt auth methods, login, logout
    register, reset password, etc.
    """
    
    @extend_schema(request=UserRegistrationSerializer, responses=UserSerializer)
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'User registered successfully',
            'user': UserSerializer(serializer.instance).data,
            'status': status.HTTP_201_CREATED
        })
    
    @extend_schema(request=LoginSerializer, responses=UserSerializer)
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            if user is not None:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Login successful',
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    },
                    'status': status.HTTP_200_OK
                })
            else:
                return Response({
                    'message': 'Invalid credentials',
                    'status': status.HTTP_401_UNAUTHORIZED
                }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @extend_schema(request=LogoutSerializer, responses={'200': {'message': 'Logout successful'}})
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        logout by blacklisting the refresh token
        """
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            refresh_token = serializer.validated_data['refresh']
            if not refresh_token:
                return Response({
                    'message': 'Refresh token is required',
                    'status': status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'message': 'Logout successful',
                'status': status.HTTP_200_OK
            })
        except TokenError as e:
            logger.error(f"Token blacklist error: {e}")
            return Response({
                'message': 'Invalid refresh token',
                'status': status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected logout error: {e}")
            return Response({
                'message': 'Logout failed',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(request=DeleteUserSerializer, responses={'200': {'message': 'User deleted successfully'}})
    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_user(self, request):
        """
        Delete the authenticated user account after password confirmation
        """
        serializer = DeleteUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = request.user
            
            # Verify password before deletion
            if not user.check_password(serializer.validated_data['password']):
                return Response({
                    'message': 'Invalid password',
                    'status': status.HTTP_401_UNAUTHORIZED
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Blacklist all user's tokens before deletion
            try:
                refresh_token = request.data.get('refresh')
                if refresh_token:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
            except:
                pass  # Continue with deletion even if token blacklist fails
            
            user_id = user.id
            user.delete()
            
            logger.info(f"User {user_id} deleted their account")
            return Response({
                'message': 'User account deleted successfully',
                'status': status.HTTP_200_OK
            })
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return Response({
                'message': 'Failed to delete user account',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(request=DeleteAllUsersSerializer, responses={'200': {'message': 'All users deleted successfully'}})
    @action(detail=False, methods=['delete'], permission_classes=[IsAdminUser])
    def delete_all_users(self, request):
        """
        Delete all users (admin only) - DANGEROUS OPERATION
        """
        serializer = DeleteAllUsersSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from django.db import transaction, connection
            
            # Get count before deletion
            admin_count = User.objects.filter(is_superuser=True).count()
            non_admin_users = User.objects.filter(is_superuser=False)
            deleted_count = non_admin_users.count()
            
            if deleted_count == 0:
                return Response({
                    'message': 'No non-admin users to delete.',
                    'deleted_count': 0,
                    'preserved_admins': admin_count,
                    'status': status.HTTP_200_OK
                })
            
            with connection.cursor() as cursor:
                # Disable foreign key constraints temporarily
                cursor.execute("PRAGMA foreign_keys = OFF")
                
                try:
                    with transaction.atomic():
                        # Delete users directly - SQLite will handle it without foreign key checks
                        result = non_admin_users.delete()
                        total_deleted = result[0]
                        breakdown = result[1]
                finally:
                    # Re-enable foreign key constraints
                    cursor.execute("PRAGMA foreign_keys = ON")
            
            logger.warning(f"Admin {request.user.username} deleted {deleted_count} users and their related data. {admin_count} superusers preserved. Details: {breakdown}")
            
            return Response({
                'message': f'Successfully deleted {deleted_count} users and their related data. {admin_count} superusers preserved.',
                'total_deleted': total_deleted,
                'deletion_breakdown': breakdown,
                'preserved_admins': admin_count,
                'status': status.HTTP_200_OK
            })
            
        except Exception as e:
            logger.error(f"Error in bulk user deletion: {e}")
            return Response({
                'message': f'Failed to delete users: {str(e)}',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(request=SuperuserCreationSerializer, responses=UserSerializer)
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def create_superuser(self, request):
        """
        Create a new superuser (admin only)
        """
        serializer = SuperuserCreationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create superuser
            user = User.objects.create_superuser(
                username=serializer.validated_data['username'],
                email=serializer.validated_data.get('email', ''),
                password=serializer.validated_data['password'],
                first_name=serializer.validated_data.get('first_name', ''),
                last_name=serializer.validated_data.get('last_name', '')
            )
            
            logger.info(f"Superuser {user.username} created by admin {request.user.username}")
            
            return Response({
                'message': 'Superuser created successfully',
                'user': UserSerializer(user).data,
                'status': status.HTTP_201_CREATED
            })
            
        except Exception as e:
            logger.error(f"Error creating superuser: {e}")
            return Response({
                'message': 'Failed to create superuser',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(responses=AdminUserListSerializer)
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def admin_user_list(self, request):
        """
        Get all users with admin information (admin only)
        """
        try:
            users = User.objects.all().select_related().prefetch_related('email_accounts')
            
            users_data = []
            for user in users:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'date_joined': user.date_joined.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'email_accounts_count': user.email_accounts.count(),
                    'processed_emails_count': sum(account.emails.count() for account in user.email_accounts.all())
                }
                users_data.append(user_data)
            
            # Get system statistics
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            superusers = User.objects.filter(is_superuser=True).count()
            staff_users = User.objects.filter(is_staff=True).count()
            
            return Response({
                'status': 'success',
                'data': {
                    'users': users_data,
                    'statistics': {
                        'total_users': total_users,
                        'active_users': active_users,
                        'superusers': superusers,
                        'staff_users': staff_users
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting admin user list: {e}")
            return Response({
                'message': 'Failed to get user list',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(responses={'200': {'message': 'User status updated'}})
    @action(detail=False, methods=['patch'], permission_classes=[IsAdminUser])
    def toggle_user_status(self, request):
        """
        Toggle user active status (admin only)
        """
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({
                'message': 'user_id is required',
                'status': status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
            
            # Prevent deactivating the requesting admin
            if user.id == request.user.id:
                return Response({
                    'message': 'Cannot deactivate your own account',
                    'status': status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Toggle active status
            user.is_active = not user.is_active
            user.save()
            
            action = 'activated' if user.is_active else 'deactivated'
            logger.info(f"User {user.username} {action} by admin {request.user.username}")
            
            return Response({
                'message': f'User {action} successfully',
                'user': UserSerializer(user).data,
                'status': status.HTTP_200_OK
            })
            
        except User.DoesNotExist:
            return Response({
                'message': 'User not found',
                'status': status.HTTP_404_NOT_FOUND
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error toggling user status: {e}")
            return Response({
                'message': 'Failed to update user status',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


