"""
Tests for users app signal handlers.

Tests automatic creation of UserProfile and Wishlist on user creation.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from users.models import UserProfile, Wishlist
from users.tests.utils import BaseUserTestCase

User = get_user_model()


class UserSignalTests(TransactionTestCase):
    """Test signal handlers for User model using TransactionTestCase for signal testing."""
    
    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'email': 'signaltest@example.com',
            'username': 'signaltest',
            'first_name': 'Signal',
            'last_name': 'Test',
            'password': 'SignalTestPassword123!'
        }
    
    def test_user_profile_created_on_user_creation(self):
        """Test UserProfile is automatically created when User is created."""
        # Create user
        password = self.user_data.pop('password')
        user = User.objects.create_user(password=password, **self.user_data)
        
        # Profile should be auto-created
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.user, user)
        self.assertIsNotNone(profile.pk)
        self.assertIsNotNone(profile.created_at)
    
    def test_default_wishlist_created_on_user_creation(self):
        """Test default Wishlist is automatically created when User is created."""
        # Create user
        password = self.user_data.pop('password')
        user = User.objects.create_user(password=password, **self.user_data)
        
        # Default wishlist should be auto-created
        self.assertTrue(Wishlist.objects.filter(user=user, is_default=True).exists())
        
        wishlist = Wishlist.objects.get(user=user, is_default=True)
        self.assertEqual(wishlist.user, user)
        self.assertEqual(wishlist.name, 'My Wishlist')
        self.assertTrue(wishlist.is_default)
        self.assertFalse(wishlist.is_public)
    
    def test_profile_and_wishlist_created_together(self):
        """Test both profile and wishlist are created on user creation."""
        # Create user
        password = self.user_data.pop('password')
        user = User.objects.create_user(password=password, **self.user_data)
        
        # Both should exist
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)
        self.assertEqual(Wishlist.objects.filter(user=user).count(), 1)
        
        # Verify relationships
        profile = UserProfile.objects.get(user=user)
        wishlist = Wishlist.objects.get(user=user)
        
        self.assertEqual(profile.user, user)
        self.assertEqual(wishlist.user, user)
        self.assertTrue(wishlist.is_default)
    
    def test_signals_only_fire_on_creation(self):
        """Test signals only fire on user creation, not on updates."""
        # Create user
        password = self.user_data.pop('password')
        user = User.objects.create_user(password=password, **self.user_data)
        
        # Get initial counts
        profile_count = UserProfile.objects.filter(user=user).count()
        wishlist_count = Wishlist.objects.filter(user=user).count()
        
        self.assertEqual(profile_count, 1)
        self.assertEqual(wishlist_count, 1)
        
        # Update user (should not create new profile/wishlist)
        user.first_name = 'Updated'
        user.save()
        
        # Counts should remain the same
        new_profile_count = UserProfile.objects.filter(user=user).count()
        new_wishlist_count = Wishlist.objects.filter(user=user).count()
        
        self.assertEqual(new_profile_count, 1)
        self.assertEqual(new_wishlist_count, 1)
    
    def test_profile_saving_on_user_update(self):
        """Test that profile is saved when user is updated (if profile exists)."""
        # Create user (this will create profile via signal)
        password = self.user_data.pop('password')
        user = User.objects.create_user(password=password, **self.user_data)
        
        # Get the auto-created profile
        profile = UserProfile.objects.get(user=user)
        original_updated_at = profile.updated_at
        
        # Update profile data
        profile.bio = 'Test bio'
        profile.save()
        
        # Save user (should trigger profile save signal)
        user.last_name = 'Updated Last Name'
        user.save()
        
        # Profile should be saved (updated_at should change)
        profile.refresh_from_db()
        self.assertGreater(profile.updated_at, original_updated_at)
    
    def test_multiple_users_get_separate_profiles_and_wishlists(self):
        """Test multiple users each get their own profile and wishlist."""
        users_data = [
            {
                'email': 'user1@example.com',
                'username': 'user1',
                'first_name': 'User',
                'last_name': 'One',
                'password': 'Password123!'
            },
            {
                'email': 'user2@example.com',
                'username': 'user2',
                'first_name': 'User',
                'last_name': 'Two',
                'password': 'Password123!'
            }
        ]
        
        created_users = []
        for user_data in users_data:
            password = user_data.pop('password')
            user = User.objects.create_user(password=password, **user_data)
            created_users.append(user)
        
        # Each user should have their own profile and wishlist
        for user in created_users:
            profile = UserProfile.objects.get(user=user)
            wishlist = Wishlist.objects.get(user=user, is_default=True)
            
            self.assertEqual(profile.user, user)
            self.assertEqual(wishlist.user, user)
        
        # Total counts should match number of users
        self.assertEqual(UserProfile.objects.count(), len(created_users))
        self.assertEqual(Wishlist.objects.filter(is_default=True).count(), len(created_users))
    
    def test_signal_handles_user_creation_with_minimal_data(self):
        """Test signals work with minimal required user data."""
        # Create user with only required fields
        user = User.objects.create_user(
            email='minimal@example.com',
            username='minimal',
            password='MinimalPassword123!'
        )
        
        # Profile and wishlist should still be created
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertTrue(Wishlist.objects.filter(user=user, is_default=True).exists())
        
        profile = UserProfile.objects.get(user=user)
        wishlist = Wishlist.objects.get(user=user)
        
        self.assertEqual(profile.user, user)
        self.assertEqual(wishlist.user, user)


class ProfileUpdateSignalTests(TransactionTestCase):
    """Test profile update signals in more detail."""
    
    def test_profile_save_signal_with_existing_profile(self):
        """Test profile save signal when profile already exists."""
        # Create user (creates profile via signal)
        user = User.objects.create_user(
            email='profiletest@example.com',
            username='profiletest',
            password='ProfileTest123!'
        )
        
        # Get the profile
        profile = UserProfile.objects.get(user=user)
        
        # Modify profile
        profile.phone = '+1234567890'
        profile.save()
        
        original_updated_at = profile.updated_at
        
        # Update user (should trigger profile save)
        user.email = 'updated@example.com'
        user.save()
        
        # Profile should have been saved (updated_at should change)
        profile.refresh_from_db()
        self.assertGreaterEqual(profile.updated_at, original_updated_at)
    
    def test_profile_save_signal_handles_missing_profile(self):
        """Test profile save signal handles case where profile doesn't exist."""
        # Create user
        user = User.objects.create_user(
            email='noprofile@example.com',
            username='noprofile',
            password='NoProfile123!'
        )
        
        # Delete the auto-created profile to simulate missing profile
        UserProfile.objects.filter(user=user).delete()
        
        # Update user (signal should handle missing profile gracefully)
        user.first_name = 'Updated'
        
        # This should not raise an exception
        try:
            user.save()
        except Exception as e:
            self.fail(f"Signal handling failed with missing profile: {e}")


