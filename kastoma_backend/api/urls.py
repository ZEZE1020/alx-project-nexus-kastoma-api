"""
Main API URL configuration.

This module contains the routing for all API versions and provides
a centralized place to manage API endpoints.

URL Structure:
- /api/v1/ - Version 1 API endpoints
- Future versions can be added here (v2, v3, etc.)
"""

from django.urls import path, include

app_name = 'api'

urlpatterns = [
    # API Version 1
    path('v1/', include('kastoma_backend.api.v1.urls')),
]