"""
Test suite for products app serializers.

This module contains unit tests for all product-related serializers
including validation, field handling, and data transformation tests.
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import serializers

from products.models import Category, Product, ProductImage, ProductVariant, ProductReview
from products.serializers import (
    CategorySerializer,
    CategoryListSerializer,
    ProductSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductImageSerializer,
    ProductVariantSerializer,
    ProductReviewSerializer,
)

User = get_user_model()


class CategorySerializerTest(TestCase):
    """Test CategorySerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.root_category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Electronic devices"
        )
        self.child_category = Category.objects.create(
            name="Smartphones",
            slug="smartphones", 
            description="Mobile phones",
            parent=self.root_category
        )
        
    def test_category_serialization(self):
        """Test basic category serialization."""
        serializer = CategorySerializer(self.root_category)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Electronics')
        self.assertEqual(data['slug'], 'electronics')
        self.assertEqual(data['description'], 'Electronic devices')
        self.assertIsNone(data['parent'])
        self.assertEqual(len(data['children']), 1)
        self.assertEqual(data['children'][0]['name'], 'Smartphones')
        
    def test_category_list_serializer(self):
        """Test CategoryListSerializer excludes children."""
        serializer = CategoryListSerializer(self.root_category)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Electronics')
        self.assertNotIn('children', data)
        self.assertIn('product_count', data)
        
    def test_product_count_calculation(self):
        """Test product_count field calculation."""
        # Create products
        Product.objects.create(
            name="iPhone",
            slug="iphone",
            price=Decimal('999.99'),
            sku="IP001",
            category=self.child_category,
            is_active=True
        )
        Product.objects.create(
            name="Samsung",
            slug="samsung",
            price=Decimal('799.99'),
            sku="SM001", 
            category=self.child_category,
            is_active=False  # Inactive product
        )
        
        serializer = CategorySerializer(self.child_category)
        data = serializer.data
        
        # Should only count active products
        self.assertEqual(data['product_count'], 1)


class ProductSerializerTest(TestCase):
    """Test ProductSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
            description="Mobile phones"
        )
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        self.product = Product.objects.create(
            name="iPhone 15",
            slug="iphone-15",
            description="Latest iPhone model",
            price=Decimal('999.99'),
            sku="IP15001",
            category=self.category,
            stock=50,
            weight=Decimal('0.194'),
            is_active=True
        )
        
    def test_product_serialization(self):
        """Test basic product serialization."""
        serializer = ProductSerializer(self.product)
        data = serializer.data
        
        self.assertEqual(data['name'], 'iPhone 15')
        self.assertEqual(data['slug'], 'iphone-15')
        self.assertEqual(data['price'], '999.99')
        self.assertEqual(data['sku'], 'IP15001')
        self.assertEqual(data['category_name'], 'Smartphones')
        self.assertEqual(data['stock'], 50)
        
    def test_price_validation(self):
        """Test price validation."""
        invalid_data = {
            'name': 'Test Product',
            'slug': 'test-product',
            'price': -10.00,  # Invalid negative price
            'sku': 'TEST001',
            'category': self.category.id,
            'stock': 10
        }
        
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)
        
    def test_stock_validation(self):
        """Test stock validation."""
        invalid_data = {
            'name': 'Test Product',
            'slug': 'test-product',
            'price': 100.00,
            'sku': 'TEST001',
            'category': self.category.id,
            'stock': -5  # Invalid negative stock
        }
        
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('stock', serializer.errors)
        
    def test_weight_validation(self):
        """Test weight validation."""
        invalid_data = {
            'name': 'Test Product',
            'slug': 'test-product',
            'price': 100.00,
            'sku': 'TEST001',
            'category': self.category.id,
            'stock': 10,
            'weight': -1.0  # Invalid negative weight
        }
        
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('weight', serializer.errors)
        
    def test_sku_uniqueness_validation(self):
        """Test SKU uniqueness validation on update."""
        # Create another product
        other_product = Product.objects.create(
            name="Galaxy S24",
            slug="galaxy-s24",
            price=Decimal('799.99'),
            sku="GS24001",
            category=self.category
        )
        
        # Try to update original product with existing SKU
        update_data = {
            'name': 'iPhone 15',
            'slug': 'iphone-15',
            'price': 999.99,
            'sku': 'GS24001',  # Duplicate SKU
            'category': self.category.id,
            'stock': 50
        }
        
        serializer = ProductSerializer(instance=self.product, data=update_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('sku', serializer.errors)


class ProductListSerializerTest(TestCase):
    """Test ProductListSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Smartphones",
            slug="smartphones"
        )
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        self.product = Product.objects.create(
            name="iPhone 15",
            slug="iphone-15",
            price=Decimal('999.99'),
            sku="IP15001",
            category=self.category,
            stock=50,
            is_active=True
        )
        
    def test_lightweight_serialization(self):
        """Test that list serializer excludes heavy fields."""
        serializer = ProductListSerializer(self.product)
        data = serializer.data
        
        # Should include basic fields
        self.assertIn('name', data)
        self.assertIn('price', data)
        self.assertIn('category_name', data)
        
        # Should exclude heavy fields
        self.assertNotIn('description', data)
        self.assertNotIn('attributes', data)
        self.assertNotIn('images', data)
        self.assertNotIn('variants', data)
        self.assertNotIn('reviews', data)
        
    def test_primary_image_field(self):
        """Test primary_image field returns correct image."""
        # Create product images
        ProductImage.objects.create(
            product=self.product,
            image="products/test1.jpg",
            alt_text="Test image 1",
            is_primary=False
        )
        primary_image = ProductImage.objects.create(
            product=self.product,
            image="products/primary.jpg",
            alt_text="Primary image",
            is_primary=True
        )
        
        serializer = ProductListSerializer(self.product)
        data = serializer.data
        
        self.assertIsNotNone(data['primary_image'])
        self.assertEqual(data['primary_image']['alt_text'], 'Primary image')
        
    def test_average_rating_field(self):
        """Test average_rating field calculation."""
        # Create reviews
        ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title="Great!",
            review_text="Excellent product"
        )
        ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            title="Good",
            review_text="Good product"
        )
        
        serializer = ProductListSerializer(self.product)
        data = serializer.data
        
        self.assertEqual(data['average_rating'], 4.5)
        self.assertEqual(data['review_count'], 2)


