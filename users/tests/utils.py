"""
Test utilities and factories for users app.

Provides helper functions and test data creation utilities.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import UserProfile, Wishlist, WishlistItem

User = get_user_model()


class BaseUserTestCase(TestCase):
    """Base test case with common user-related test utilities."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data that doesn't change during the test."""
        cls.user_data = {
            'email': 'testuser@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'StrongPassword123!'
        }
        
        cls.admin_data = {
            'email': 'admin@example.com',
            'username': 'admin',
            'first_name': 'Admin',
            'last_name': 'User',
            'password': 'AdminPassword123!',
            'is_staff': True,
            'is_superuser': True
        }
    
    def create_user(self, **kwargs):
        """Create a test user with default or custom data."""
        user_data = self.user_data.copy()
        user_data.update(kwargs)
        
        # Extract password before creating user
        password = user_data.pop('password')
        user = User.objects.create_user(password=password, **user_data)
        return user
    
    def create_admin_user(self, **kwargs):
        """Create an admin user for testing admin functionality."""
        admin_data = self.admin_data.copy()
        admin_data.update(kwargs)
        
        password = admin_data.pop('password')
        admin = User.objects.create_user(password=password, **admin_data)
        return admin
    
    def create_user_with_profile(self, **profile_kwargs):
        """Create user with complete profile data."""
        user = self.create_user()
        
        # Update profile with additional data
        profile_data = {
            'phone': '+1234567890',
            'date_of_birth': '1990-01-01',
            'bio': 'Test user bio',
            'address': '123 Test Street',
            'city': 'Test City',
            'country': 'Test Country',
            'postal_code': '12345',
            'newsletter_subscribed': True,
            'marketing_emails_enabled': True
        }
        profile_data.update(profile_kwargs)
        
        # Get the auto-created profile and update it
        profile = user.profile
        for key, value in profile_data.items():
            setattr(profile, key, value)
        profile.save()
        
        return user


class APITestCaseMixin:
    """Mixin for API testing with authentication helpers."""
    
    def setUp(self):
        """Set up API client and authentication helpers."""
        super().setUp()
        self.client = APIClient()
        self.auth_client = APIClient()
        self.admin_client = APIClient()
    
    def authenticate_user(self, user):
        """Authenticate user and return JWT tokens."""
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Set authentication for API client
        self.auth_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        return {
            'refresh': str(refresh),
            'access': access_token
        }
    
    def authenticate_admin(self, admin_user):
        """Authenticate admin user."""
        refresh = RefreshToken.for_user(admin_user)
        access_token = str(refresh.access_token)
        
        self.admin_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        return {
            'refresh': str(refresh),
            'access': access_token
        }


def create_test_product():
    """Create a test product for wishlist testing."""
    # This would normally import from products app
    # For now, we'll mock it or skip product-dependent tests
    # until products app is available
    pass


def create_test_product_variant():
    """Create a test product variant for wishlist testing."""
    # This would normally import from products app
    pass


# Test data constants
VALID_USER_DATA = {
    'email': 'newuser@example.com',
    'username': 'newuser',
    'first_name': 'New',
    'last_name': 'User',
    'password': 'NewPassword123!',
    'password_confirm': 'NewPassword123!'
}

INVALID_USER_DATA = {
    'email': 'invalid-email',
    'username': '',
    'first_name': '',
    'last_name': '',
    'password': '123',  # Too weak
    'password_confirm': '456'  # Doesn't match
}

VALID_PROFILE_DATA = {
    'phone': '+1987654321',
    'date_of_birth': '1985-05-15',
    'bio': 'Updated bio text',
    'address': '456 Updated Street',
    'city': 'Updated City',
    'country': 'Updated Country',
    'postal_code': '54321',
    'newsletter_subscribed': False,
    'marketing_emails_enabled': False
}

INVALID_PROFILE_DATA = {
    'phone': 'invalid-phone',  # Invalid format
    'date_of_birth': 'invalid-date',
    'bio': 'x' * 600,  # Too long (max 500)
}