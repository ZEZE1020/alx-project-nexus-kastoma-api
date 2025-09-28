"""
Users app URL configuration.

Defines REST API endpoints for user authentication, registration,
and profile management using Django REST Framework.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

# Create router for API endpoints
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.UserProfileViewSet, basename='userprofile')

app_name = 'users'

urlpatterns = [
    # Router URLs (user management)
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('auth/register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token-verify'),
    
    # Password reset endpoints
    path('auth/password-reset/', views.PasswordResetView.as_view(), name='password-reset'),
    path('auth/password-reset-confirm/<str:token>/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Profile management shortcuts
    path('profile/', views.UserViewSet.as_view({'get': 'me'}), name='user-profile'),
    path('profile/update/', views.UserViewSet.as_view({'put': 'update_profile', 'patch': 'update_profile'}), name='user-profile-update'),
    path('profile/change-password/', views.UserViewSet.as_view({'post': 'change_password'}), name='user-change-password'),
    path('profile/delete/', views.UserViewSet.as_view({'delete': 'delete_account'}), name='user-delete-account'),
]

# URL patterns available:
# 
# Authentication:
# POST   /api/v1/auth/register/                    - Register new user
# POST   /api/v1/auth/login/                       - Login (get JWT tokens)
# POST   /api/v1/auth/refresh/                     - Refresh JWT access token
# POST   /api/v1/auth/verify/                      - Verify JWT token
# POST   /api/v1/auth/password-reset/              - Request password reset
# POST   /api/v1/auth/password-reset-confirm/{token}/ - Confirm password reset
#
# User Management (Admin):
# GET    /api/v1/users/                            - List all users (admin only)
# GET    /api/v1/users/{id}/                       - Get user details (admin only)
# PUT    /api/v1/users/{id}/                       - Update user (admin only)
# DELETE /api/v1/users/{id}/                       - Delete user (admin only)
#
# Profile Management:
# GET    /api/v1/profile/                          - Get current user profile
# GET    /api/v1/users/me/                         - Get current user profile (alternative)
# PUT    /api/v1/profile/update/                   - Update current user profile
# PATCH  /api/v1/profile/update/                   - Partially update current user profile
# POST   /api/v1/profile/change-password/          - Change password
# DELETE /api/v1/profile/delete/                   - Deactivate account
#
# Custom Actions:
# GET    /api/v1/users/me/                         - Get current user profile
# PUT    /api/v1/users/update_profile/             - Update current user profile
# POST   /api/v1/users/change_password/            - Change password
# DELETE /api/v1/users/delete_account/             - Deactivate account