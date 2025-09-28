"""
Tests for users app serializers.

Tests validation, security, and data transformation logic.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from users.serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    UserProfileSerializer,
    UserListSerializer
)
from users.tests.utils import BaseUserTestCase, VALID_USER_DATA, INVALID_USER_DATA, VALID_PROFILE_DATA

User = get_user_model()


class UserRegistrationSerializerTests(BaseUserTestCase):
    """Test UserRegistrationSerializer validation and user creation."""
    
    def test_valid_user_registration(self):
        """Test successful user registration with valid data."""
        serializer = UserRegistrationSerializer(data=VALID_USER_DATA)
        
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        # Check user was created correctly
        self.assertEqual(user.email, VALID_USER_DATA['email'])
        self.assertEqual(user.username, VALID_USER_DATA['username'])
        self.assertEqual(user.first_name, VALID_USER_DATA['first_name'])
        self.assertEqual(user.last_name, VALID_USER_DATA['last_name'])
        self.assertTrue(user.check_password(VALID_USER_DATA['password']))
        self.assertTrue(user.is_active)
    
    def test_email_uniqueness_validation(self):
        """Test email uniqueness validation."""
        # Create a user first
        self.create_user()
        
        # Try to register with same email
        data = VALID_USER_DATA.copy()
        data['email'] = self.user_data['email']
        data['username'] = 'differentuser'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertIn('already exists', str(serializer.errors['email']))
    
    def test_username_uniqueness_validation(self):
        """Test username uniqueness validation."""
        # Create a user first
        self.create_user()
        
        # Try to register with same username
        data = VALID_USER_DATA.copy()
        data['username'] = self.user_data['username']
        data['email'] = 'different@example.com'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('already exists', str(serializer.errors['username']))
    
    def test_password_confirmation_validation(self):
        """Test password confirmation matching."""
        data = VALID_USER_DATA.copy()
        data['password_confirm'] = 'DifferentPassword123!'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('do not match', str(serializer.errors))
    
    def test_password_strength_validation(self):
        """Test Django password validation integration."""
        data = VALID_USER_DATA.copy()
        data['password'] = '123'  # Too weak
        data['password_confirm'] = '123'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    
    def test_required_fields_validation(self):
        """Test required fields validation."""
        incomplete_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!'
            # Missing username, first_name, last_name
        }
        
        serializer = UserRegistrationSerializer(data=incomplete_data)
        self.assertFalse(serializer.is_valid())
        
        required_fields = ['username', 'first_name', 'last_name']
        for field in required_fields:
            self.assertIn(field, serializer.errors)
    
    def test_password_is_hashed(self):
        """Test password is properly hashed during user creation."""
        serializer = UserRegistrationSerializer(data=VALID_USER_DATA)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        
        # Password should be hashed, not stored as plaintext
        self.assertNotEqual(user.password, VALID_USER_DATA['password'])
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
        self.assertTrue(user.check_password(VALID_USER_DATA['password']))


class UserSerializerTests(BaseUserTestCase):
    """Test UserSerializer for user data representation."""
    
    def test_user_serialization(self):
        """Test user data serialization."""
        user = self.create_user()
        serializer = UserSerializer(user)
        
        expected_fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'is_active', 'date_joined', 'last_login'
        ]
        
        for field in expected_fields:
            self.assertIn(field, serializer.data)
        
        # Test computed field
        expected_full_name = f"{user.first_name} {user.last_name}"
        self.assertEqual(serializer.data['full_name'], expected_full_name)
    
    def test_read_only_fields(self):
        """Test that read-only fields cannot be updated."""
        user = self.create_user()
        
        # Try to update read-only fields
        update_data = {
            'id': 999,
            'username': 'newusername',
            'is_active': False,
            'email': 'newemail@example.com'  # This should be allowed
        }
        
        serializer = UserSerializer(user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.save()
        
        # Read-only fields should not change
        self.assertNotEqual(updated_user.id, 999)
        self.assertEqual(updated_user.username, user.username)  # Unchanged
        self.assertTrue(updated_user.is_active)  # Unchanged
        
        # Non-read-only field should update
        self.assertEqual(updated_user.email, 'newemail@example.com')


class UserUpdateSerializerTests(BaseUserTestCase):
    """Test UserUpdateSerializer for profile updates and password changes."""
    
    def test_email_update_validation(self):
        """Test email update with uniqueness validation."""
        user1 = self.create_user()
        user2 = self.create_user(email='user2@example.com', username='user2')
        
        # Try to update user2's email to user1's email
        serializer = UserUpdateSerializer(
            user2,
            data={'email': user1.email},
            partial=True
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertIn('already exists', str(serializer.errors['email']))
    
    def test_email_update_excludes_current_user(self):
        """Test email update allows keeping current email."""
        user = self.create_user()
        
        # Update user with same email (should be allowed)
        serializer = UserUpdateSerializer(
            user,
            data={'email': user.email, 'first_name': 'Updated'},
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertEqual(updated_user.email, user.email)
        self.assertEqual(updated_user.first_name, 'Updated')
    
    def test_password_change_requires_current_password(self):
        """Test password change requires current password."""
        user = self.create_user()
        
        # Try to change password without current password
        data = {
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'NewPassword123!'
        }
        
        serializer = UserUpdateSerializer(user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('Current password is required', str(serializer.errors))
    
    def test_password_change_validates_current_password(self):
        """Test password change validates current password."""
        user = self.create_user()
        
        # Try to change password with wrong current password
        data = {
            'current_password': 'WrongPassword123!',
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'NewPassword123!'
        }
        
        serializer = UserUpdateSerializer(user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('Current password is incorrect', str(serializer.errors))
    
    def test_successful_password_change(self):
        """Test successful password change with valid current password."""
        user = self.create_user()
        old_password = self.user_data['password']
        
        data = {
            'current_password': old_password,
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'NewPassword123!'
        }
        
        serializer = UserUpdateSerializer(user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.save()
        
        # Old password should no longer work
        self.assertFalse(updated_user.check_password(old_password))
        # New password should work
        self.assertTrue(updated_user.check_password('NewPassword123!'))
    
    def test_new_password_confirmation_validation(self):
        """Test new password confirmation matching."""
        user = self.create_user()
        
        data = {
            'current_password': self.user_data['password'],
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'DifferentPassword123!'
        }
        
        serializer = UserUpdateSerializer(user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('New passwords do not match', str(serializer.errors))
    
    def test_new_password_strength_validation(self):
        """Test new password strength validation."""
        user = self.create_user()
        
        data = {
            'current_password': self.user_data['password'],
            'new_password': '123',  # Too weak
            'new_password_confirm': '123'
        }
        
        serializer = UserUpdateSerializer(user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)


class CustomTokenObtainPairSerializerTests(BaseUserTestCase):
    """Test CustomTokenObtainPairSerializer for JWT authentication."""
    
    def test_token_generation_with_custom_claims(self):
        """Test JWT token includes custom claims."""
        user = self.create_user()
        
        # Create token manually to test claims
        serializer = CustomTokenObtainPairSerializer()
        token = serializer.get_token(user)
        
        # Check custom claims
        self.assertEqual(token['username'], user.username)
        self.assertEqual(token['email'], user.email)
        expected_full_name = f"{user.first_name} {user.last_name}".strip()
        self.assertEqual(token['full_name'], expected_full_name)
    
    def test_validate_includes_user_data(self):
        """Test validation includes user data in response."""
        user = self.create_user()
        
        # Create proper login data
        login_data = {
            'email': user.email,
            'password': self.user_data['password']
        }
        
        # Test our validate method with proper credentials
        serializer = CustomTokenObtainPairSerializer()
        result = serializer.validate(login_data)
        
        # Should include user data
        self.assertIn('user', result)
        user_data = result['user']
        
        expected_fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        for field in expected_fields:
            self.assertIn(field, user_data)


class PasswordResetSerializerTests(BaseUserTestCase):
    """Test PasswordResetSerializer validation."""
    
    def test_valid_email_validation(self):
        """Test password reset with existing email."""
        user = self.create_user()
        
        serializer = PasswordResetSerializer(data={'email': user.email})
        self.assertTrue(serializer.is_valid())
    
    def test_nonexistent_email_validation(self):
        """Test password reset with non-existent email."""
        serializer = PasswordResetSerializer(data={'email': 'nonexistent@example.com'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertIn('No user found', str(serializer.errors['email']))
    
    def test_email_required(self):
        """Test email field is required."""
        serializer = PasswordResetSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class PasswordResetConfirmSerializerTests(TestCase):
    """Test PasswordResetConfirmSerializer validation."""
    
    def test_valid_password_reset_confirm(self):
        """Test valid password reset confirmation."""
        data = {
            'new_password': 'NewStrongPassword123!',
            'new_password_confirm': 'NewStrongPassword123!'
        }
        
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_password_confirmation_mismatch(self):
        """Test password confirmation mismatch."""
        data = {
            'new_password': 'NewStrongPassword123!',
            'new_password_confirm': 'DifferentPassword123!'
        }
        
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('Passwords do not match', str(serializer.errors))
    
    def test_weak_password_validation(self):
        """Test weak password validation."""
        data = {
            'new_password': '123',
            'new_password_confirm': '123'
        }
        
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)


class UserProfileSerializerTests(BaseUserTestCase):
    """Test UserProfileSerializer for profile data."""
    
    def test_profile_serialization(self):
        """Test profile data serialization."""
        user = self.create_user_with_profile()
        profile = UserProfile.objects.get(user=user)
        
        serializer = UserProfileSerializer(profile)
        
        expected_fields = [
            'id', 'user', 'phone', 'date_of_birth', 'bio',
            'avatar', 'address', 'city', 'country', 'postal_code',
            'newsletter_subscribed', 'marketing_emails_enabled',
            'is_complete', 'full_address', 'created_at', 'updated_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, serializer.data)
    
    def test_computed_fields(self):
        """Test computed read-only fields."""
        user = self.create_user_with_profile()
        profile = UserProfile.objects.get(user=user)
        
        serializer = UserProfileSerializer(profile)
        
        # Test is_complete computed field
        self.assertIn('is_complete', serializer.data)
        self.assertTrue(serializer.data['is_complete'])
        
        # Test full_address computed field
        self.assertIn('full_address', serializer.data)
        self.assertIn('Test City', serializer.data['full_address'])
    
    def test_nested_user_serialization(self):
        """Test nested user data in profile."""
        user = self.create_user_with_profile()
        profile = UserProfile.objects.get(user=user)
        
        serializer = UserProfileSerializer(profile)
        
        # Should include nested user data
        self.assertIn('user', serializer.data)
        user_data = serializer.data['user']
        self.assertEqual(user_data['email'], user.email)
        self.assertEqual(user_data['username'], user.username)


class UserListSerializerTests(BaseUserTestCase):
    """Test UserListSerializer for admin user lists."""
    
    def test_user_list_serialization(self):
        """Test lightweight user list serialization."""
        user = self.create_user()
        serializer = UserListSerializer(user)
        
        expected_fields = [
            'id', 'username', 'email', 'full_name',
            'is_active', 'is_staff', 'date_joined'
        ]
        
        for field in expected_fields:
            self.assertIn(field, serializer.data)
        
        # Test computed full_name field
        expected_full_name = f"{user.first_name} {user.last_name}".strip()
        self.assertEqual(serializer.data['full_name'], expected_full_name)
    
    def test_admin_user_serialization(self):
        """Test admin user appears in list with correct flags."""
        admin = self.create_admin_user()
        serializer = UserListSerializer(admin)
        
        self.assertTrue(serializer.data['is_staff'])
        self.assertTrue(serializer.data['is_active'])


# Import statements that might be needed for actual implementation
from users.models import UserProfile