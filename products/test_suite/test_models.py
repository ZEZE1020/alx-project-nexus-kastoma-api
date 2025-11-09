"""
Test suite for products app models.

This module contains unit tests for all product-related models
including validation, relationships, methods, and database constraints.
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from products.models import Category, Product, ProductImage, ProductVariant, ProductReview, StockMovement

User = get_user_model()


class CategoryModelTest(TestCase):
    """Test Category model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.root_category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Electronic devices and gadgets"
        )
        
    def test_category_creation(self):
        """Test basic category creation."""
        category = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
            description="Mobile phones"
        )
        
        self.assertEqual(category.name, "Smartphones")
        self.assertEqual(category.slug, "smartphones")
        self.assertTrue(category.is_active)
        self.assertIsNone(category.parent)
        self.assertTrue(category.is_root)
        self.assertEqual(category.level, 0)
        
    def test_category_hierarchy(self):
        """Test category parent-child relationships."""
        child_category = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
            parent=self.root_category
        )
        
        self.assertEqual(child_category.parent, self.root_category)
        self.assertFalse(child_category.is_root)
        self.assertEqual(child_category.level, 1)
        
        # Test that parent has child
        self.assertIn(child_category, self.root_category.children.all())
        
    def test_category_ancestors(self):
        """Test getting category ancestors."""
        # Create hierarchy: Electronics > Smartphones > iPhones
        smartphones = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
            parent=self.root_category
        )
        
        iphones = Category.objects.create(
            name="iPhones",
            slug="iphones",
            parent=smartphones
        )
        
        ancestors = iphones.get_ancestors()
        self.assertEqual(len(ancestors), 2)
        self.assertEqual(ancestors[0], self.root_category)  # Root first
        self.assertEqual(ancestors[1], smartphones)
        
    def test_category_descendants(self):
        """Test getting category descendants."""
        # Create hierarchy
        smartphones = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
            parent=self.root_category
        )
        
        laptops = Category.objects.create(
            name="Laptops",
            slug="laptops",
            parent=self.root_category
        )
        
        iphones = Category.objects.create(
            name="iPhones",
            slug="iphones",
            parent=smartphones
        )
        
        descendants = self.root_category.get_descendants()
        self.assertEqual(len(descendants), 3)
        self.assertIn(smartphones, descendants)
        self.assertIn(laptops, descendants)
        self.assertIn(iphones, descendants)
        
    def test_category_slug_uniqueness(self):
        """Test that category slugs must be unique."""
        with self.assertRaises(IntegrityError):
            Category.objects.create(
                name="Another Electronics",
                slug="electronics",  # Duplicate slug
                description="Another electronics category"
            )
            
    def test_category_auto_slug_generation(self):
        """Test automatic slug generation from name."""
        category = Category(name="Smart Home Devices")
        category.save()
        
        self.assertEqual(category.slug, "smart-home-devices")
        
    def test_category_str_representation(self):
        """Test category string representation."""
        self.assertEqual(str(self.root_category), "Electronics")
        
    def test_category_absolute_url(self):
        """Test category absolute URL generation."""
        url = self.root_category.get_absolute_url()
        self.assertIn("electronics", url)


