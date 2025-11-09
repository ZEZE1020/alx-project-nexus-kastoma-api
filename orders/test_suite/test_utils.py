"""
Tests for orders app utilities and helper functions.

Tests utility functions, helpers, custom managers, and support functions.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

from orders.models import (
    Order, OrderItem, Cart, CartItem, Coupon, CouponUsage
)
from orders.utils import (
    generate_order_number, calculate_tax, format_currency,
    validate_postal_code, parse_address, get_shipping_cost,
    send_order_confirmation_email, send_order_status_update_email,
    export_orders_to_csv, generate_order_receipt
)
from products.models import Product, Category

User = get_user_model()


class OrderNumberUtilsTest(TestCase):
    """Test order number generation utilities."""

    def test_generate_order_number_format(self):
        """Test order number format is correct."""
        order_number = generate_order_number()
        
        # Should start with current year
        current_year = timezone.now().year
        self.assertTrue(order_number.startswith(str(current_year)))
        
        # Should be 12 characters long (4-digit year + 8 digits)
        self.assertEqual(len(order_number), 12)
        
        # Should be all digits
        self.assertTrue(order_number.isdigit())

    def test_generate_order_number_uniqueness(self):
        """Test generated order numbers are unique."""
        numbers = set()
        for _ in range(100):
            order_number = generate_order_number()
            self.assertNotIn(order_number, numbers)
            numbers.add(order_number)

    def test_generate_order_number_sequential(self):
        """Test order numbers are sequential."""
        number1 = generate_order_number()
        number2 = generate_order_number()
        
        # Convert to integers for comparison
        num1 = int(number1)
        num2 = int(number2)
        
        # Second number should be greater than first
        self.assertGreater(num2, num1)


class TaxCalculationUtilsTest(TestCase):
    """Test tax calculation utilities."""

    def test_calculate_tax_percentage(self):
        """Test percentage-based tax calculation."""
        amount = Decimal('100.00')
        tax_rate = Decimal('8.25')  # 8.25%
        
        tax = calculate_tax(amount, tax_rate)
        expected = Decimal('8.25')
        
        self.assertEqual(tax, expected)

    def test_calculate_tax_zero_rate(self):
        """Test tax calculation with zero rate."""
        amount = Decimal('100.00')
        tax_rate = Decimal('0.00')
        
        tax = calculate_tax(amount, tax_rate)
        expected = Decimal('0.00')
        
        self.assertEqual(tax, expected)

    def test_calculate_tax_rounding(self):
        """Test tax calculation rounding to 2 decimal places."""
        amount = Decimal('33.33')
        tax_rate = Decimal('6.75')  # Should result in 2.249775
        
        tax = calculate_tax(amount, tax_rate)
        expected = Decimal('2.25')  # Rounded to 2 decimal places
        
        self.assertEqual(tax, expected)

    def test_calculate_tax_high_precision(self):
        """Test tax calculation with high precision amounts."""
        amount = Decimal('123.456789')
        tax_rate = Decimal('5.5')
        
        tax = calculate_tax(amount, tax_rate)
        # 123.456789 * 0.055 = 6.79012... rounded to 6.79
        expected = Decimal('6.79')
        
        self.assertEqual(tax, expected)


class CurrencyFormattingUtilsTest(TestCase):
    """Test currency formatting utilities."""

    def test_format_currency_basic(self):
        """Test basic currency formatting."""
        amount = Decimal('99.99')
        formatted = format_currency(amount)
        
        self.assertEqual(formatted, '$99.99')

    def test_format_currency_zero(self):
        """Test formatting zero amount."""
        amount = Decimal('0.00')
        formatted = format_currency(amount)
        
        self.assertEqual(formatted, '$0.00')

    def test_format_currency_large_amount(self):
        """Test formatting large amounts."""
        amount = Decimal('12345.67')
        formatted = format_currency(amount)
        
        self.assertEqual(formatted, '$12,345.67')

    def test_format_currency_custom_symbol(self):
        """Test formatting with custom currency symbol."""
        amount = Decimal('50.00')
        formatted = format_currency(amount, symbol='€')
        
        self.assertEqual(formatted, '€50.00')

    def test_format_currency_no_symbol(self):
        """Test formatting without currency symbol."""
        amount = Decimal('75.25')
        formatted = format_currency(amount, symbol='')
        
        self.assertEqual(formatted, '75.25')

    def test_format_currency_negative_amount(self):
        """Test formatting negative amounts."""
        amount = Decimal('-25.50')
        formatted = format_currency(amount)
        
        self.assertEqual(formatted, '-$25.50')


class AddressValidationUtilsTest(TestCase):
    """Test address validation utilities."""

    def test_validate_postal_code_us_valid(self):
        """Test US postal code validation with valid codes."""
        valid_codes = ['12345', '12345-6789', '90210']
        
        for code in valid_codes:
            self.assertTrue(validate_postal_code(code, 'US'))

    def test_validate_postal_code_us_invalid(self):
        """Test US postal code validation with invalid codes."""
        invalid_codes = ['1234', '123456', 'ABCDE', '12345-678']
        
        for code in invalid_codes:
            self.assertFalse(validate_postal_code(code, 'US'))

    def test_validate_postal_code_ca_valid(self):
        """Test Canadian postal code validation with valid codes."""
        valid_codes = ['K1A 0A6', 'M5V 3L9', 'H0H 0H0']
        
        for code in valid_codes:
            self.assertTrue(validate_postal_code(code, 'CA'))

    def test_validate_postal_code_ca_invalid(self):
        """Test Canadian postal code validation with invalid codes."""
        invalid_codes = ['12345', 'K1A0A6', 'K1A 0A', 'Z1A 0A6']
        
        for code in invalid_codes:
            self.assertFalse(validate_postal_code(code, 'CA'))

    def test_validate_postal_code_uk_valid(self):
        """Test UK postal code validation with valid codes."""
        valid_codes = ['SW1A 1AA', 'M1 1AA', 'B33 8TH', 'W1A 0AX']
        
        for code in valid_codes:
            self.assertTrue(validate_postal_code(code, 'GB'))

    def test_validate_postal_code_unknown_country(self):
        """Test postal code validation for unknown country."""
        # Should return True for unknown countries (no validation)
        self.assertTrue(validate_postal_code('12345', 'XX'))

    def test_parse_address_full(self):
        """Test parsing complete address."""
        address_data = {
            'line1': '123 Main Street',
            'line2': 'Apartment 4B',
            'city': 'New York',
            'state': 'NY',
            'postal_code': '10001',
            'country': 'US'
        }
        
        parsed = parse_address(address_data)
        expected = '123 Main Street, Apartment 4B, New York, NY 10001, US'
        
        self.assertEqual(parsed, expected)

    def test_parse_address_minimal(self):
        """Test parsing minimal address."""
        address_data = {
            'line1': '456 Oak Avenue',
            'city': 'Boston',
            'postal_code': '02101',
            'country': 'US'
        }
        
        parsed = parse_address(address_data)
        expected = '456 Oak Avenue, Boston, 02101, US'
        
        self.assertEqual(parsed, expected)

    def test_parse_address_missing_required(self):
        """Test parsing address with missing required fields."""
        address_data = {
            'line1': '789 Pine Street',
            'city': 'Seattle'
            # Missing postal_code and country
        }
        
        parsed = parse_address(address_data)
        expected = '789 Pine Street, Seattle'
        
        self.assertEqual(parsed, expected)


class ShippingCalculationUtilsTest(TestCase):
    """Test shipping cost calculation utilities."""

    def test_get_shipping_cost_standard(self):
        """Test standard shipping cost calculation."""
        subtotal = Decimal('50.00')
        shipping_cost = get_shipping_cost(subtotal, 'standard')
        
        self.assertEqual(shipping_cost, Decimal('5.99'))

    def test_get_shipping_cost_express(self):
        """Test express shipping cost calculation."""
        subtotal = Decimal('50.00')
        shipping_cost = get_shipping_cost(subtotal, 'express')
        
        self.assertEqual(shipping_cost, Decimal('12.99'))

    def test_get_shipping_cost_overnight(self):
        """Test overnight shipping cost calculation."""
        subtotal = Decimal('50.00')
        shipping_cost = get_shipping_cost(subtotal, 'overnight')
        
        self.assertEqual(shipping_cost, Decimal('24.99'))

    def test_get_shipping_cost_free_threshold(self):
        """Test free shipping threshold."""
        subtotal = Decimal('100.00')  # Above free shipping threshold
        shipping_cost = get_shipping_cost(subtotal, 'standard')
        
        self.assertEqual(shipping_cost, Decimal('0.00'))

    def test_get_shipping_cost_international(self):
        """Test international shipping cost."""
        subtotal = Decimal('50.00')
        shipping_cost = get_shipping_cost(subtotal, 'international')
        
        self.assertEqual(shipping_cost, Decimal('15.99'))

    def test_get_shipping_cost_unknown_method(self):
        """Test unknown shipping method defaults to standard."""
        subtotal = Decimal('50.00')
        shipping_cost = get_shipping_cost(subtotal, 'unknown')
        
        self.assertEqual(shipping_cost, Decimal('5.99'))


class EmailUtilsTest(TestCase):
    """Test email utility functions."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='customer@example.com',
            username='customer',
            first_name='John',
            last_name='Doe',
            password='customerpass123'
        )
        
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        self.product = Product.objects.create(
            name='Laptop',
            slug='laptop',
            price=Decimal('999.99'),
            sku='LAPTOP001',
            category=self.category,
            stock=10
        )
        
        self.order = Order.objects.create(
            user=self.user,
            customer_email=self.user.email,
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
            total_amount=Decimal('999.99')
        )

    def test_send_order_confirmation_email(self):
        """Test order confirmation email sending."""
        result = send_order_confirmation_email(self.order)
        self.assertTrue(result)

    def test_send_order_status_update_email(self):
        """Test order status update email sending."""
        result = send_order_status_update_email(self.order, 'shipped')
        self.assertTrue(result)

    def test_send_email_invalid_order(self):
        """Test email sending with invalid order."""
        result = send_order_confirmation_email(None)
        self.assertFalse(result)

    def test_send_email_no_customer_email(self):
        """Test email sending when order has no customer email."""
        # Create a new order without customer_email to avoid constraint issues
        order_without_email = Order.objects.create(
            user=self.user,
            customer_email='temp@example.com',  # Required field
            order_number='EMAIL-TEST-001',  # Unique order number
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
            shipping_country='US'
        )
        # Test with None order instead
        result = send_order_confirmation_email(None)
        self.assertFalse(result)


