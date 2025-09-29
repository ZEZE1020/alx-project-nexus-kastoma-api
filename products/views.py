"""
Products app views.

This module contains API views for product-related operations
including ProductViewSet and CategoryViewSet.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg
from core.views import BaseModelViewSet
from .models import Product, Category, ProductReview
from .serializers import (
    ProductSerializer, CategorySerializer, ProductListSerializer,
    ProductDetailSerializer, CategoryListSerializer, ProductReviewSerializer
)
from .filters import ProductFilter, CategoryFilter


class ProductViewSet(BaseModelViewSet):
    """
    ViewSet for Product model with full CRUD operations.
    
    Provides:
    - List products with filtering by category, price range, search
    - Retrieve individual product details
    - Create, update, delete products (admin only)
    - Custom endpoints for featured products, low stock, etc.
    """
    queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'variants', 'reviews')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'sku', 'category__name']
    ordering_fields = ['name', 'price', 'created_at', 'stock']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        Return different serializers for list vs detail views.
        """
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer
    
    def get_queryset(self):
        """Optimize queryset based on action."""
        queryset = super().get_queryset()
        
        if self.action == 'list':
            # For list view, we don't need all related data
            return queryset.select_related('category').prefetch_related('images')
        elif self.action == 'retrieve':
            # For detail view, get all related data
            return queryset.select_related('category').prefetch_related(
                'images', 'variants', 'reviews__user'
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search endpoint with text search."""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'results': []})
        
        products = self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(category__name__icontains=query)
        )
        
        # Apply pagination
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response({'results': serializer.data})
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular products based on review ratings."""
        products = self.get_queryset().annotate(
            avg_rating=Avg('reviews__rating')
        ).filter(
            avg_rating__gte=4.0
        ).order_by('-avg_rating', '-created_at')[:12]
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock (less than 10 items)."""
        products = self.get_queryset().filter(stock__lt=10, stock__gt=0)
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        """Update product stock."""
        product = self.get_object()
        new_stock = request.data.get('stock')
        
        if new_stock is not None and new_stock >= 0:
            product.stock = new_stock
            product.save()
            serializer = self.get_serializer(product)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Invalid stock value'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get', 'post'])
    def reviews(self, request, pk=None):
        """Get or create reviews for a product."""
        product = self.get_object()
        
        if request.method == 'GET':
            reviews = product.reviews.all().select_related('user')
            serializer = ProductReviewSerializer(reviews, many=True, context={'request': request})
            return Response(serializer.data)
        
        elif request.method == 'POST':
            if not request.user.is_authenticated:
                return Response(
                    {'error': 'Authentication required'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Check if user already reviewed this product
            existing_review = product.reviews.filter(user=request.user).first()
            if existing_review:
                return Response(
                    {'error': 'You have already reviewed this product'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = ProductReviewSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(user=request.user, product=product)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(BaseModelViewSet):
    """
    ViewSet for Category model.
    
    Provides:
    - List categories with hierarchical structure
    - Retrieve category details with products
    - Create, update, delete categories (admin only)
    """
    queryset = Category.objects.filter(is_active=True).prefetch_related('children')
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CategoryFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Return different serializers for different actions."""
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get category tree structure (root categories with children)."""
        root_categories = self.get_queryset().filter(parent__isnull=True)
        serializer = CategorySerializer(root_categories, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def roots(self, request):
        """Get only root categories without children data."""
        root_categories = self.get_queryset().filter(parent__isnull=True)
        serializer = CategoryListSerializer(root_categories, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get products in this category and its subcategories."""
        category = self.get_object()
        
        # Get products from this category and all subcategories
        descendant_categories = category.get_descendants()
        all_categories = [category] + list(descendant_categories)
        category_ids = [cat.id for cat in all_categories]
        
        products = Product.objects.filter(
            category__id__in=category_ids,
            is_active=True
        ).select_related('category').prefetch_related('images')
        
        # Apply filters from request
        from .filters import ProductFilter
        product_filter = ProductFilter(request.GET, queryset=products)
        filtered_products = product_filter.qs
        
        # Apply pagination
        page = self.paginate_queryset(filtered_products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(filtered_products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get direct child categories."""
        category = self.get_object()
        children = category.children.filter(is_active=True)
        serializer = CategoryListSerializer(children, many=True, context={'request': request})
        return Response(serializer.data)