class ProductModelTest(TestCase):
    """Test Product model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
            description="Mobile phones"
        )
        
        self.product = Product.objects.create(
            name="iPhone 15 Pro",
            slug="iphone-15-pro",
            description="Latest iPhone with Pro features",
            price=Decimal('1199.99'),
            sku="IP15PRO001",
            category=self.category,
            stock=30,
            weight=Decimal('0.221')
        )
        
    def test_product_creation(self):
        """Test basic product creation."""
        self.assertEqual(self.product.name, "iPhone 15 Pro")
        self.assertEqual(self.product.slug, "iphone-15-pro")
        self.assertEqual(self.product.price, Decimal('1199.99'))
        self.assertEqual(self.product.sku, "IP15PRO001")
        self.assertEqual(self.product.stock, 30)
        self.assertTrue(self.product.is_active)
        self.assertEqual(self.product.category, self.category)
        
    def test_product_sku_uniqueness(self):
        """Test that product SKUs must be unique."""
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name="Another iPhone",
                slug="another-iphone",
                price=Decimal('999.99'),
                sku="IP15PRO001",  # Duplicate SKU
                category=self.category
            )
            
    def test_product_slug_uniqueness(self):
        """Test that product slugs must be unique."""
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name="Another iPhone",
                slug="iphone-15-pro",  # Duplicate slug
                price=Decimal('999.99'),
                sku="ANOTHER001",
                category=self.category
            )
            
    def test_product_price_validation(self):
        """Test product price validation."""
        product = Product(
            name="Test Product",
            slug="test-product",
            price=Decimal('-10.00'),  # Invalid negative price
            sku="TEST001",
            category=self.category
        )
        
        with self.assertRaises(ValidationError):
            product.full_clean()
            
    def test_product_weight_validation(self):
        """Test product weight validation."""
        product = Product(
            name="Test Product",
            slug="test-product",
            price=Decimal('100.00'),
            sku="TEST001",
            category=self.category,
            weight=Decimal('-1.0')  # Invalid negative weight
        )
        
        with self.assertRaises(ValidationError):
            product.full_clean()
            
    def test_product_auto_slug_generation(self):
        """Test automatic slug generation from name."""
        product = Product(
            name="Amazing Smart Phone",
            price=Decimal('299.99'),
            sku="ASP001",
            category=self.category
        )
        product.save()
        
        self.assertEqual(product.slug, "amazing-smart-phone")
        
    def test_product_is_in_stock(self):
        """Test product stock availability."""
        self.assertTrue(self.product.is_in_stock)
        
        self.product.stock = 0
        self.product.save()
        self.assertFalse(self.product.is_in_stock)
        
    def test_product_is_low_stock(self):
        """Test low stock detection."""
        self.product.stock = 3
        self.product.min_stock_level = 5
        self.product.save()
        
        self.assertTrue(self.product.is_low_stock)
        
        self.product.stock = 10
        self.product.save()
        self.assertFalse(self.product.is_low_stock)
        
    def test_product_discount_percentage(self):
        """Test discount percentage calculation."""
        self.product.compare_price = Decimal('1399.99')
        self.product.save()
        
        expected_discount = ((1399.99 - 1199.99) / 1399.99) * 100
        self.assertAlmostEqual(self.product.discount_percentage, expected_discount, places=2)
        
    def test_product_profit_margin(self):
        """Test profit margin calculation."""
        self.product.cost_price = Decimal('800.00')
        self.product.save()
        
        expected_margin = ((1199.99 - 800.00) / 1199.99) * 100
        self.assertAlmostEqual(self.product.profit_margin, expected_margin, places=2)
        
    def test_product_str_representation(self):
        """Test product string representation."""
        self.assertEqual(str(self.product), "iPhone 15 Pro")
        
    def test_product_absolute_url(self):
        """Test product absolute URL generation."""
        url = self.product.get_absolute_url()
        self.assertIn("iphone-15-pro", url)


class ProductImageModelTest(TestCase):
    """Test ProductImage model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Smartphones",
            slug="smartphones"
        )
        
        self.product = Product.objects.create(
            name="iPhone 15 Pro",
            slug="iphone-15-pro",
            price=Decimal('1199.99'),
            sku="IP15PRO001",
            category=self.category
        )
        
    def test_product_image_creation(self):
        """Test product image creation."""
        image = ProductImage.objects.create(
            product=self.product,
            image="products/iphone-15-pro.jpg",
            alt_text="iPhone 15 Pro front view",
            is_primary=True
        )
        
        self.assertEqual(image.product, self.product)
        self.assertEqual(image.alt_text, "iPhone 15 Pro front view")
        self.assertTrue(image.is_primary)
        
    def test_product_image_str_representation(self):
        """Test product image string representation."""
        image = ProductImage.objects.create(
            product=self.product,
            image="products/iphone-15-pro.jpg",
            alt_text="iPhone 15 Pro"
        )
        
        expected_str = f"{self.product.name} - iPhone 15 Pro"
        self.assertEqual(str(image), expected_str)


class ProductVariantModelTest(TestCase):
    """Test ProductVariant model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Smartphones",
            slug="smartphones"
        )
        
        self.product = Product.objects.create(
            name="iPhone 15 Pro",
            slug="iphone-15-pro",
            price=Decimal('1199.99'),
            sku="IP15PRO001",
            category=self.category
        )
        
    def test_product_variant_creation(self):
        """Test product variant creation."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name="iPhone 15 Pro - 256GB",
            sku="IP15PRO001-256",
            price=Decimal('1299.99'),
            stock=15,
            attributes={'storage': '256GB', 'color': 'Natural Titanium'}
        )
        
        self.assertEqual(variant.product, self.product)
        self.assertEqual(variant.name, "iPhone 15 Pro - 256GB")
        self.assertEqual(variant.price, Decimal('1299.99'))
        self.assertEqual(variant.attributes['storage'], '256GB')
        
    def test_variant_sku_uniqueness(self):
        """Test that variant SKUs must be unique."""
        ProductVariant.objects.create(
            product=self.product,
            name="iPhone 15 Pro - 128GB",
            sku="VARIANT001",
            price=Decimal('1199.99'),
            stock=10
        )
        
        with self.assertRaises(IntegrityError):
            ProductVariant.objects.create(
                product=self.product,
                name="iPhone 15 Pro - 256GB",
                sku="VARIANT001",  # Duplicate SKU
                price=Decimal('1299.99'),
                stock=5
            )
            
    def test_variant_price_validation(self):
        """Test variant price validation."""
        variant = ProductVariant(
            product=self.product,
            name="Test Variant",
            sku="TEST-VAR",
            price=Decimal('-10.00'),  # Invalid negative price
            stock=10
        )
        
        with self.assertRaises(ValidationError):
            variant.full_clean()
            
    def test_variant_str_representation(self):
        """Test variant string representation."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name="iPhone 15 Pro - 256GB",
            sku="IP15PRO001-256",
            price=Decimal('1299.99'),
            stock=15
        )
        
        self.assertEqual(str(variant), "iPhone 15 Pro - 256GB")


class ProductReviewModelTest(TestCase):
    """Test ProductReview model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        
        self.category = Category.objects.create(
            name="Smartphones",
            slug="smartphones"
        )
        
        self.product = Product.objects.create(
            name="iPhone 15 Pro",
            slug="iphone-15-pro",
            price=Decimal('1199.99'),
            sku="IP15PRO001",
            category=self.category
        )
        
    def test_product_review_creation(self):
        """Test product review creation."""
        review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title="Excellent product!",
            review_text="This iPhone is amazing, highly recommended!",
            is_verified_purchase=True
        )
        
        self.assertEqual(review.product, self.product)
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.title, "Excellent product!")
        self.assertTrue(review.is_verified_purchase)
        
    def test_review_rating_validation(self):
        """Test review rating validation (1-5 range)."""
        # Test rating too high
        review = ProductReview(
            product=self.product,
            user=self.user,
            rating=6,  # Invalid - above 5
            title="Test Review"
        )
        
        with self.assertRaises(ValidationError):
            review.full_clean()
            
        # Test rating too low
        review.rating = 0  # Invalid - below 1
        
        with self.assertRaises(ValidationError):
            review.full_clean()
            
    def test_review_str_representation(self):
        """Test review string representation."""
        review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title="Great product!"
        )
        
        expected_str = f"iPhone 15 Pro - 5 stars by Test User"
        self.assertEqual(str(review), expected_str)
        
    def test_unique_review_per_user_product(self):
        """Test that users can only review each product once."""
        # Create first review
        ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title="First review"
        )
        
        # Try to create duplicate review
        with self.assertRaises(IntegrityError):
            ProductReview.objects.create(
                product=self.product,
                user=self.user,
                rating=4,
                title="Second review"
            )


