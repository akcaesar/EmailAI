"""
User authentication and authorization for EmailAI system.

Author: Akshay NS
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, LoginSerializer, UserSerializer
from drf_spectacular.utils import extend_schema
import logging

logger = logging.getLogger(__name__)

class AuthViewSet(viewsets.ViewSet):
    """
    simmple viewest for differnt auth methods, login, logout
    register, reset password, etc.
    """
    
    @extend_schema(request=UserRegistrationSerializer, responses=UserRegistrationSerializer)
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'User registered successfully',
            'user': serializer.data,
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

    

