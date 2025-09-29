"""
Products app filters.

Custom filters for product and category querysets
using django-filter for advanced filtering capabilities.
"""

import django_filters
from django.db import models
from .models import Product, Category


class ProductFilter(django_filters.FilterSet):
    """
    Advanced filtering for Product model.
    
    Supports filtering by:
    - Price range (min_price, max_price)
    - Category (exact and subcategories)
    - Stock availability
    - Date ranges for created/updated
    - Active status
    """
    
    # Price range filters
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Category filters
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.filter(is_active=True)
    )
    category_slug = django_filters.CharFilter(field_name='category__slug')
    category_tree = django_filters.CharFilter(method='filter_category_tree')
    
    # Stock filters
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    low_stock = django_filters.BooleanFilter(method='filter_low_stock')
    min_stock = django_filters.NumberFilter(field_name='stock', lookup_expr='gte')
    
    # Date filters
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    # Status filters
    active = django_filters.BooleanFilter(field_name='is_active')
    
    # Search filters
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    sku = django_filters.CharFilter(field_name='sku', lookup_expr='iexact')
    
    # Price sorting
    price_sort = django_filters.OrderingFilter(
        fields=(
            ('price', 'price'),
            ('created_at', 'created_at'),
            ('name', 'name'),
            ('stock', 'stock'),
        )
    )
    
    class Meta:
        model = Product
        fields = {
            'price': ['exact', 'gte', 'lte'],
            'stock': ['exact', 'gte', 'lte'],
            'is_active': ['exact'],
            'created_at': ['exact', 'gte', 'lte'],
            'updated_at': ['exact', 'gte', 'lte'],
        }
    
    def filter_in_stock(self, queryset, name, value):
        """Filter products that are in stock (stock > 0)."""
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)
    
    def filter_low_stock(self, queryset, name, value):
        """Filter products with low stock (less than 10 items)."""
        if value:
            return queryset.filter(stock__lt=10, stock__gt=0)
        return queryset.filter(stock__gte=10)
    
    def filter_category_tree(self, queryset, name, value):
        """Filter products by category and all its subcategories."""
        try:
            category = Category.objects.get(slug=value, is_active=True)
            # Get all descendant categories
            descendant_ids = category.get_descendants().values_list('id', flat=True)
            category_ids = [category.id] + list(descendant_ids)
            return queryset.filter(category__id__in=category_ids)
        except Category.DoesNotExist:
            return queryset.none()


class CategoryFilter(django_filters.FilterSet):
    """
    Filtering for Category model.
    
    Supports filtering by:
    - Parent category
    - Active status
    - Name search
    """
    
    parent = django_filters.ModelChoiceFilter(
        queryset=Category.objects.filter(is_active=True)
    )
    parent_slug = django_filters.CharFilter(field_name='parent__slug')
    is_root = django_filters.BooleanFilter(method='filter_is_root')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    has_products = django_filters.BooleanFilter(method='filter_has_products')
    
    class Meta:
        model = Category
        fields = {
            'is_active': ['exact'],
            'created_at': ['exact', 'gte', 'lte'],
        }
    
    def filter_is_root(self, queryset, name, value):
        """Filter root categories (no parent)."""
        if value:
            return queryset.filter(parent__isnull=True)
        return queryset.filter(parent__isnull=False)
    
    def filter_has_products(self, queryset, name, value):
        """Filter categories that have products."""
        if value:
            return queryset.filter(products__isnull=False).distinct()
        return queryset.filter(products__isnull=True).distinct()


# Utility functions for complex filters
def get_category_with_children(category):
    """
    Get a category and all its descendant categories.
    Useful for filtering products in a category tree.
    """
    descendants = category.get_descendants()
    return [category] + list(descendants)


def filter_products_by_category_tree(queryset, category):
    """
    Filter products by category including all subcategories.
    """
    category_ids = [cat.id for cat in get_category_with_children(category)]
    return queryset.filter(category__id__in=category_ids)