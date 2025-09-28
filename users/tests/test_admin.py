"""
Tests for users app admin interface.

Tests admin registration, configurations, and functionality.
"""

from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.admin import ModelAdmin
from users.admin import UserAdmin, UserProfileAdmin, WishlistAdmin, WishlistItemAdmin
from users.models import UserProfile, Wishlist, WishlistItem
from users.tests.utils import BaseUserTestCase

User = get_user_model()


class AdminRegistrationTests(TestCase):
    """Test that admin classes are properly registered."""
    
    def test_user_admin_registered(self):
        """Test User model is registered with custom admin."""
        from django.contrib import admin
        
        # Check if User is registered
        self.assertIn(User, admin.site._registry)
        
        # Check if custom admin class is used
        admin_class = admin.site._registry[User]
        self.assertIsInstance(admin_class, UserAdmin)
    
    def test_user_profile_admin_registered(self):
        """Test UserProfile model is registered with admin."""
        from django.contrib import admin
        
        self.assertIn(UserProfile, admin.site._registry)
        admin_class = admin.site._registry[UserProfile]
        self.assertIsInstance(admin_class, UserProfileAdmin)
    
    def test_wishlist_admin_registered(self):
        """Test Wishlist model is registered with admin."""
        from django.contrib import admin
        
        self.assertIn(Wishlist, admin.site._registry)
        admin_class = admin.site._registry[Wishlist]
        self.assertIsInstance(admin_class, WishlistAdmin)
    
    def test_wishlist_item_admin_registered(self):
        """Test WishlistItem model is registered with admin."""
        from django.contrib import admin
        
        self.assertIn(WishlistItem, admin.site._registry)
        admin_class = admin.site._registry[WishlistItem]
        self.assertIsInstance(admin_class, WishlistItemAdmin)


class UserAdminTests(BaseUserTestCase):
    """Test UserAdmin configuration."""
    
    def setUp(self):
        super().setUp()
        self.site = AdminSite()
        self.admin = UserAdmin(User, self.site)
    
    def test_user_admin_list_display(self):
        """Test UserAdmin list_display configuration."""
        expected_fields = [
            'email', 'username', 'first_name', 'last_name', 
            'is_active', 'is_staff', 'date_joined'
        ]
        
        self.assertEqual(self.admin.list_display, tuple(expected_fields))
    
    def test_user_admin_list_filter(self):
        """Test UserAdmin list_filter configuration."""
        expected_filters = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
        
        self.assertEqual(self.admin.list_filter, tuple(expected_filters))
    
    def test_user_admin_search_fields(self):
        """Test UserAdmin search_fields configuration."""
        expected_search = ['email', 'username', 'first_name', 'last_name']
        
        self.assertEqual(self.admin.search_fields, tuple(expected_search))
    
    def test_user_admin_ordering(self):
        """Test UserAdmin ordering configuration."""
        expected_ordering = ('-date_joined',)
        
        self.assertEqual(self.admin.ordering, expected_ordering)
    
    def test_user_admin_fieldsets(self):
        """Test UserAdmin fieldsets configuration."""
        fieldsets = self.admin.fieldsets
        
        # Should have 4 fieldsets
        self.assertEqual(len(fieldsets), 4)
        
        # Check fieldset names and key fields
        fieldset_names = [fs[0] for fs in fieldsets]
        self.assertIn(None, fieldset_names)  # Basic info section
        self.assertIn('Personal info', fieldset_names)
        self.assertIn('Permissions', fieldset_names)
        self.assertIn('Important dates', fieldset_names)
        
        # Check that email is in basic info
        basic_fields = fieldsets[0][1]['fields']
        self.assertIn('email', basic_fields)
        self.assertIn('username', basic_fields)
        self.assertIn('password', basic_fields)
    
    def test_user_admin_add_fieldsets(self):
        """Test UserAdmin add_fieldsets configuration."""
        add_fieldsets = self.admin.add_fieldsets
        
        # Should have at least one fieldset for adding users
        self.assertGreater(len(add_fieldsets), 0)
        
        # Check that essential fields are included
        add_fields = add_fieldsets[0][1]['fields']
        required_fields = ['email', 'username', 'first_name', 'last_name', 'password1', 'password2']
        
        for field in required_fields:
            self.assertIn(field, add_fields)


