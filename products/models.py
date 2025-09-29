"""
Products app models.

Django models for product catalog including categories, products,
variants, images, and inventory tracking.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse

User = get_user_model()


class TimeStampedModel(models.Model):
    """
    Abstract base model with created_at and updated_at timestamps.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Category(TimeStampedModel):
    """
    Product category model with hierarchical structure.
    
    Supports nested categories with parent-child relationships.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
            models.Index(fields=['is_active']),
            models.Index(fields=['sort_order']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return the URL for this category."""
        return reverse('products:category-detail', kwargs={'slug': self.slug})
    
    @property
    def is_root(self):
        """Check if this is a root category (no parent)."""
        return self.parent is None
    
    @property
    def level(self):
        """Get the depth level of this category in the hierarchy."""
        if self.is_root:
            return 0
        return self.parent.level + 1
    
    def get_ancestors(self):
        """Get all ancestor categories up to the root."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return list(reversed(ancestors))
    
    def get_descendants(self):
        """Get all descendant categories recursively."""
        descendants = []
        for child in self.children.filter(is_active=True):
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def get_products_count(self, include_children=True):
        """Get count of products in this category and optionally children."""
        count = self.products.filter(is_active=True).count()
        if include_children:
            for child in self.children.filter(is_active=True):
                count += child.get_products_count(include_children=True)
        return count


class Product(TimeStampedModel):
    """
    Product model with comprehensive e-commerce features.
    
    Includes pricing, inventory, SEO, and flexible attributes.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    short_description = models.TextField(max_length=500, blank=True, null=True)
    
    # Pricing
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    compare_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Original price for showing discounts"
    )
    cost_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Cost price for profit calculations"
    )
    
    # Product identification
    sku = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True)
    
    # Category relationship
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    
    # Inventory
    stock = models.PositiveIntegerField(default=0)
    min_stock_level = models.PositiveIntegerField(
        default=5,
        help_text="Minimum stock level for low stock alerts"
    )
    
    # Physical properties
    weight = models.DecimalField(
        max_digits=8, 
        decimal_places=3, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Weight in kg"
    )
    dimensions_length = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Length in cm"
    )
    dimensions_width = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Width in cm"
    )
    dimensions_height = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Height in cm"
    )
    
    # Flexible attributes (JSON field)
    attributes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible product attributes as key-value pairs"
    )
    
    # Images (JSON field for image URLs/paths)
    images = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of image URLs or paths"
    )
    
    # Status flags
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_digital = models.BooleanField(
        default=False,
        help_text="Digital products don't require shipping"
    )
    requires_shipping = models.BooleanField(default=True)
    track_inventory = models.BooleanField(
        default=True,
        help_text="Whether to track inventory for this product"
    )
    allow_backorder = models.BooleanField(
        default=False,
        help_text="Allow orders when out of stock"
    )
    
    # SEO fields
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    tags = models.CharField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text="Comma-separated tags for search and filtering"
    )
    
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['price']),
            models.Index(fields=['stock']),
            models.Index(fields=['created_at']),
            models.Index(fields=['category', 'is_active', 'is_featured']),
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['price', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return the URL for this product."""
        return reverse('products:product-detail', kwargs={'slug': self.slug})
    
    @property
    def is_in_stock(self):
        """Check if product is in stock."""
        if not self.track_inventory:
            return True
        return self.stock > 0 or self.allow_backorder
    
    @property
    def is_low_stock(self):
        """Check if product stock is below minimum level."""
        if not self.track_inventory:
            return False
        return self.stock <= self.min_stock_level
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage if compare_price is set."""
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0
    
    @property
    def primary_image(self):
        """Get the primary product image."""
        if self.images and len(self.images) > 0:
            return self.images[0]
        return None
    
    def get_price_display(self):
        """Get formatted price with currency."""
        return f"${self.price:.2f}"
    
    def get_tags_list(self):
        """Convert tags string to list."""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def add_tag(self, tag):
        """Add a tag to the product."""
        tags_list = self.get_tags_list()
        if tag not in tags_list:
            tags_list.append(tag)
            self.tags = ', '.join(tags_list)
    
    def remove_tag(self, tag):
        """Remove a tag from the product."""
        tags_list = self.get_tags_list()
        if tag in tags_list:
            tags_list.remove(tag)
            self.tags = ', '.join(tags_list)


class ProductImage(TimeStampedModel):
    """
    Product image model for storing multiple images per product.
    
    Alternative to using JSON field for images.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_images'
    )
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['sort_order', 'created_at']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['sort_order']),
            models.Index(fields=['is_primary']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - Image {self.sort_order}"
    
    def save(self, *args, **kwargs):
        """Ensure only one primary image per product."""
        if self.is_primary:
            # Set all other images for this product as non-primary
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductVariant(TimeStampedModel):
    """
    Product variant model for handling product variations.
    
    Used for products with different sizes, colors, etc.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    
    # Override product price if set
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Override product price for this variant"
    )
    
    # Variant-specific inventory
    stock = models.PositiveIntegerField(default=0)
    
    # Variant attributes (size, color, etc.)
    attributes = models.JSONField(
        default=dict,
        help_text="Variant-specific attributes like size, color, etc."
    )
    
    # Variant-specific image
    image = models.ImageField(upload_to='variants/', blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'
        ordering = ['name']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['sku']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    @property
    def effective_price(self):
        """Get the effective price (variant price or product price)."""
        return self.price if self.price is not None else self.product.price
    
    @property
    def is_in_stock(self):
        """Check if variant is in stock."""
        return self.stock > 0


class StockMovement(TimeStampedModel):
    """
    Track inventory movements for audit and reporting.
    """
    MOVEMENT_TYPES = [
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
        ('damage', 'Damage'),
    ]
    
    REFERENCE_TYPES = [
        ('order', 'Order'),
        ('manual', 'Manual'),
        ('import', 'Import'),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='stock_movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity_change = models.IntegerField(
        help_text="Positive for increase, negative for decrease"
    )
    reference_type = models.CharField(max_length=20, choices=REFERENCE_TYPES)
    reference_id = models.UUIDField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='stock_movements'
    )
    
    class Meta:
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['movement_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.movement_type} ({self.quantity_change})"


class ProductReview(TimeStampedModel):
    """
    Product review and rating model.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='product_reviews'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Link to verified purchase"
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    review_text = models.TextField(blank=True, null=True)
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Product Review'
        verbose_name_plural = 'Product Reviews'
        ordering = ['-created_at']
        unique_together = ['user', 'product', 'order']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['user']),
            models.Index(fields=['rating']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.rating} stars by {self.user.username}"
