"""
Simplified tests for orders app business logic.

Tests basic model functionality and validation.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from orders.models import Order, OrderItem, Cart, CartItem, Coupon
from products.models import Product, Category

User = get_user_model()


class OrderBusinessLogicTest(TestCase):
    """Test Order model business logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=Decimal('29.99'),
            sku='TEST001',
            category=self.category,
            stock=100
        )

    def test_order_creation(self):
        """Test basic order creation."""
        order = Order.objects.create(
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
            total_amount=Decimal('29.99')
        )
        
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.order_number, 'TEST-001')
        self.assertEqual(order.status, 'pending')  # Default status
        self.assertEqual(order.total_amount, Decimal('29.99'))

    def test_order_item_creation(self):
        """Test order item creation."""
        order = Order.objects.create(
            user=self.user,
            customer_email='customer@example.com',
            order_number='TEST-002',
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
            total_amount=Decimal('59.98')
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            product_sku=self.product.sku,
            unit_price=self.product.price,
            quantity=2,
            total_price=self.product.price * 2
        )
        
        self.assertEqual(order_item.order, order)
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.total_price, Decimal('59.98'))

    def test_order_status_values(self):
        """Test order status field accepts valid values."""
        order = Order.objects.create(
            user=self.user,
            customer_email='customer@example.com',
            order_number='TEST-003',
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
            status='confirmed',
            total_amount=Decimal('29.99')
        )
        
        self.assertEqual(order.status, 'confirmed')


class CartBusinessLogicTest(TestCase):
    """Test Cart model business logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=Decimal('29.99'),
            sku='TEST001',
            category=self.category,
            stock=100
        )

    def test_cart_creation(self):
        """Test basic cart creation."""
        cart = Cart.objects.create(user=self.user)
        
        self.assertEqual(cart.user, self.user)
        self.assertIsNotNone(cart.created_at)

    def test_cart_item_creation(self):
        """Test cart item creation."""
        cart = Cart.objects.create(user=self.user)
        
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        self.assertEqual(cart_item.cart, cart)
        self.assertEqual(cart_item.product, self.product)
        self.assertEqual(cart_item.quantity, 2)


class CouponBusinessLogicTest(TestCase):
    """Test Coupon model business logic."""

    def setUp(self):
        """Set up test data."""
        pass

    def test_coupon_creation(self):
        """Test basic coupon creation."""
        coupon = Coupon.objects.create(
            code='TEST10',
            name='Test Coupon',
            description='Test discount coupon',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            is_active=True,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timezone.timedelta(days=30)
        )
        
        self.assertEqual(coupon.code, 'TEST10')
        self.assertEqual(coupon.discount_type, 'percentage')
        self.assertEqual(coupon.discount_value, Decimal('10.00'))
        self.assertTrue(coupon.is_active)

    def test_coupon_types(self):
        """Test different coupon discount types."""
        # Percentage coupon
        percentage_coupon = Coupon.objects.create(
            code='PERCENT20',
            name='20% Off',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            is_active=True,
            valid_from=timezone.now()
        )
        
        # Fixed amount coupon
        fixed_coupon = Coupon.objects.create(
            code='FIXED5',
            name='$5 Off',
            discount_type='fixed_amount',
            discount_value=Decimal('5.00'),
            is_active=True,
            valid_from=timezone.now()
        )
        
        self.assertEqual(percentage_coupon.discount_type, 'percentage')
        self.assertEqual(fixed_coupon.discount_type, 'fixed_amount')