class UserProfileAdminTests(BaseUserTestCase):
    """Test UserProfileAdmin configuration."""
    
    def setUp(self):
        super().setUp()
        self.site = AdminSite()
        self.admin = UserProfileAdmin(UserProfile, self.site)
    
    def test_user_profile_admin_list_display(self):
        """Test UserProfileAdmin list_display configuration."""
        expected_fields = ['user', 'phone', 'city', 'country', 'is_complete', 'created_at']
        
        self.assertEqual(self.admin.list_display, tuple(expected_fields))
    
    def test_user_profile_admin_list_filter(self):
        """Test UserProfileAdmin list_filter configuration."""
        expected_filters = ['newsletter_subscribed', 'marketing_emails_enabled', 'country', 'created_at']
        
        self.assertEqual(self.admin.list_filter, tuple(expected_filters))
    
    def test_user_profile_admin_search_fields(self):
        """Test UserProfileAdmin search_fields configuration."""
        expected_search = ['user__email', 'user__first_name', 'user__last_name', 'phone', 'city']
        
        self.assertEqual(self.admin.search_fields, tuple(expected_search))
    
    def test_user_profile_admin_readonly_fields(self):
        """Test UserProfileAdmin readonly_fields configuration."""
        expected_readonly = ['id', 'created_at', 'updated_at']
        
        self.assertEqual(self.admin.readonly_fields, tuple(expected_readonly))
    
    def test_user_profile_admin_fieldsets(self):
        """Test UserProfileAdmin fieldsets organization."""
        fieldsets = self.admin.fieldsets
        
        # Should have organized fieldsets
        self.assertGreater(len(fieldsets), 4)
        
        # Check for key sections
        fieldset_names = [fs[0] for fs in fieldsets]
        self.assertIn('User', fieldset_names)
        self.assertIn('Contact Information', fieldset_names)
        self.assertIn('Address', fieldset_names)
        self.assertIn('Profile', fieldset_names)
        self.assertIn('Preferences', fieldset_names)
        self.assertIn('Metadata', fieldset_names)


class WishlistAdminTests(BaseUserTestCase):
    """Test WishlistAdmin configuration."""
    
    def setUp(self):
        super().setUp()
        self.site = AdminSite()
        self.admin = WishlistAdmin(Wishlist, self.site)
    
    def test_wishlist_admin_list_display(self):
        """Test WishlistAdmin list_display configuration."""
        expected_fields = ['user', 'name', 'is_default', 'is_public', 'item_count', 'created_at']
        
        self.assertEqual(self.admin.list_display, tuple(expected_fields))
    
    def test_wishlist_admin_list_filter(self):
        """Test WishlistAdmin list_filter configuration."""
        expected_filters = ['is_default', 'is_public', 'created_at']
        
        self.assertEqual(self.admin.list_filter, tuple(expected_filters))
    
    def test_wishlist_admin_search_fields(self):
        """Test WishlistAdmin search_fields configuration."""
        expected_search = ['user__email', 'user__first_name', 'user__last_name', 'name']
        
        self.assertEqual(self.admin.search_fields, tuple(expected_search))
    
    def test_wishlist_admin_has_inlines(self):
        """Test WishlistAdmin includes WishlistItemInline."""
        inlines = self.admin.inlines
        
        self.assertGreater(len(inlines), 0)
        
        # Check that it's the WishlistItemInline
        from users.admin import WishlistItemInline
        self.assertIn(WishlistItemInline, inlines)


class WishlistItemAdminTests(BaseUserTestCase):
    """Test WishlistItemAdmin configuration."""
    
    def setUp(self):
        super().setUp()
        self.site = AdminSite()
        self.admin = WishlistItemAdmin(WishlistItem, self.site)
    
    def test_wishlist_item_admin_list_display(self):
        """Test WishlistItemAdmin list_display configuration."""
        expected_fields = ['wishlist', 'product', 'variant', 'added_at']
        
        self.assertEqual(self.admin.list_display, tuple(expected_fields))
    
    def test_wishlist_item_admin_list_filter(self):
        """Test WishlistItemAdmin list_filter configuration."""
        expected_filters = ['added_at', 'wishlist__user']
        
        self.assertEqual(self.admin.list_filter, tuple(expected_filters))
    
    def test_wishlist_item_admin_search_fields(self):
        """Test WishlistItemAdmin search_fields configuration."""
        expected_search = ['wishlist__name', 'product__name', 'variant__name']
        
        self.assertEqual(self.admin.search_fields, tuple(expected_search))
    
    def test_wishlist_item_admin_readonly_fields(self):
        """Test WishlistItemAdmin readonly_fields configuration."""
        expected_readonly = ['id', 'added_at']
        
        self.assertEqual(self.admin.readonly_fields, tuple(expected_readonly))