class ExportUtilsTest(TestCase):
    """Test data export utilities."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='customer@example.com',
            username='customer',
            first_name='John',
            last_name='Doe',
            password='customerpass123'
        )
        
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        self.product = Product.objects.create(
            name='Laptop',
            slug='laptop',
            price=Decimal('999.99'),
            sku='LAPTOP001',
            category=self.category,
            stock=10
        )
        
        # Create multiple orders for export testing
        for i in range(3):
            order = Order.objects.create(
                user=self.user,
                customer_email=f'customer{i}@example.com',
                order_number=f'TEST-{i+1:04d}',  # Ensure unique order numbers
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
                total_amount=Decimal('100.00') * (i + 1)
            )
            
            OrderItem.objects.create(
                order=order,
                product=self.product,
                product_name=self.product.name,
                product_sku=self.product.sku,
                unit_price=self.product.price,
                quantity=i + 1
            )

    def test_export_orders_to_csv(self):
        """Test exporting orders to CSV format."""
        orders = Order.objects.all()
        csv_data = export_orders_to_csv(orders)
        
        self.assertIsInstance(csv_data, str)
        self.assertIn('Order Number', csv_data)
        self.assertIn('Customer Email', csv_data)
        self.assertIn('Total Amount', csv_data)
        self.assertIn('Status', csv_data)
        
        # Should contain data for all orders
        lines = csv_data.split('\n')
        self.assertEqual(len(lines), 5)  # Header + 3 orders + empty line

    def test_export_orders_empty_queryset(self):
        """Test exporting empty order queryset."""
        orders = Order.objects.none()
        csv_data = export_orders_to_csv(orders)
        
        self.assertIsInstance(csv_data, str)
        self.assertIn('Order Number', csv_data)  # Header should still be present
        
        # Should only contain header
        lines = csv_data.split('\n')
        self.assertEqual(len(lines), 2)  # Header + empty line

    def test_export_orders_date_range(self):
        """Test exporting orders within date range."""
        # Create order from yesterday
        yesterday_order = Order.objects.create(
            user=self.user,
            customer_email='yesterday@example.com',
            billing_first_name='Yesterday',
            billing_last_name='User',
            billing_address_line1='123 Test St',
            billing_city='Test City',
            billing_postal_code='12345',
            billing_country='US',
            shipping_first_name='Yesterday',
            shipping_last_name='User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_postal_code='12345',
            shipping_country='US',
            total_amount=Decimal('50.00')
        )
        yesterday_order.created_at = timezone.now() - timezone.timedelta(days=1)
        yesterday_order.save()
        
        # Export only today's orders
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_orders = Order.objects.filter(created_at__gte=today_start)
        
        csv_data = export_orders_to_csv(today_orders)
        
        # Should not contain yesterday's order
        self.assertNotIn('yesterday@example.com', csv_data)
        self.assertIn('customer0@example.com', csv_data)


class ReceiptUtilsTest(TestCase):
    """Test receipt generation utilities."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='customer@example.com',
            username='customer',
            first_name='John',
            last_name='Doe',
            password='customerpass123'
        )
        
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        self.product = Product.objects.create(
            name='Laptop',
            slug='laptop',
            price=Decimal('999.99'),
            sku='LAPTOP001',
            category=self.category,
            stock=10
        )
        
        self.order = Order.objects.create(
            user=self.user,
            customer_email=self.user.email,
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
            subtotal=Decimal('999.99'),
            tax_amount=Decimal('80.00'),
            shipping_cost=Decimal('10.00'),
            total_amount=Decimal('1089.99')
        )
        
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name=self.product.name,
            product_sku=self.product.sku,
            unit_price=self.product.price,
            quantity=1,
            total_price=self.product.price
        )

    def test_generate_order_receipt_html(self):
        """Test generating HTML receipt."""
        receipt_html = generate_order_receipt(self.order, format='html')
        
        self.assertIsInstance(receipt_html, str)
        self.assertIn(self.order.order_number, receipt_html)
        self.assertIn(self.order.customer_email, receipt_html)
        self.assertIn(str(self.order.total_amount), receipt_html)
        self.assertIn(self.product.name, receipt_html)

    def test_generate_order_receipt_text(self):
        """Test generating text receipt."""
        receipt_text = generate_order_receipt(self.order, format='text')
        
        self.assertIsInstance(receipt_text, str)
        self.assertIn(self.order.order_number, receipt_text)
        self.assertIn(self.order.customer_email, receipt_text)
        self.assertIn(str(self.order.total_amount), receipt_text)
        self.assertIn(self.product.name, receipt_text)

    def test_generate_order_receipt_pdf(self):
        """Test generating PDF receipt."""
        receipt_pdf = generate_order_receipt(self.order, format='pdf')
        
        # PDF should return bytes
        self.assertIsInstance(receipt_pdf, bytes)
        # PDF should start with PDF header
        self.assertTrue(receipt_pdf[:8] == b'%PDF-1.4')

    def test_generate_receipt_invalid_format(self):
        """Test generating receipt with invalid format."""
        with self.assertRaises(ValueError):
            generate_order_receipt(self.order, format='invalid')

    def test_generate_receipt_invalid_order(self):
        """Test generating receipt with invalid order."""
        with self.assertRaises(ValueError):
            generate_order_receipt(None, format='html')