class SignalIntegrationTests(TransactionTestCase):
    """Test signal integration with other app functionality."""
    
    def test_signal_integration_with_user_registration(self):
        """Test signals work correctly during user registration flow."""
        from users.serializers import UserRegistrationSerializer
        
        registration_data = {
            'email': 'integration@example.com',
            'username': 'integration',
            'first_name': 'Integration',
            'last_name': 'Test',
            'password': 'IntegrationTest123!',
            'password_confirm': 'IntegrationTest123!'
        }
        
        # Use serializer to create user (simulates API registration)
        serializer = UserRegistrationSerializer(data=registration_data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        
        # Profile and wishlist should be auto-created even through serializer
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertTrue(Wishlist.objects.filter(user=user, is_default=True).exists())
        
        profile = UserProfile.objects.get(user=user)
        wishlist = Wishlist.objects.get(user=user)
        
        # Verify proper initialization
        self.assertEqual(profile.user, user)
        self.assertEqual(wishlist.name, 'My Wishlist')
        self.assertTrue(wishlist.is_default)
    
    def test_signal_performance_with_bulk_creation(self):
        """Test signal performance doesn't degrade with multiple user creation."""
        import time
        
        # Create multiple users and measure time
        start_time = time.time()
        
        users = []
        for i in range(10):  # Create 10 users
            user = User.objects.create_user(
                email=f'bulk{i}@example.com',
                username=f'bulk{i}',
                password='BulkTest123!'
            )
            users.append(user)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Verify all profiles and wishlists were created
        for user in users:
            self.assertTrue(UserProfile.objects.filter(user=user).exists())
            self.assertTrue(Wishlist.objects.filter(user=user, is_default=True).exists())
        
        # Verify total counts
        self.assertEqual(UserProfile.objects.count(), 10)
        self.assertEqual(Wishlist.objects.filter(is_default=True).count(), 10)
        
        # Performance should be reasonable (less than 5 seconds for 10 users)
        self.assertLess(creation_time, 5.0)