class AdminIntegrationTests(BaseUserTestCase):
    """Test admin interface integration and functionality."""
    
    def setUp(self):
        super().setUp()
        self.admin_user = self.create_admin_user()
        self.client = Client()
        self.client.force_login(self.admin_user)
    
    def test_admin_user_list_view(self):
        """Test admin user list view works correctly."""
        # Create some test users
        self.create_user()
        self.create_user(email='user2@example.com', username='user2')
        
        # Access admin user list
        url = reverse('admin:users_user_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Should contain user data
        self.assertContains(response, self.user_data['email'])
        self.assertContains(response, 'user2@example.com')
    
    def test_admin_user_detail_view(self):
        """Test admin user detail view works correctly."""
        user = self.create_user()
        
        url = reverse('admin:users_user_change', args=[user.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Should contain user data in form
        self.assertContains(response, user.email)
        self.assertContains(response, user.username)
        self.assertContains(response, user.first_name)
    
    def test_admin_user_profile_list_view(self):
        """Test admin user profile list view works correctly."""
        user = self.create_user_with_profile()
        
        url = reverse('admin:users_userprofile_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Should contain profile data
        self.assertContains(response, user.email)  # Through user relationship
        self.assertContains(response, 'Test City')  # From profile data
    
    def test_admin_wishlist_list_view(self):
        """Test admin wishlist list view works correctly."""
        user = self.create_user()
        
        url = reverse('admin:users_wishlist_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Should contain wishlist data (default wishlist created via signal)
        self.assertContains(response, user.email)
        self.assertContains(response, 'My Wishlist')
    
    def test_admin_search_functionality(self):
        """Test admin search functionality works correctly."""
        user = self.create_user()
        
        # Test user search
        url = reverse('admin:users_user_changelist')
        response = self.client.get(url, {'q': user.email})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, user.email)
        
        # Test profile search
        profile_url = reverse('admin:users_userprofile_changelist')
        response = self.client.get(profile_url, {'q': user.first_name})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, user.first_name)
    
    def test_admin_filter_functionality(self):
        """Test admin filter functionality works correctly."""
        # Create active and inactive users
        active_user = self.create_user()
        inactive_user = self.create_user(
            email='inactive@example.com',
            username='inactive',
            is_active=False
        )
        
        url = reverse('admin:users_user_changelist')
        
        # Filter by active users
        response = self.client.get(url, {'is_active__exact': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, active_user.email)
        self.assertNotContains(response, inactive_user.email)
        
        # Filter by inactive users
        response = self.client.get(url, {'is_active__exact': '0'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, inactive_user.email)
    
    def test_admin_user_add_view(self):
        """Test admin user add view works correctly."""
        url = reverse('admin:users_user_add')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Should contain add form fields
        self.assertContains(response, 'email')
        self.assertContains(response, 'username')
        self.assertContains(response, 'first_name')
        self.assertContains(response, 'last_name')
        self.assertContains(response, 'password1')
        self.assertContains(response, 'password2')
    
    def test_admin_user_creation_through_admin(self):
        """Test creating user through admin interface."""
        url = reverse('admin:users_user_add')
        
        user_data = {
            'email': 'admintest@example.com',
            'username': 'admintest',
            'first_name': 'Admin',
            'last_name': 'Test',
            'password1': 'AdminTestPassword123!',
            'password2': 'AdminTestPassword123!',
        }
        
        response = self.client.post(url, user_data, follow=True)
        
        # Should redirect to user list (successful creation)
        self.assertEqual(response.status_code, 200)
        
        # User should be created
        self.assertTrue(User.objects.filter(email='admintest@example.com').exists())
        
        # Profile should be auto-created via signals
        created_user = User.objects.get(email='admintest@example.com')
        self.assertTrue(UserProfile.objects.filter(user=created_user).exists())
        self.assertTrue(Wishlist.objects.filter(user=created_user, is_default=True).exists())


class AdminPermissionTests(BaseUserTestCase):
    """Test admin interface permission requirements."""
    
    def setUp(self):
        super().setUp()
        self.regular_user = self.create_user()
        self.admin_user = self.create_admin_user()
        self.client = Client()
    
    def test_regular_user_cannot_access_admin(self):
        """Test regular users cannot access admin interface."""
        self.client.force_login(self.regular_user)
        
        # Try to access admin index
        url = reverse('admin:index')
        response = self.client.get(url)
        
        # Should redirect to login or show permission denied
        self.assertNotEqual(response.status_code, 200)
    
    def test_admin_user_can_access_admin(self):
        """Test admin users can access admin interface."""
        self.client.force_login(self.admin_user)
        
        # Access admin index
        url = reverse('admin:index')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django administration')
    
    def test_admin_user_can_manage_users(self):
        """Test admin users can manage all user-related models."""
        self.client.force_login(self.admin_user)
        
        # Test access to all user-related admin pages
        admin_urls = [
            reverse('admin:users_user_changelist'),
            reverse('admin:users_userprofile_changelist'),
            reverse('admin:users_wishlist_changelist'),
            reverse('admin:users_wishlistitem_changelist'),
        ]
        
        for url in admin_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)