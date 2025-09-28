"""
Settings package for kastoma_backend project.

This package contains environment-specific Django settings:
- base.py: Common settings shared across environments
- dev.py: Development-specific settings
- prod.py: Production-specific settings

Usage:
- Development: DJANGO_SETTINGS_MODULE=kastoma_backend.settings.dev
- Production: DJANGO_SETTINGS_MODULE=kastoma_backend.settings.prod

The default environment is development.
"""

import os

# Default to development settings if not specified
ENVIRONMENT = os.getenv('DJANGO_ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    from .prod import *
elif ENVIRONMENT == 'development':
    from .dev import *
else:
    # Fallback to development settings
    from .dev import *