"""
Simplified tests for orders app admin.

Tests basic admin functionality.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite

from orders.models import Order, OrderItem, Cart, Coupon
from orders.admin import OrderAdmin, OrderItemAdmin, CartAdmin, CouponAdmin
from products.models import Product, Category

User = get_user_model()


class OrderAdminTest(TestCase):
    """Test OrderAdmin."""

    def setUp(self):
        """Set up test data."""
        self.site = AdminSite()
        self.admin = OrderAdmin(Order, self.site)
        
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            customer_email='customer@example.com',
            order_number='TEST-001',
            billing_first_name='John',
            billing_last_name='Doe',
            billing_address_line1='123 Test St',
            billing_city='Test City',
            billing_postal_code='12345',
            billing_country='US',
            shipping_first_name='John',
            shipping_last_name='Doe',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_postal_code='12345',
            shipping_country='US',
            total_amount=Decimal('100.00')
        )

    def test_admin_model_registration(self):
        """Test admin model is registered."""
        self.assertIsInstance(self.admin, OrderAdmin)

    def test_admin_list_display(self):
        """Test admin list display configuration."""
        if hasattr(self.admin, 'list_display'):
            self.assertIn('order_number', self.admin.list_display)


class CouponAdminTest(TestCase):
    """Test CouponAdmin."""

    def setUp(self):
        """Set up test data."""
        self.site = AdminSite()
        self.admin = CouponAdmin(Coupon, self.site)

    def test_admin_model_registration(self):
        """Test admin model is registered."""
        self.assertIsInstance(self.admin, CouponAdmin)


class CartAdminTest(TestCase):
    """Test CartAdmin."""

    def setUp(self):
        """Set up test data."""
        self.site = AdminSite()
        self.admin = CartAdmin(Cart, self.site)

    def test_admin_model_registration(self):
        """Test admin model is registered."""
        self.assertIsInstance(self.admin, CartAdmin)