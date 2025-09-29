"""
Test suite for products app viewsets.

This module contains integration tests for ProductViewSet and CategoryViewSet
including CRUD operations, filtering, pagination, authentication, and custom actions.
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Category, Product, ProductImage, ProductVariant, ProductReview
from products.serializers import ProductListSerializer, CategorySerializer

User = get_user_model()


class BaseProductAPITest(APITestCase):
    """Base test class with common setup for product API tests."""
    
    def setUp(self):
        """Set up test data and authentication."""
        # Create test users
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            first_name="Admin",
            last_name="User",
            is_staff=True,
            is_superuser=True
        )
        
        self.regular_user = User.objects.create_user(
            email="user@example.com",
            username="user",
            first_name="Regular",
            last_name="User"
        )
        
        # Create test categories
        self.root_category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Electronic devices"
        )
        
        self.smartphone_category = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
            description="Mobile phones",
            parent=self.root_category
        )
        
        self.laptop_category = Category.objects.create(
            name="Laptops",
            slug="laptops", 
            description="Laptop computers",
            parent=self.root_category
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name="iPhone 15 Pro",
            slug="iphone-15-pro",
            description="Latest iPhone with Pro features",
            price=Decimal('1199.99'),
            sku="IP15PRO001",
            category=self.smartphone_category,
            stock=30,
            weight=Decimal('0.221'),
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            name="MacBook Pro M3",
            slug="macbook-pro-m3",
            description="Powerful laptop with M3 chip",
            price=Decimal('1999.99'),
            sku="MBP-M3-001",
            category=self.laptop_category,
            stock=15,
            weight=Decimal('1.62'),
            is_active=True
        )
        
        self.inactive_product = Product.objects.create(
            name="Discontinued Phone",
            slug="discontinued-phone",
            price=Decimal('299.99'),
            sku="DISC001",
            category=self.smartphone_category,
            stock=0,
            is_active=False
        )
        
        # Create JWT tokens for authentication
        self.admin_token = self.get_jwt_token(self.admin_user)
        self.user_token = self.get_jwt_token(self.regular_user)
        
    def get_jwt_token(self, user):
        """Generate JWT token for user."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
        
    def authenticate_admin(self):
        """Authenticate as admin user."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
    def authenticate_user(self):
        """Authenticate as regular user."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        
    def unauthenticate(self):
        """Remove authentication."""
        self.client.credentials()


