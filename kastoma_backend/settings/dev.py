"""
Development settings for kastoma_backend project.

This file contains settings specific to the development environment.
It imports base settings and overrides them for local development.

Features enabled in development:
- Debug mode
- Django Debug Toolbar
- Extended logging
- SQLite database (for quick setup)
- CORS for local frontend development
"""

import os
from .base import *
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# Override base settings for development
DEBUG = True

# Development-specific installed apps
INSTALLED_APPS += [
    'django_extensions',  # Useful development tools
    'debug_toolbar',      # Django Debug Toolbar
]

# Development-specific middleware
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# Database override for development
# Prefer SQLite for quick setup, but can use MySQL if configured in .env
if not os.getenv('DB_ENGINE') or os.getenv('DB_ENGINE') == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Django Debug Toolbar configuration
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Show debug toolbar only if not running in Docker
import socket
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS += [ip[: ip.rfind(".")] + ".1" for ip in ips]

# More permissive CORS for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Email backend for development (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Cache configuration for development (dummy cache)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Development-specific logging
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['kastoma_backend']['level'] = 'DEBUG'

# Static files configuration for development
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Django REST Framework settings for development
REST_FRAMEWORK.update({
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Enable browsable API
    ],
})

# Development-specific spectacular settings
SPECTACULAR_SETTINGS.update({
    'SERVE_INCLUDE_SCHEMA': True,  # Include schema endpoint in development
})

print(f"Development settings loaded")
print(f"Debug mode: {DEBUG}")
print(f"Database: {DATABASES['default']['ENGINE']}")
print(f"Static files: {STATIC_URL}")
print(f"Media files: {MEDIA_URL}")