"""
Users app views.

API views for user authentication, registration, profile management,
and JWT token handling using Django REST Framework.
"""

from typing import TYPE_CHECKING, Any, Dict
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from core.views import BaseModelViewSet

if TYPE_CHECKING:
    from django.http import HttpRequest
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
    UserListSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
)

User = get_user_model()


class UserRegistrationView(APIView):
    """
    API view for user registration.
    
    Allows new users to create accounts with email verification.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def post(self, request):
        """Create a new user account."""
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Send welcome email (optional)
            if hasattr(settings, 'SEND_WELCOME_EMAIL') and settings.SEND_WELCOME_EMAIL:
                self.send_welcome_email(user)
            
            # Return user data (excluding password)
            user_serializer = UserSerializer(user)
            return Response(
                {
                    'message': 'Account created successfully.',
                    'user': user_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_welcome_email(self, user):
        """Send welcome email to new user."""
        try:
            send_mail(
                subject='Welcome to Kastoma!',
                message=f'Hello {user.first_name},\n\nWelcome to Kastoma! Your account has been created successfully.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            # Log error in production
            pass


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token view that includes user data in response.
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(BaseModelViewSet):
    """
    ViewSet for user management.
    
    Provides:
    - List users (admin only)
    - Retrieve user profile
    - Update user profile
    - Delete user account
    - Custom actions for profile operations
    """
    queryset = User.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return UserListSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == 'list':
            # Only admin can list all users
            permission_classes = [permissions.IsAdminUser]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            # Users can only access their own profile
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'destroy':
            # Users can delete their own account or admin can delete any
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_object(self):
        """
        Override to allow users to access their own profile with 'me' pk.
        """
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object()
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        if self.request.user.is_staff:
            return User.objects.all()
        
        # Regular users can only see their own profile
        return User.objects.filter(pk=self.request.user.pk)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user's profile."""
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        
        if serializer.is_valid():
            serializer.save()
            user_serializer = UserSerializer(request.user)
            return Response(user_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user's password."""
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Password changed successfully.'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def delete_account(self, request):
        """Delete current user's account."""
        user = request.user
        user.is_active = False
        user.save()
        
        return Response(
            {'message': 'Account deactivated successfully.'},
            status=status.HTTP_200_OK
        )


class PasswordResetView(APIView):
    """
    API view for password reset request.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetSerializer
    
    def post(self, request):
        """Send password reset email."""
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            # Type ignore to work around serializer type inference issues
            email = serializer.validated_data['email']  # type: ignore
            
            # In a real implementation, you would:
            # 1. Generate a password reset token
            # 2. Send email with reset link
            # 3. Store token in database or cache
            
            # For now, just return success message
            return Response(
                {'message': 'Password reset email sent.'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    API view for password reset confirmation.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer
    
    def post(self, request, token):
        """Confirm password reset with token."""
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            # In a real implementation, you would:
            # 1. Validate the reset token
            # 2. Find the user associated with the token
            # 3. Update the user's password
            # 4. Invalidate the token
            
            # Type ignore to work around serializer type inference issues
            new_password = serializer.validated_data['new_password']  # type: ignore
            
            # TODO: Implement token validation and password update
            
            return Response(
                {'message': 'Password reset successfully.'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileViewSet(BaseModelViewSet):
    """
    ViewSet for extended user profile management.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Return UserProfileSerializer."""
        from .serializers import UserProfileSerializer
        return UserProfileSerializer
    
    def get_queryset(self):
        """Filter to user's own profile."""
        from .models import UserProfile
        return UserProfile.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get or create user's profile."""
        from .models import UserProfile
        try:
            return UserProfile.objects.get(user=self.request.user)
        except UserProfile.DoesNotExist:
            return UserProfile.objects.create(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile."""
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """Update current user's profile."""
        profile = self.get_object()
        serializer = self.get_serializer(
            profile,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