class StockMovementModelTest(TestCase):
    """Test StockMovement model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Smartphones",
            slug="smartphones"
        )
        
        self.product = Product.objects.create(
            name="iPhone 15 Pro",
            slug="iphone-15-pro",
            price=Decimal('1199.99'),
            sku="IP15PRO001",
            category=self.category,
            stock=30
        )
        
    def test_stock_movement_creation(self):
        """Test stock movement creation."""
        movement = StockMovement.objects.create(
            product=self.product,
            movement_type='in',
            quantity=50,
            reference="PO-2024-001",
            notes="Initial stock purchase"
        )
        
        self.assertEqual(movement.product, self.product)
        self.assertEqual(movement.movement_type, 'in')
        self.assertEqual(movement.quantity, 50)
        self.assertEqual(movement.reference, "PO-2024-001")
        
    def test_stock_movement_str_representation(self):
        """Test stock movement string representation."""
        movement = StockMovement.objects.create(
            product=self.product,
            movement_type='out',
            quantity=5,
            reference="ORDER-001"
        )
        
        expected_str = f"iPhone 15 Pro: -5 (ORDER-001)"
        self.assertEqual(str(movement), expected_str)


class ModelRelationshipTest(TestCase):
    """Test model relationships and cascading behavior."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser"
        )
        
        self.category = Category.objects.create(
            name="Electronics", 
            slug="electronics"
        )
        
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            price=Decimal('99.99'),
            sku="TEST001",
            category=self.category
        )
        
    def test_category_deletion_cascade(self):
        """Test that deleting category affects products."""
        # Create product in category
        product_id = self.product.id
        
        # Delete category (should set product.category to NULL due to SET_NULL)
        self.category.delete()
        
        # Product should still exist but category should be None
        product = Product.objects.get(id=product_id)
        self.assertIsNone(product.category)
        
    def test_product_deletion_cascade(self):
        """Test that deleting product cascades to related objects."""
        # Create related objects
        image = ProductImage.objects.create(
            product=self.product,
            image="test.jpg",
            alt_text="Test"
        )
        
        variant = ProductVariant.objects.create(
            product=self.product,
            name="Test Variant",
            sku="TEST-VAR",
            price=Decimal('109.99')
        )
        
        review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title="Great!"
        )
        
        movement = StockMovement.objects.create(
            product=self.product,
            movement_type='in',
            quantity=10
        )
        
        product_id = self.product.id
        
        # Delete product
        self.product.delete()
        
        # All related objects should be deleted due to CASCADE
        self.assertFalse(ProductImage.objects.filter(id=image.id).exists())
        self.assertFalse(ProductVariant.objects.filter(id=variant.id).exists())
        self.assertFalse(ProductReview.objects.filter(id=review.id).exists())
        self.assertFalse(StockMovement.objects.filter(id=movement.id).exists())
        
    def test_user_deletion_cascade(self):
        """Test that deleting user cascades to reviews."""
        review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title="Great!"
        )
        
        review_id = review.id
        
        # Delete user
        self.user.delete()
        
        # Review should be deleted due to CASCADE
        self.assertFalse(ProductReview.objects.filter(id=review_id).exists())