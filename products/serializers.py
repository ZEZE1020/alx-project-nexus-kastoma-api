"""
Products app serializers.

This module contains serializers for product-related models
including Product, Category, and Image serializers.
"""

from rest_framework import serializers
from decimal import Decimal
from drf_spectacular.utils import extend_schema_field
from core.serializers import BaseModelSerializer
from .models import Product, Category, ProductImage, ProductVariant, ProductReview


class CategorySerializer(BaseModelSerializer):
    """
    Serializer for Category model with nested category support.
    """
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent',
            'is_active', 'children', 'product_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'children', 'product_count']
    
    def get_children(self, obj):
        """Get child categories."""
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True, context=self.context).data
    
    def get_product_count(self, obj):
        """Get count of active products in this category."""
        return obj.products.filter(is_active=True).count()


class CategoryListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for category listings without nested children.
    """
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'product_count']
    
    def get_product_count(self, obj):
        """Get count of active products in this category."""
        return obj.products.filter(is_active=True).count()


class ProductImageSerializer(BaseModelSerializer):
    """
    Serializer for Product images.
    """
    
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'alt_text', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductVariantSerializer(BaseModelSerializer):
    """
    Serializer for Product variants.
    """
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 'name', 'sku', 'price', 'stock', 
            'attributes', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_price(self, value):
        """Ensure price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value
    
    def validate_stock(self, value):
        """Ensure stock is not negative."""
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value


class ProductReviewSerializer(BaseModelSerializer):
    """
    Serializer for Product reviews.
    """
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'product', 'user', 'user_name', 'rating', 'title', 
            'review_text', 'is_verified_purchase', 'is_approved', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'user_name', 'is_verified_purchase', 'is_approved', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        """Ensure rating is between 1 and 5."""
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class ProductSerializer(BaseModelSerializer):
    """
    Serializer for Product model with full CRUD operations.
    
    Includes validation for:
    - Price must be positive
    - SKU uniqueness
    - Stock cannot be negative
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'sku',
            'category', 'category_name', 'category_slug', 'stock', 
            'attributes', 'is_active', 'weight', 'dimensions_length', 
            'dimensions_width', 'dimensions_height',
            'images', 'variants', 'reviews', 'average_rating', 'review_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'category_name', 'category_slug', 'images', 'variants', 
            'reviews', 'average_rating', 'review_count', 'created_at', 'updated_at'
        ]
    
    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_average_rating(self, obj):
        """Calculate average rating from reviews."""
        reviews = obj.reviews.all()
        if not reviews:
            return None
        return sum(review.rating for review in reviews) / len(reviews)
    
    @extend_schema_field(serializers.IntegerField())
    def get_review_count(self, obj):
        """Get total number of reviews."""
        return obj.reviews.count()
    
    def validate_price(self, value):
        """Ensure price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value
    
    def validate_stock(self, value):
        """Ensure stock is not negative."""
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value
    
    def validate_weight(self, value):
        """Ensure weight is positive if provided."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Weight must be greater than zero.")
        return value
    
    def validate(self, attrs):
        """Object-level validation."""
        # Ensure SKU is unique
        sku = attrs.get('sku')
        if sku and self.instance and self.instance.sku != sku:
            if Product.objects.filter(sku=sku).exists():
                raise serializers.ValidationError({
                    'sku': 'Product with this SKU already exists.'
                })
        
        return super().validate(attrs)


class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer for product listings.
    Excludes heavy fields like full description and attributes.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    primary_image = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'sku',
            'category_name', 'category_slug', 'stock', 'is_active',
            'primary_image', 'average_rating', 'review_count'
        ]
    
    @extend_schema_field(serializers.DictField())
    def get_primary_image(self, obj):
        """Get the primary image for the product."""
        primary_image = next((img for img in obj.images if img.get('is_primary', False)), None)
        if primary_image:
            return primary_image
        return None
    
    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_average_rating(self, obj):
        """Calculate average rating from reviews."""
        reviews = obj.reviews.all()
        if not reviews:
            return None
        return sum(review.rating for review in reviews) / len(reviews)
    
    @extend_schema_field(serializers.IntegerField())
    def get_review_count(self, obj):
        """Get total number of reviews."""
        return obj.reviews.count()


class ProductDetailSerializer(ProductSerializer):
    """
    Extended serializer for product detail view with all related data.
    """
    related_products = serializers.SerializerMethodField()
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['related_products']
    
    def get_related_products(self, obj):
        """Get related products from the same category."""
        related = [
            product for product in Product.objects.filter(
                category=obj.category,
                is_active=True
            ).exclude(id=obj.id)[:4]
        ]
        return ProductListSerializer(related, many=True, context=self.context).data