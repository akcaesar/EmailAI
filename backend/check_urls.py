#!/usr/bin/env python
"""
Quick script to check available URLs
"""
import sys
import os

# Add the backend directory to Python path
sys.path.append('/home/akshay/Akshay-CL-Projects/backend')

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emailai.settings')

import django
django.setup()

from django.urls import reverse
from django.conf import settings

print("Available URLs:")
print("=" * 40)

# Check some key URLs
urls_to_check = [
    'api:accounts-list',
    'api:dashboard-list', 
    'api:emails-list',
    'api:register',
    'api:login',
    'api:schema',
    'api:swagger-ui',
]

for url_name in urls_to_check:
    try:
        url = reverse(url_name)
        print(f"✓ {url_name}: {url}")
    except Exception as e:
        print(f"✗ {url_name}: {e}")

print("\nDjango settings:")
print(f"DEBUG: {settings.DEBUG}")
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"CORS_ALLOW_ALL_ORIGINS: {getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', 'Not set')}")