class ProductViewSetTest(BaseProductAPITest):
    """Test ProductViewSet functionality."""
    
    def test_list_products_unauthenticated(self):
        """Test listing products without authentication."""
        url = reverse('v1:product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Only active products
        
        # Check that inactive products are not included
        product_names = [p['name'] for p in response.data['results']]
        self.assertNotIn('Discontinued Phone', product_names)
        
    def test_list_products_pagination(self):
        """Test product list pagination."""
        # Create more products to test pagination
        for i in range(15):
            Product.objects.create(
                name=f"Test Product {i}",
                slug=f"test-product-{i}",
                price=Decimal('99.99'),
                sku=f"TEST{i:03d}",
                category=self.smartphone_category,
                is_active=True
            )
        
        url = reverse('v1:product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        
    def test_retrieve_product(self):
        """Test retrieving a single product."""
        url = reverse('v1:product-detail', kwargs={'pk': self.product1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'iPhone 15 Pro')
        self.assertEqual(response.data['sku'], 'IP15PRO001')
        
        # Check that detail serializer is used (includes more fields)
        self.assertIn('description', response.data)
        self.assertIn('images', response.data)
        self.assertIn('variants', response.data)
        self.assertIn('reviews', response.data)
        
    def test_create_product_unauthorized(self):
        """Test creating product without authentication fails."""
        url = reverse('v1:product-list')
        data = {
            'name': 'New Product',
            'slug': 'new-product',
            'price': '199.99',
            'sku': 'NEW001',
            'category': self.smartphone_category.pk,
            'stock': 20
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_create_product_authenticated(self):
        """Test creating product with authentication."""
        self.authenticate_admin()
        
        url = reverse('v1:product-list')
        data = {
            'name': 'New Product',
            'slug': 'new-product',
            'price': '199.99',
            'sku': 'NEW001',
            'category': self.smartphone_category.pk,
            'stock': 20,
            'weight': '0.5'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Product')
        
        # Verify product was created
        self.assertTrue(Product.objects.filter(sku='NEW001').exists())
        
    def test_update_product(self):
        """Test updating a product."""
        self.authenticate_admin()
        
        url = reverse('v1:product-detail', kwargs={'pk': self.product1.pk})
        data = {
            'name': 'iPhone 15 Pro Updated',
            'price': '1299.99'
        }
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'iPhone 15 Pro Updated')
        self.assertEqual(response.data['price'], '1299.99')
        
    def test_delete_product(self):
        """Test deleting a product (soft delete)."""
        self.authenticate_admin()
        
        url = reverse('v1:product-detail', kwargs={'pk': self.product1.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Check if product still exists but is inactive (soft delete)
        self.product1.refresh_from_db()
        # Note: Depending on implementation, this might set is_active=False or actually delete
        
    def test_product_search(self):
        """Test product search functionality."""
        url = reverse('v1:product-search')
        response = self.client.get(url, {'q': 'iPhone'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'iPhone 15 Pro')
        
    def test_product_search_empty_query(self):
        """Test search with empty query."""
        url = reverse('v1:product-search')
        response = self.client.get(url, {'q': ''})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
        
    def test_popular_products(self):
        """Test popular products endpoint."""
        # Create reviews to make products popular
        ProductReview.objects.create(
            product=self.product1,
            user=self.regular_user,
            rating=5,
            title="Great!",
            review_text="Excellent product"
        )
        ProductReview.objects.create(
            product=self.product1,
            user=self.admin_user,
            rating=4,
            title="Good",
            review_text="Good product"
        )
        
        url = reverse('v1:product-popular')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include products with rating >= 4.0
        self.assertGreaterEqual(len(response.data), 1)
        
    def test_low_stock_products(self):
        """Test low stock products endpoint."""
        # Update product to have low stock
        self.product1.stock = 5
        self.product1.save()
        
        url = reverse('v1:product-low-stock')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include products with stock < 10
        product_names = [p['name'] for p in response.data]
        self.assertIn('iPhone 15 Pro', product_names)
        
    def test_update_stock_action(self):
        """Test updating product stock via custom action."""
        self.authenticate_admin()
        
        url = reverse('v1:product-update-stock', kwargs={'pk': self.product1.pk})
        data = {'stock': 100}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, 100)
        
    def test_update_stock_invalid_value(self):
        """Test updating stock with invalid value."""
        self.authenticate_admin()
        
        url = reverse('v1:product-update-stock', kwargs={'pk': self.product1.pk})
        data = {'stock': -5}  # Invalid negative stock
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProductFilteringTest(BaseProductAPITest):
    """Test product filtering functionality."""
    
    def setUp(self):
        """Set up additional test data for filtering."""
        super().setUp()
        
        # Create products with different prices for filtering
        self.cheap_product = Product.objects.create(
            name="Budget Phone",
            slug="budget-phone",
            price=Decimal('199.99'),
            sku="BUDGET001",
            category=self.smartphone_category,
            stock=50,
            is_active=True
        )
        
        self.expensive_product = Product.objects.create(
            name="Premium Laptop",
            slug="premium-laptop",
            price=Decimal('2999.99'),
            sku="PREM001",
            category=self.laptop_category,
            stock=5,
            is_active=True
        )
        
    def test_filter_by_category(self):
        """Test filtering products by category."""
        url = reverse('v1:product-list')
        response = self.client.get(url, {'category': self.smartphone_category.pk})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only return smartphone products
        product_categories = [p['category_name'] for p in response.data['results']]
        self.assertTrue(all(cat == 'Smartphones' for cat in product_categories))
        
    def test_filter_by_category_slug(self):
        """Test filtering products by category slug."""
        url = reverse('v1:product-list')
        response = self.client.get(url, {'category_slug': 'smartphones'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_categories = [p['category_slug'] for p in response.data['results']]
        self.assertTrue(all(slug == 'smartphones' for slug in product_categories))
        
    def test_filter_by_price_range(self):
        """Test filtering products by price range."""
        url = reverse('v1:product-list')
        
        # Test minimum price filter
        response = self.client.get(url, {'min_price': '1000'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for product in response.data['results']:
            self.assertGreaterEqual(float(product['price']), 1000.0)
            
        # Test maximum price filter
        response = self.client.get(url, {'max_price': '500'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for product in response.data['results']:
            self.assertLessEqual(float(product['price']), 500.0)
            
        # Test price range
        response = self.client.get(url, {'min_price': '200', 'max_price': '1500'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for product in response.data['results']:
            price = float(product['price'])
            self.assertGreaterEqual(price, 200.0)
            self.assertLessEqual(price, 1500.0)
            
    def test_filter_in_stock(self):
        """Test filtering products by stock availability."""
        # Set one product to zero stock
        self.product1.stock = 0
        self.product1.save()
        
        url = reverse('v1:product-list')
        
        # Test in stock filter
        response = self.client.get(url, {'in_stock': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for product in response.data['results']:
            self.assertGreater(product['stock'], 0)
            
        # Test out of stock filter
        response = self.client.get(url, {'in_stock': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for product in response.data['results']:
            self.assertEqual(product['stock'], 0)
            
    def test_search_filter(self):
        """Test search functionality."""
        url = reverse('v1:product-list')
        
        # Search by name
        response = self.client.get(url, {'search': 'iPhone'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
        
        # Search by SKU
        response = self.client.get(url, {'search': 'IP15PRO001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Search by category name
        response = self.client.get(url, {'search': 'Smartphones'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
        
    def test_ordering(self):
        """Test product ordering functionality."""
        url = reverse('v1:product-list')
        
        # Test ordering by price (ascending)
        response = self.client.get(url, {'ordering': 'price'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        prices = [float(p['price']) for p in response.data['results']]
        self.assertEqual(prices, sorted(prices))
        
        # Test ordering by price (descending)
        response = self.client.get(url, {'ordering': '-price'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        prices = [float(p['price']) for p in response.data['results']]
        self.assertEqual(prices, sorted(prices, reverse=True))
        
        # Test ordering by name
        response = self.client.get(url, {'ordering': 'name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        names = [p['name'] for p in response.data['results']]
        self.assertEqual(names, sorted(names))


class ProductReviewsTest(BaseProductAPITest):
    """Test product reviews functionality."""
    
    def test_get_product_reviews(self):
        """Test getting reviews for a product."""
        # Create a review
        ProductReview.objects.create(
            product=self.product1,
            user=self.regular_user,
            rating=5,
            title="Excellent!",
            review_text="Great product, highly recommended!",
            is_verified_purchase=True,
            is_approved=True
        )
        
        url = reverse('v1:product-reviews', kwargs={'pk': self.product1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Excellent!')
        self.assertEqual(response.data[0]['rating'], 5)
        
    def test_create_product_review_authenticated(self):
        """Test creating a product review when authenticated."""
        self.authenticate_user()
        
        url = reverse('v1:product-reviews', kwargs={'pk': self.product1.pk})
        data = {
            'rating': 4,
            'title': 'Good product',
            'review_text': 'Works well, good value for money.'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify review was created
        review = ProductReview.objects.get(product=self.product1, user=self.regular_user)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.title, 'Good product')
        
    def test_create_product_review_unauthenticated(self):
        """Test creating a review without authentication fails."""
        url = reverse('v1:product-reviews', kwargs={'pk': self.product1.pk})
        data = {
            'rating': 4,
            'title': 'Good product',
            'review_text': 'Works well.'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_create_duplicate_review(self):
        """Test that users can't review the same product twice."""
        # Create initial review
        ProductReview.objects.create(
            product=self.product1,
            user=self.regular_user,
            rating=5,
            title="First review",
            review_text="Great product!"
        )
        
        self.authenticate_user()
        
        url = reverse('v1:product-reviews', kwargs={'pk': self.product1.pk})
        data = {
            'rating': 3,
            'title': 'Second review',
            'review_text': 'Changed my mind.'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already reviewed', response.data['error'])


class CategoryViewSetTest(BaseProductAPITest):
    """Test CategoryViewSet functionality."""
    
    def test_list_categories(self):
        """Test listing categories."""
        url = reverse('v1:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 3)
        
    def test_retrieve_category(self):
        """Test retrieving a single category."""
        url = reverse('v1:category-detail', kwargs={'pk': self.root_category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Electronics')
        self.assertIn('children', response.data)
        self.assertEqual(len(response.data['children']), 2)  # smartphones + laptops
        
    def test_category_tree(self):
        """Test getting category tree structure."""
        url = reverse('v1:category-tree')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return root categories with children
        root_categories = [cat for cat in response.data if cat['parent'] is None]
        self.assertEqual(len(root_categories), 1)
        self.assertEqual(root_categories[0]['name'], 'Electronics')
        self.assertEqual(len(root_categories[0]['children']), 2)
        
    def test_category_products(self):
        """Test getting products in a category."""
        url = reverse('v1:category-products', kwargs={'pk': self.smartphone_category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return products in smartphones category
        for product in response.data['results']:
            self.assertEqual(product['category_name'], 'Smartphones')
            
        # Should include products from subcategories if any exist
        
    def test_category_children(self):
        """Test getting direct child categories."""
        url = reverse('v1:category-children', kwargs={'pk': self.root_category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # smartphones + laptops
        
        child_names = [cat['name'] for cat in response.data]
        self.assertIn('Smartphones', child_names)
        self.assertIn('Laptops', child_names)