from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import authentication as auth
from .viewsets import (
    EmailAccountViewSet,
    ProcessedEmailViewSet,
    FollowUpViewSet,
    EmailProcessingViewSet,
    FollowUpViewSet,
    UserDashboardViewSet,
    SystemViewSet
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'accounts', EmailAccountViewSet, basename='accounts')
router.register(r'emails', ProcessedEmailViewSet, basename='emails')
router.register(r'follow-up-emails', FollowUpViewSet, basename='follow-up-emails')
router.register(r'processing', EmailProcessingViewSet, basename='processing')
router.register(r'follow-ups', FollowUpViewSet, basename='follow-ups')
router.register(r'dashboard', UserDashboardViewSet, basename='dashboard')
router.register(r'system', SystemViewSet, basename='system')
router.register(r'auth', auth.AuthViewSet, basename='auth')

urlpatterns = [
    # Landing and test endpoints
    path('', views.LandingView.as_view(), name='landing'),
    path('test-ollama/', views.OllamaTestView.as_view(), name='test-ollama'),
    
    # # Authentication endpoints
    # path('auth/register/', auth.UserRegistrationViewSet.as_view({'post': 'create'}), name='register'),

    
    # ViewSet-based API endpoints
    path('v1/', include(router.urls)),
]