class ProductVariantSerializerTest(TestCase):
    """Test ProductVariantSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Smartphones",
            slug="smartphones"
        )
        self.product = Product.objects.create(
            name="iPhone 15",
            slug="iphone-15",
            price=Decimal('999.99'),
            sku="IP15001",
            category=self.category
        )
        
    def test_variant_serialization(self):
        """Test product variant serialization."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name="iPhone 15 - Blue",
            sku="IP15001-BL",
            price=Decimal('1099.99'),
            stock=25,
            attributes={'color': 'Blue', 'storage': '256GB'},
            is_active=True
        )
        
        serializer = ProductVariantSerializer(variant)
        data = serializer.data
        
        self.assertEqual(data['name'], 'iPhone 15 - Blue')
        self.assertEqual(data['sku'], 'IP15001-BL')
        self.assertEqual(data['price'], '1099.99')
        self.assertEqual(data['stock'], 25)
        self.assertEqual(data['attributes']['color'], 'Blue')
        
    def test_variant_validation(self):
        """Test variant price and stock validation."""
        invalid_data = {
            'product': self.product.id,
            'name': 'Test Variant',
            'sku': 'TEST-VAR',
            'price': -10.00,  # Invalid
            'stock': -5,      # Invalid
            'attributes': {}
        }
        
        serializer = ProductVariantSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)
        self.assertIn('stock', serializer.errors)


class ProductReviewSerializerTest(TestCase):
    """Test ProductReviewSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Smartphones",
            slug="smartphones"
        )
        self.product = Product.objects.create(
            name="iPhone 15",
            slug="iphone-15",
            price=Decimal('999.99'),
            sku="IP15001",
            category=self.category
        )
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            first_name="John",
            last_name="Doe"
        )
        
    def test_review_serialization(self):
        """Test product review serialization."""
        review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title="Excellent!",
            review_text="Great product, highly recommended!",
            is_verified_purchase=True
        )
        
        serializer = ProductReviewSerializer(review)
        data = serializer.data
        
        self.assertEqual(data['rating'], 5)
        self.assertEqual(data['title'], 'Excellent!')
        self.assertEqual(data['review_text'], 'Great product, highly recommended!')
        self.assertEqual(data['user_name'], 'John Doe')
        self.assertTrue(data['is_verified_purchase'])
        
    def test_rating_validation(self):
        """Test rating validation (1-5 range)."""
        invalid_data = {
            'product': self.product.id,
            'rating': 6,  # Invalid - above 5
            'title': 'Test Review',
            'review_text': 'Test content'
        }
        
        serializer = ProductReviewSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('rating', serializer.errors)
        
        invalid_data['rating'] = 0  # Invalid - below 1
        serializer = ProductReviewSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('rating', serializer.errors)


class SerializerIntegrationTest(TestCase):
    """Test serializers working together."""
    
    def setUp(self):
        """Set up complex test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        
        self.root_category = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )
        
        self.child_category = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
            parent=self.root_category
        )
        
        self.product = Product.objects.create(
            name="iPhone 15 Pro",
            slug="iphone-15-pro",
            description="Latest iPhone with Pro features",
            price=Decimal('1199.99'),
            sku="IP15PRO001",
            category=self.child_category,
            stock=30,
            weight=Decimal('0.221'),
            is_active=True
        )
        
    def test_product_detail_with_all_relations(self):
        """Test ProductDetailSerializer with all related data."""
        # Create related data
        ProductImage.objects.create(
            product=self.product,
            image="products/iphone-primary.jpg",
            alt_text="iPhone 15 Pro",
            is_primary=True
        )
        
        ProductVariant.objects.create(
            product=self.product,
            name="iPhone 15 Pro - 256GB",
            sku="IP15PRO001-256",
            price=Decimal('1299.99'),
            stock=15,
            attributes={'storage': '256GB', 'color': 'Natural Titanium'}
        )
        
        ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title="Amazing phone!",
            review_text="Best iPhone yet with excellent camera and performance."
        )
        
        # Create related product for testing
        related_product = Product.objects.create(
            name="iPhone 15",
            slug="iphone-15",
            price=Decimal('999.99'),
            sku="IP15001",
            category=self.child_category,
            is_active=True
        )
        
        serializer = ProductDetailSerializer(self.product)
        data = serializer.data
        
        # Test main product data
        self.assertEqual(data['name'], 'iPhone 15 Pro')
        self.assertEqual(data['category_name'], 'Smartphones')
        
        # Test nested relations
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['alt_text'], 'iPhone 15 Pro')
        
        self.assertEqual(len(data['variants']), 1)
        self.assertEqual(data['variants'][0]['name'], 'iPhone 15 Pro - 256GB')
        
        self.assertEqual(len(data['reviews']), 1)
        self.assertEqual(data['reviews'][0]['title'], 'Amazing phone!')
        
        # Test calculated fields
        self.assertEqual(data['average_rating'], 5.0)
        self.assertEqual(data['review_count'], 1)
        
        # Test related products
        self.assertIn('related_products', data)
        self.assertEqual(len(data['related_products']), 1)
        self.assertEqual(data['related_products'][0]['name'], 'iPhone 15')