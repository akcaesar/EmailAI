from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import authentication as auth
from .viewsets import (
    EmailAccountViewSet,
    EmailProcessingViewSet,
    SystemViewSet,
    ProcessedEmailViewSet
)

# Create a router and register core viewsets only
router = DefaultRouter()
router.register(r'accounts', EmailAccountViewSet, basename='accounts')
router.register(r'emails', ProcessedEmailViewSet, basename='emails')
router.register(r'processing', EmailProcessingViewSet, basename='processing')
router.register(r'system', SystemViewSet, basename='system')
router.register(r'auth', auth.AuthViewSet, basename='auth')

urlpatterns = [
    # Core API endpoints
    path('v1/', include(router.urls)),
]