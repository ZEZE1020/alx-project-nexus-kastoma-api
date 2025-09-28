"""
Tests for users app views and API endpoints.

Tests authentication, permissions, and API functionality.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import UserProfile
from users.tests.utils import BaseUserTestCase, APITestCaseMixin, VALID_USER_DATA, VALID_PROFILE_DATA

User = get_user_model()


class UserRegistrationViewTests(APITestCase, BaseUserTestCase):
    """Test user registration API endpoint."""
    
    def setUp(self):
        super().setUp()
        self.registration_url = reverse('api:v1:users:user-register')
    
    def test_successful_user_registration(self):
        """Test successful user registration."""
        response = self.client.post(self.registration_url, VALID_USER_DATA)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        
        # Check user was created
        user = User.objects.get(email=VALID_USER_DATA['email'])
        self.assertEqual(user.username, VALID_USER_DATA['username'])
        self.assertTrue(user.check_password(VALID_USER_DATA['password']))
        
        # Check profile was auto-created
        self.assertTrue(hasattr(user, 'profile'))
        
        # Check default wishlist was created
        self.assertEqual(user.wishlists.count(), 1)
        self.assertTrue(user.wishlists.first().is_default)
    
    def test_registration_with_duplicate_email(self):
        """This tests registration fails with duplicate email."""
        # Create user first
        self.create_user()
        
        # Try to register with same email
        data = VALID_USER_DATA.copy()
        data['email'] = self.user_data['email']
        data['username'] = 'differentuser'
        
        response = self.client.post(self.registration_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_registration_with_invalid_data(self):
        """Test registration fails with invalid data."""
        invalid_data = {
            'email': 'invalid-email',
            'username': '',
            'password': '123',
            'password_confirm': '456'
        }
        
        response = self.client.post(self.registration_url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('username', response.data)
        self.assertIn('password', response.data)
    
    def test_registration_allows_anonymous_access(self):
        """Test registration endpoint allows anonymous access."""
        # Should not require authentication
        response = self.client.post(self.registration_url, VALID_USER_DATA)
        
        # Should not return 401 Unauthorized
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CustomTokenObtainPairViewTests(APITestCase, BaseUserTestCase):
    """Tests JWT authentication endpoints."""
    
    def setUp(self):
        super().setUp()
        self.login_url = reverse('api:v1:users:token-obtain-pair')
        self.refresh_url = reverse('api:v1:users:token-refresh')
        self.verify_url = reverse('api:v1:users:token-verify')
        self.user = self.create_user()
    
    def test_successful_login_with_email(self):
        """Tests successful login with email and password."""
        login_data = {
            'email': self.user.email,
            'password': self.user_data['password']
        }
        
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        
        # Check user data in response
        user_data = response.data['user']
        self.assertEqual(user_data['email'], self.user.email)
        self.assertEqual(user_data['username'], self.user.username)
        self.assertIn('full_name', user_data)
    
    def test_login_with_invalid_credentials(self):
        """Test login fails with invalid credentials."""
        login_data = {
            'email': self.user.email,
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh(self):
        """Test JWT token refresh functionality."""
        # Get initial tokens
        refresh = RefreshToken.for_user(self.user)
        
        refresh_data = {'refresh': str(refresh)}
        response = self.client.post(self.refresh_url, refresh_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_token_verification(self):
        """Test JWT token verification."""
        # Get access token
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        verify_data = {'token': access_token}
        response = self.client.post(self.verify_url, verify_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserViewSetTests(APITestCaseMixin, APITestCase, BaseUserTestCase):
    """Test UserViewSet API endpoints."""
    
    def setUp(self):
        super().setUp()
        self.user = self.create_user()
        self.admin = self.create_admin_user()
        self.tokens = self.authenticate_user(self.user)
        self.admin_tokens = self.authenticate_admin(self.admin)
    
    def test_user_list_requires_admin(self):
        """Test user list endpoint requires admin permissions."""
        url = reverse('api:v1:users:user-list')
        
        # Regular user should not access list
        response = self.auth_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin should access list
        response = self.admin_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_me_endpoint(self):
        """Test /users/me/ endpoint returns current user."""
        url = reverse('api:v1:users:user-profile')
        
        response = self.auth_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['username'], self.user.username)
    
    def test_user_profile_update(self):
        """Test user profile update endpoint."""
        url = reverse('api:v1:users:user-profile-update')
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        
        response = self.auth_client.put(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh user from database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'updated@example.com')
    
    def test_user_profile_partial_update(self):
        """Test user profile partial update (PATCH)."""
        url = reverse('api:v1:users:user-profile-update')
        
        update_data = {'first_name': 'PartialUpdate'}
        
        response = self.auth_client.patch(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh user from database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'PartialUpdate')
        # Other fields should remain unchanged
        self.assertEqual(self.user.last_name, self.user_data['last_name'])
    
    def test_change_password_endpoint(self):
        """Test password change endpoint."""
        url = reverse('api:v1:users:user-change-password')
        
        password_data = {
            'current_password': self.user_data['password'],
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'NewPassword123!'
        }
        
        response = self.auth_client.post(url, password_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123!'))
        self.assertFalse(self.user.check_password(self.user_data['password']))
    
    def test_change_password_requires_current_password(self):
        """Test password change requires correct current password."""
        url = reverse('api:v1:users:user-change-password')
        
        password_data = {
            'current_password': 'wrongpassword',
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'NewPassword123!'
        }
        
        response = self.auth_client.post(url, password_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_delete_account_endpoint(self):
        """Test account deactivation endpoint."""
        url = reverse('api:v1:users:user-delete-account')
        
        response = self.auth_client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # User should be deactivated, not deleted
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
    
    def test_user_detail_with_me_parameter(self):
        """Test accessing user detail with 'me' as pk."""
        url = reverse('api:v1:users:user-detail', kwargs={'pk': 'me'})
        
        response = self.auth_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
    
    def test_unauthorized_access_protection(self):
        """Test endpoints require authentication."""
        urls = [
            reverse('api:v1:users:user-profile'),
            reverse('api:v1:users:user-profile-update'),
            reverse('api:v1:users:user-change-password'),
            reverse('api:v1:users:user-delete-account'),
        ]
        
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileViewSetTests(APITestCaseMixin, APITestCase, BaseUserTestCase):
    """Test UserProfileViewSet API endpoints."""
    
    def setUp(self):
        super().setUp()
        self.user = self.create_user_with_profile()
        self.tokens = self.authenticate_user(self.user)
        self.profile_me_url = '/api/v1/profiles/me/'  # Based on custom action
    
    def test_get_user_profile(self):
        """Test retrieving user's profile."""
        response = self.auth_client.get(self.profile_me_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check profile data
        expected_fields = [
            'id', 'user', 'phone', 'address', 'city', 'country',
            'is_complete', 'full_address'
        ]
        
        for field in expected_fields:
            self.assertIn(field, response.data)
    
    def test_update_user_profile(self):
        """Test updating user's profile."""
        update_url = '/api/v1/profiles/update_me/'
        
        update_data = {
            'phone': '+9876543210',
            'bio': 'Updated bio',
            'city': 'New City',
            'newsletter_subscribed': False
        }
        
        response = self.auth_client.put(update_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify updates in database
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.phone, '+9876543210')
        self.assertEqual(profile.bio, 'Updated bio')
        self.assertEqual(profile.city, 'New City')
        self.assertFalse(profile.newsletter_subscribed)
    
    def test_profile_partial_update(self):
        """Test partial profile update (PATCH)."""
        update_url = '/api/v1/profiles/update_me/'
        
        update_data = {'bio': 'Partially updated bio'}
        
        response = self.auth_client.patch(update_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify partial update
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.bio, 'Partially updated bio')
        # Other fields should remain unchanged
        self.assertEqual(profile.phone, '+1234567890')  # From test setup
    
    def test_profile_access_requires_authentication(self):
        """Test profile endpoints require authentication."""
        response = self.client.get(self.profile_me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetViewTests(APITestCase, BaseUserTestCase):
    """Test password reset API endpoints."""
    
    def setUp(self):
        super().setUp()
        self.reset_url = reverse('api:v1:users:password-reset')
        self.user = self.create_user()
    
    def test_password_reset_request_with_valid_email(self):
        """Test password reset request with existing email."""
        reset_data = {'email': self.user.email}
        
        response = self.client.post(self.reset_url, reset_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_password_reset_request_with_invalid_email(self):
        """Test password reset request with non-existent email."""
        reset_data = {'email': 'nonexistent@example.com'}
        
        response = self.client.post(self.reset_url, reset_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_password_reset_allows_anonymous_access(self):
        """Test password reset endpoint allows anonymous access."""
        reset_data = {'email': self.user.email}
        
        response = self.client.post(self.reset_url, reset_data)
        
        # Should not require authentication
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetConfirmViewTests(APITestCase):
    """Test password reset confirmation endpoint."""
    
    def setUp(self):
        super().setUp()
        # Mock token for testing
        self.confirm_url = reverse('api:v1:users:password-reset-confirm', kwargs={'token': 'mock-token'})
    
    def test_password_reset_confirm_structure(self):
        """Test password reset confirm endpoint structure."""
        confirm_data = {
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'NewPassword123!'
        }
        
        response = self.client.post(self.confirm_url, confirm_data)
        
        # Since token validation is not implemented, this will succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_password_reset_confirm_validation(self):
        """Test password reset confirm validation."""
        confirm_data = {
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'DifferentPassword123!'
        }
        
        response = self.client.post(self.confirm_url, confirm_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_password_reset_confirm_allows_anonymous_access(self):
        """Test password reset confirm allows anonymous access."""
        confirm_data = {
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'NewPassword123!'
        }
        
        response = self.client.post(self.confirm_url, confirm_data)
        
        # Should not require authentication
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PermissionTests(APITestCaseMixin, APITestCase, BaseUserTestCase):
    """Test API permission ."""
    
    def setUp(self):
        super().setUp()
        self.user1 = self.create_user()
        self.user2 = self.create_user(email='user2@example.com', username='user2')
        self.admin = self.create_admin_user()
        
        self.user1_tokens = self.authenticate_user(self.user1)
        # Create separate client for user2
        from rest_framework.test import APIClient
        self.user2_client = APIClient()
        user2_refresh = RefreshToken.for_user(self.user2)
        user2_access = str(user2_refresh.access_token)
        self.user2_client.credentials(HTTP_AUTHORIZATION=f'Bearer {user2_access}')
        
        self.admin_tokens = self.authenticate_admin(self.admin)
    
    def test_users_cannot_access_other_profiles(self):
        """Test users cannot access other users' profiles."""
        # Try to access user2's profile with user1's token
        user2_detail_url = reverse('api:v1:users:user-detail', kwargs={'pk': self.user2.pk})
        
        response = self.auth_client.get(user2_detail_url)
        
        # Should be forbidden or not found (depending on implementation)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
    
    def test_admin_can_access_all_users(self):
        """Test admin can access all user profiles."""
        user_list_url = reverse('api:v1:users:user-list')
        
        response = self.admin_client.get(user_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return multiple users
        self.assertGreaterEqual(len(response.data['results'] if 'results' in response.data else response.data), 2)
    
    def test_regular_users_cannot_list_all_users(self):
        """Test regular users cannot list all users."""
        user_list_url = reverse('api:v1:users:user-list')
        
        response = self.auth_client.get(user_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_profile_isolation(self):
        """Test users can only see their own profile data."""
        profile_url = reverse('api:v1:users:user-profile')
        
        # User1 should see their own profile
        response = self.auth_client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user1.email)
        
        # User2 should see their own profile
        response = self.user2_client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user2.email)


class APIEndpointIntegrationTests(APITestCaseMixin, APITestCase, BaseUserTestCase):
    """Test complete API workflows and integration."""
    
    def test_complete_user_registration_and_login_flow(self):
        """Test complete user registration and login workflow."""
        # Step 1: Register user
        registration_url = reverse('api:v1:users:user-register')
        response = self.client.post(registration_url, VALID_USER_DATA)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 2: Login with registered credentials
        login_url = reverse('api:v1:users:token-obtain-pair')
        login_data = {
            'email': VALID_USER_DATA['email'],
            'password': VALID_USER_DATA['password']
        }
        
        response = self.client.post(login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Step 3: Access protected endpoint with token
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        profile_url = reverse('api:v1:users:user-profile')
        response = self.client.get(profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], VALID_USER_DATA['email'])
    
    def test_complete_profile_management_flow(self):
        """Test complete profile management workflow."""
        # Setup user and authentication
        user = self.create_user()
        self.authenticate_user(user)
        
        # Step 1: Get initial profile
        profile_url = reverse('api:v1:users:user-profile')
        response = self.auth_client.get(profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        initial_data = response.data
        
        # Step 2: Update profile
        update_url = reverse('api:v1:users:user-profile-update')
        update_data = {
            'first_name': 'Updated',
            'last_name': 'User',
            'email': 'updated@example.com'
        }
        
        response = self.auth_client.put(update_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 3: Verify changes
        response = self.auth_client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['email'], 'updated@example.com')
        
        # Step 4: Change password
        password_url = reverse('api:v1:users:user-change-password')
        password_data = {
            'current_password': self.user_data['password'],
            'new_password': 'NewSecurePassword123!',
            'new_password_confirm': 'NewSecurePassword123!'
        }
        
        response = self.auth_client.post(password_url, password_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 5: Verify new password works
        login_url = reverse('api:v1:users:token-obtain-pair')
        login_data = {
            'email': 'updated@example.com',
            'password': 'NewSecurePassword123!'
        }
        
        response = self.client.post(login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)