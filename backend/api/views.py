from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_field
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from .models import ProcessedEmail, EmailAccount, FollowUpEmail
from .services.ollama_service import OllamaService
from .services.email_processor import process_email_batch
from django.utils import timezone
from datetime import timedelta
import os, logging
from django.conf import settings
from .serializers import (
    ProcessedEmailSerializer, EmailAccountSerializer, FollowUpEmailSerializer
)


logger = logging.getLogger(__name__)


class OllamaTestView(GenericAPIView):
    """
    Test Ollama service connection and response.
    """
    serializer_class = None  # No input serialization needed
    def get(self, request):
          try:
              # Initialize the service
              ollama = OllamaService()
              # Test direct generation
              simple_response = ollama.generate(
                  prompt="Explain quantum computing to a 5 year old",
                  model=getattr(settings, 'OLLAMA_DEFAULT_MODEL', 'llava:latest')
              )

              # Test chat completion
              chat_response = ollama.chat(
                  messages=[
                      {
                          'role': 'user',
                          'content': "Explain quantum computing to a 5 year old"
                      }
                  ]
              )

              return Response({
                  'status': 'success',
                  'direct_generation': simple_response,
                  'chat_completion': chat_response,
                  'model_used': getattr(settings, 'OLLAMA_DEFAULT_MODEL', 'llava:latest')
              })

          except Exception as e:
              logger.error(f"Ollama test failed: {str(e)}", exc_info=True)
              return Response({
                  'status': 'error',
                  'message': str(e),
                  'hint': 'Is Ollama running? Try: ollama serve',
                  'settings_check': {
                      'OLLAMA_HOST': getattr(settings, 'OLLAMA_HOST', 'NOT SET'),
                      'OLLAMA_DEFAULT_MODEL': getattr(settings, 'OLLAMA_DEFAULT_MODEL', 'NOT SET')
                  }
              }, status=500)


class LandingView(GenericAPIView):
    """
    API landing page with basic information.
    """
    serializer_class = None  # No input serialization needed
    def get(self, request):
          return Response({
              'message': 'Welcome to the Email AI API',
              # 'documentation': 'https://docs.emailai.example.com',
              'status': 'API is running'
          })