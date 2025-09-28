"""
Tests for users app models.

Tests User, UserProfile, Wishlist, and WishlistItem models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from users.models import UserProfile, Wishlist, WishlistItem
from users.tests.utils import BaseUserTestCase

User = get_user_model()


class UserModelTests(BaseUserTestCase):
    """Test the custom User model."""
    
    def test_create_user_with_email(self):
        """Test creating a user with email as primary identifier."""
        user = self.create_user()
        
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.username, self.user_data['username'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_user_email_uniqueness(self):
        """Test that user email must be unique."""
        self.create_user()
        
        # Try to create another user with same email
        with self.assertRaises(IntegrityError):
            self.create_user(username='differentuser')
    
    def test_user_username_uniqueness(self):
        """Test that username must be unique."""
        self.create_user()
        
        # Try to create another user with same username
        with self.assertRaises(IntegrityError):
            self.create_user(email='different@example.com')
    
    def test_user_username_validation(self):
        """Test username regex validation."""
        # Valid usernames
        valid_usernames = [
            'user123',
            'user.name',
            'user_plus',
            'user+tag',
            'user-name',
            'user_name'
        ]
        
        for i, username in enumerate(valid_usernames):
            with self.subTest(username=username):
                # Use unique email for each test
                user = self.create_user(
                    username=f"{username}_{i}",
                    email=f"valid{i}@example.com"
                )
                user.full_clean()  # Trigger validation
                self.assertIn(username, user.username)  # Check contains the base username
    
    def test_user_email_as_username_field(self):
        """Test that email is used as USERNAME_FIELD."""
        self.assertEqual(User.USERNAME_FIELD, 'email')
        self.assertIn('username', User.REQUIRED_FIELDS)
        self.assertIn('first_name', User.REQUIRED_FIELDS)
        self.assertIn('last_name', User.REQUIRED_FIELDS)
    
    def test_get_full_name_method(self):
        """Test get_full_name() method returns correct format."""
        user = self.create_user()
        expected = f"{user.first_name} {user.last_name}"
        self.assertEqual(user.get_full_name(), expected)
    
    def test_get_full_name_fallback_to_username(self):
        """Test get_full_name() falls back to username when names empty."""
        user = self.create_user(first_name='', last_name='')
        self.assertEqual(user.get_full_name(), user.username)
    
    def test_get_short_name_method(self):
        """Test get_short_name() method returns first name."""
        user = self.create_user()
        self.assertEqual(user.get_short_name(), user.first_name)
    
    def test_get_short_name_fallback_to_username(self):
        """Test get_short_name() falls back to username when first_name empty."""
        user = self.create_user(first_name='')
        self.assertEqual(user.get_short_name(), user.username)
    
    def test_user_str_method(self):
        """Test User __str__ method format."""
        user = self.create_user()
        expected = f"{user.get_full_name()} ({user.email})"
        self.assertEqual(str(user), expected)
    
    def test_user_model_indexes(self):
        """Test that proper database indexes are created."""
        # This is more of a model meta test
        meta = User._meta
        index_fields = []
        for index in meta.indexes:
            index_fields.extend(index.fields)
        
        expected_indexed_fields = ['email', 'username', 'is_active', 'date_joined']
        for field in expected_indexed_fields:
            self.assertIn(field, index_fields)


class UserProfileModelTests(BaseUserTestCase):
    """Test the UserProfile model."""
    
    def test_user_profile_creation(self):
        """Test UserProfile is created automatically with User."""
        user = self.create_user()
        
        # Profile should be auto-created via signals
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, UserProfile)
        self.assertEqual(user.profile.user, user)
    
    def test_user_profile_one_to_one_relationship(self):
        """Test one-to-one relationship between User and UserProfile."""
        user = self.create_user()
        profile = user.profile
        
        # Test reverse relationship
        self.assertEqual(profile.user, user)
        
        # Test that profile has UUID primary key
        self.assertIsNotNone(profile.pk)
        self.assertNotEqual(profile.pk, user.pk)  # Different PKs
    
    def test_phone_number_validation(self):
        """Test phone number regex validation."""
        user = self.create_user()
        profile = user.profile
        
        # Valid phone numbers
        valid_phones = [
            '+1234567890',
            '1234567890',
            '+123456789012345',  # Max 15 digits
            '123456789'  # Min 9 digits
        ]
        
        for phone in valid_phones:
            with self.subTest(phone=phone):
                profile.phone = phone
                profile.full_clean()  # Should not raise ValidationError
        
        # Invalid phone numbers
        invalid_phones = [
            'abc123',  # Contains letters
            '12345',   # Too short (less than 9 digits)
            '12345678901234567',  # Too long (more than 15 digits without +)
            '+1-234-567-890',  # Contains dashes
        ]
        
        for phone in invalid_phones:
            with self.subTest(phone=phone):
                profile.phone = phone
                with self.assertRaises(ValidationError):
                    profile.full_clean()
    
    def test_profile_is_complete_property(self):
        """Test is_complete property logic."""
        user = self.create_user()
        profile = user.profile
        
        # Initially incomplete (missing required fields)
        self.assertFalse(profile.is_complete)
        
        # Fill in required fields
        profile.phone = '+1234567890'
        profile.address = '123 Main St'
        profile.city = 'Test City'
        profile.country = 'Test Country'
        profile.postal_code = '12345'
        profile.save()
        
        # Now should be complete
        self.assertTrue(profile.is_complete)
        
        # Remove one required field
        profile.phone = None
        profile.save()
        self.assertFalse(profile.is_complete)
    
    def test_get_full_address_method(self):
        """Test get_full_address() method formatting."""
        user = self.create_user()
        profile = user.profile
        
        # Test with all address fields
        profile.address = '123 Main St'
        profile.city = 'Test City'
        profile.postal_code = '12345'
        profile.country = 'Test Country'
        profile.save()
        
        expected = '123 Main St, Test City, 12345, Test Country'
        self.assertEqual(profile.get_full_address(), expected)
        
        # Test with missing fields (should skip empty ones)
        profile.postal_code = None
        profile.save()
        expected = '123 Main St, Test City, Test Country'
        self.assertEqual(profile.get_full_address(), expected)
        
        # Test with no address fields
        profile.address = None
        profile.city = None
        profile.country = None
        profile.save()
        self.assertEqual(profile.get_full_address(), '')
    
    def test_profile_str_method(self):
        """Test UserProfile __str__ method."""
        user = self.create_user()
        profile = user.profile
        
        expected = f"{user.get_full_name()}'s Profile"
        self.assertEqual(str(profile), expected)
    
    def test_profile_timestamps(self):
        """Test created_at and updated_at timestamps."""
        user = self.create_user()
        profile = user.profile
        
        # Check timestamps exist
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)
        
        # Initially, created_at and updated_at should be close
        time_diff = profile.updated_at - profile.created_at
        self.assertLess(time_diff.total_seconds(), 1)
        
        # Update profile and check updated_at changes
        original_updated_at = profile.updated_at
        profile.bio = 'Updated bio'
        profile.save()
        
        self.assertGreater(profile.updated_at, original_updated_at)


class WishlistModelTests(BaseUserTestCase):
    """Test the Wishlist model."""
    
    def test_default_wishlist_creation(self):
        """Test default wishlist is created automatically with User."""
        user = self.create_user()
        
        # Default wishlist should be auto-created via signals
        wishlists = user.wishlists.all()
        self.assertEqual(wishlists.count(), 1)
        
        default_wishlist = wishlists.first()
        self.assertTrue(default_wishlist.is_default)
        self.assertEqual(default_wishlist.name, 'My Wishlist')
        self.assertFalse(default_wishlist.is_public)
    
    def test_user_can_have_multiple_wishlists(self):
        """Test user can create multiple wishlists."""
        user = self.create_user()
        
        # Create additional wishlists
        Wishlist.objects.create(
            user=user,
            name='Holiday Wishlist',
            is_public=True
        )
        Wishlist.objects.create(
            user=user,
            name='Private Wishlist'
        )
        
        self.assertEqual(user.wishlists.count(), 3)  # Including default
    
    def test_only_one_default_wishlist_per_user(self):
        """Test only one wishlist can be default per user."""
        user = self.create_user()
        
        # Get the auto-created default wishlist
        default_wishlist = user.wishlists.get(is_default=True)
        
        # Create another wishlist and set it as default
        new_wishlist = Wishlist.objects.create(
            user=user,
            name='New Default',
            is_default=True
        )
        
        # Refresh from database
        default_wishlist.refresh_from_db()
        new_wishlist.refresh_from_db()
        
        # Original should no longer be default
        self.assertFalse(default_wishlist.is_default)
        self.assertTrue(new_wishlist.is_default)
        
        # Only one default should exist
        default_count = user.wishlists.filter(is_default=True).count()
        self.assertEqual(default_count, 1)
    
    def test_wishlist_str_method(self):
        """Test Wishlist __str__ method."""
        user = self.create_user()
        wishlist = user.wishlists.first()
        
        expected = f"{user.get_full_name()}'s {wishlist.name}"
        self.assertEqual(str(wishlist), expected)
    
    def test_wishlist_item_count_property(self):
        """Test item_count property (will be 0 without actual products)."""
        user = self.create_user()
        wishlist = user.wishlists.first()
        
        # Should start with 0 items
        self.assertEqual(wishlist.item_count, 0)
        
        # Note: We can't fully test with items until products app exists
        # This tests the property works and doesn't error
    
    def test_wishlist_ordering(self):
        """Test wishlists are ordered by creation date (newest first)."""
        user = self.create_user()
        
        # Create additional wishlists
        wishlist2 = Wishlist.objects.create(user=user, name='Second')
        wishlist3 = Wishlist.objects.create(user=user, name='Third')
        
        # Get ordered wishlists
        ordered_wishlists = list(user.wishlists.all())
        
        # Should be ordered by newest first (reverse chronological)
        self.assertEqual(ordered_wishlists[0], wishlist3)
        self.assertEqual(ordered_wishlists[1], wishlist2)
        # Default wishlist (created first) should be last
        self.assertEqual(ordered_wishlists[2].is_default, True)


class WishlistItemModelTests(BaseUserTestCase):
    """Test the WishlistItem model (limited without products app)."""
    
    def test_wishlist_item_model_structure(self):
        """Test WishlistItem model has correct structure."""
        user = self.create_user()
        wishlist = user.wishlists.first()
        
        # Test the model fields exist (can't create items without products)
        self.assertTrue(hasattr(WishlistItem, 'wishlist'))
        self.assertTrue(hasattr(WishlistItem, 'product'))
        self.assertTrue(hasattr(WishlistItem, 'variant'))
        self.assertTrue(hasattr(WishlistItem, 'added_at'))
        
        # Test unique constraint is defined
        unique_together = WishlistItem._meta.unique_together
        expected_constraint = ('wishlist', 'product', 'variant')
        self.assertIn(expected_constraint, unique_together)
    
    def test_wishlist_item_relationships(self):
        """Test WishlistItem relationships are properly configured."""
        # Test reverse relationship name
        user = self.create_user()
        wishlist = user.wishlists.first()
        
        # Should have 'items' reverse relationship
        self.assertTrue(hasattr(wishlist, 'items'))
        self.assertEqual(wishlist.items.count(), 0)
    
    def test_wishlist_item_uuid_primary_key(self):
        """Test WishlistItem uses UUID primary key."""
        # Check the field type
        pk_field = WishlistItem._meta.pk
        self.assertEqual(pk_field.get_internal_type(), 'UUIDField')
        
    def test_wishlist_item_cascade_deletion(self):
        """Test WishlistItem is deleted when wishlist is deleted."""
        user = self.create_user()
        wishlist = user.wishlists.first()
        
        # Note: Can't fully test without products, but can test relationship setup
        # Test that the foreign key has CASCADE delete
        wishlist_field = WishlistItem._meta.get_field('wishlist')
        self.assertEqual(wishlist_field.remote_field.on_delete.__name__, 'CASCADE')


# Note: Some tests are limited because they depend on the products app
# which may not be available. These tests focus on the users app models
# in isolation and test the structure and relationships that can be verified
# without external dependencies.