"""
URL configuration for emailai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

def landing_page(request):
    """Simple landing page for the EmailAI API."""
    return JsonResponse({
        'message': '📬 Welcome to AI Email Assistant for Job Applications',
        'version': 'v1.0',
        'description': 'An intelligent, local-first assistant that reads your job application emails, classifies them using a local LLM, and automatically generates polished replies.',
        'endpoints': {
            'api_root': '/api/v1/',
            'admin': '/admin/',
            'documentation': {
                'swagger': '/api/swagger/',
                'redoc': '/api/redoc/',
                'schema': '/api/schema/'
            },
            'health_check': '/api/v1/system/health/',
            'test_ollama': '/api/test-ollama/'
        },
        'tech_stack': ['Django REST Framework', 'Ollama (local LLM)', 'SQLite'],
        'status': 'running'
    })

urlpatterns = [
    # Landing page
    path('', landing_page, name='landing_page'),
    
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),

    # API Documentation - Swagger/OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]