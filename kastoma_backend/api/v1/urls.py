"""
API v1 URL configuration.

This module contains the routing for version 1 of the API,
including all app-specific endpoints with DRF routers.

Endpoints:
- /products/ - Product management (CRUD)
- /categories/ - Category management (CRUD)
- /users/ - User management 
- /auth/ - Authentication endpoints

All endpoints are automatically documented via drf-spectacular.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import viewsets from each app
from products.views import ProductViewSet, CategoryViewSet
from users.views import UserViewSet

# Create the main router
router = DefaultRouter()

# Register viewsets for automatic URL routing  
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'users', UserViewSet, basename='user')

app_name = 'v1'

urlpatterns = [
    # Include all router URLs
    path('', include(router.urls)),
    
    # App-specific URL includes for custom endpoints
    path('', include('users.urls')),  # This includes auth endpoints
    path('', include('orders.urls')),  # This includes order and cart endpoints
    path('core/', include('core.urls')),  # Core management endpoints
]