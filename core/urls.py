"""
Core app URL configuration.

This module contains base URL patterns that can be
included in other app URLconfs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    SiteSettingViewSet,
    PageViewViewSet,
    EmailTemplateViewSet,
    APILogViewSet
)

# Create a router instance for the core app
router = DefaultRouter()
router.register(r'site-settings', SiteSettingViewSet, basename='sitesetting')
router.register(r'page-views', PageViewViewSet, basename='pageview')
router.register(r'email-templates', EmailTemplateViewSet, basename='emailtemplate')
router.register(r'api-logs', APILogViewSet, basename='apilog')

app_name = 'core'

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]