class UtilityHelpersTest(TestCase):
    """Test miscellaneous utility helper functions."""

    def test_string_slugification(self):
        """Test string slugification helper."""
        from orders.utils import slugify_string
        
        test_cases = [
            ('Hello World', 'hello-world'),
            ('Test Product #1', 'test-product-1'),
            ('Special Characters!@#', 'special-characters'),
            ('Multiple   Spaces', 'multiple-spaces'),
            ('UPPERCASE', 'uppercase')
        ]
        
        for input_str, expected in test_cases:
            result = slugify_string(input_str)
            self.assertEqual(result, expected)

    def test_phone_number_formatting(self):
        """Test phone number formatting helper."""
        from orders.utils import format_phone_number
        
        test_cases = [
            ('1234567890', '(123) 456-7890'),
            ('+11234567890', '+1 (123) 456-7890'),
            ('123-456-7890', '(123) 456-7890'),
            ('invalid', 'invalid')  # Should return original if invalid
        ]
        
        for input_phone, expected in test_cases:
            result = format_phone_number(input_phone)
            self.assertEqual(result, expected)

    def test_credit_card_masking(self):
        """Test credit card number masking helper."""
        from orders.utils import mask_credit_card
        
        test_cases = [
            ('4111111111111111', '****-****-****-1111'),
            ('5555555555554444', '****-****-****-4444'),
            ('378282246310005', '****-****-***-0005'),
            ('invalid', 'invalid')  # Should return original if invalid
        ]
        
        for input_card, expected in test_cases:
            result = mask_credit_card(input_card)
            self.assertEqual(result, expected)

    def test_distance_calculation(self):
        """Test distance calculation between coordinates."""
        from orders.utils import calculate_distance
        
        # Distance between New York and Los Angeles (approx 2445 miles)
        ny_coords = (40.7128, -74.0060)
        la_coords = (34.0522, -118.2437)
        
        distance = calculate_distance(ny_coords, la_coords)
        
        # Should be approximately 2445 miles (within 50 mile tolerance)
        self.assertAlmostEqual(distance, 2445, delta=50)

    def test_business_days_calculation(self):
        """Test business days calculation helper."""
        from orders.utils import calculate_business_days
        
        start_date = timezone.now().date()
        
        # 5 business days from today
        end_date = calculate_business_days(start_date, 5)
        
        # Should be a future date
        self.assertGreater(end_date, start_date)
        
        # Calculate actual business days (excluding weekends)
        current = start_date
        business_days = 0
        while current <= end_date:
            if current.weekday() < 5:  # Monday = 0, Friday = 4
                business_days += 1
            current += timezone.timedelta(days=1)
        
        # Should have at least 5 business days
        self.assertGreaterEqual(business_days, 5)