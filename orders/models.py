"""
Orders app models.

Shopping cart, order management, and payment tracking models.
"""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

if TYPE_CHECKING:
    from django.db.models import QuerySet

User = get_user_model()


class TimeStampedModel(models.Model):
    """
    Abstract base model with UUID primary key and timestamps.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Cart(TimeStampedModel):
    """
    Shopping cart model for both authenticated and anonymous users.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='carts'
    )
    session_key = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        help_text="Session key for anonymous users"
    )
    
    if TYPE_CHECKING:
        items: "QuerySet[CartItem]"
    
    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.get_full_name()}"
        return f"Anonymous Cart ({self.session_key})"
    
    @property
    def item_count(self):
        """Get total number of items in cart."""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_amount(self):
        """Calculate total cart amount."""
        return sum(
            item.quantity * item.get_price()
            for item in self.items.all()
        )
    
    def clear(self):
        """Remove all items from cart."""
        self.items.all().delete()


class CartItem(TimeStampedModel):
    """
    Items in a shopping cart.
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        unique_together = ['cart', 'product', 'variant']
        indexes = [
            models.Index(fields=['cart']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        variant_info = f" ({self.variant.name})" if self.variant else ""
        return f"{self.product.name}{variant_info} x{self.quantity}"
    
    def get_price(self):
        """Get the effective price for this item."""
        if self.variant:
            return self.variant.effective_price
        return self.product.price
    
    @property
    def subtotal(self):
        """Calculate subtotal for this cart item."""
        return self.quantity * self.get_price()


class Order(TimeStampedModel):
    """
    Order model with comprehensive e-commerce features.
    """
    ORDER_STATUSES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    if TYPE_CHECKING:
        items: "QuerySet[OrderItem]"
    
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]
    
    PAYMENT_STATUSES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]
    
    # Basic order information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='orders'
    )
    order_number = models.CharField(max_length=32, unique=True)
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUSES,
        default='pending'
    )
    
    # Customer information
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Billing address
    billing_first_name = models.CharField(max_length=50)
    billing_last_name = models.CharField(max_length=50)
    billing_company = models.CharField(max_length=100, blank=True, null=True)
    billing_address_line1 = models.CharField(max_length=255)
    billing_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=100, blank=True, null=True)
    billing_postal_code = models.CharField(max_length=20)
    billing_country = models.CharField(max_length=100)
    
    # Shipping address
    shipping_first_name = models.CharField(max_length=50)
    shipping_last_name = models.CharField(max_length=50)
    shipping_company = models.CharField(max_length=100, blank=True, null=True)
    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100, blank=True, null=True)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100)
    
    # Financial information
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    
    # Payment information
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        blank=True,
        null=True
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUSES,
        default='pending'
    )
    payment_reference = models.CharField(max_length=255, blank=True, null=True)
    
    # Shipping information
    shipping_method = models.CharField(max_length=100, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    tracking_carrier = models.CharField(max_length=50, blank=True, null=True)
    tracking_url = models.URLField(max_length=500, blank=True, null=True)
    estimated_delivery_date = models.DateField(blank=True, null=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    internal_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Staff-only notes"
    )
    
    # Additional timestamps
    confirmed_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['customer_email']),
            models.Index(fields=['created_at']),
            models.Index(fields=['total_amount']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['payment_status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        """Generate order number if not provided."""
        if not self.order_number:
            import time
            timestamp = str(int(time.time()))
            self.order_number = f"KAS-{timestamp[-8:]}"
        super().save(*args, **kwargs)
    
    @property
    def item_count(self):
        """Get total number of items in order."""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def billing_full_name(self):
        """Get full billing name."""
        return f"{self.billing_first_name} {self.billing_last_name}"
    
    @property
    def shipping_full_name(self):
        """Get full shipping name."""
        return f"{self.shipping_first_name} {self.shipping_last_name}"
    
    def get_billing_address(self):
        """Get formatted billing address."""
        address_parts = [
            self.billing_address_line1,
            self.billing_address_line2,
            self.billing_city,
            self.billing_state,
            self.billing_postal_code,
            self.billing_country
        ]
        return ', '.join(part for part in address_parts if part)
    
    def get_shipping_address(self):
        """Get formatted shipping address."""
        address_parts = [
            self.shipping_address_line1,
            self.shipping_address_line2,
            self.shipping_city,
            self.shipping_state,
            self.shipping_postal_code,
            self.shipping_country
        ]
        return ', '.join(part for part in address_parts if part)
    
    def can_be_cancelled(self):
        """Check if order can be cancelled."""
        return self.status in ['pending', 'confirmed']
    
    def calculate_totals(self):
        """Recalculate order totals based on items."""
        self.subtotal = sum(
            item.total_price for item in self.items.all()
        )
        self.total_amount = (
            self.subtotal + 
            self.shipping_cost + 
            self.tax_amount - 
            self.discount_amount
        )


class OrderItem(TimeStampedModel):
    """
    Items in an order with historical product information.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='order_items'
    )
    
    # Product information at time of order
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=100)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Product attributes at time of order
    product_attributes = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity} - {self.order.order_number}"
    
    def save(self, *args, **kwargs):
        """Calculate total price automatically."""
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class Coupon(TimeStampedModel):
    """
    Discount coupon model.
    """
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    maximum_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    usage_limit = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Leave blank for unlimited usage"
    )
    usage_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['valid_from']),
            models.Index(fields=['valid_until']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def is_valid(self):
        """Check if coupon is currently valid."""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.valid_from > now:
            return False
        
        if self.valid_until and self.valid_until < now:
            return False
        
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        
        return True
    
    def calculate_discount(self, order_amount):
        """Calculate discount amount for given order amount."""
        if not self.is_valid():
            return Decimal('0.00')
        
        if self.minimum_order_amount and order_amount < self.minimum_order_amount:
            return Decimal('0.00')
        
        if self.discount_type == 'percentage':
            discount = order_amount * (self.discount_value / 100)
        else:  # fixed_amount
            discount = self.discount_value
        
        if self.maximum_discount_amount:
            discount = min(discount, self.maximum_discount_amount)
        
        return min(discount, order_amount)


class CouponUsage(TimeStampedModel):
    """
    Track coupon usage for analytics and limits.
    """
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='usages'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='coupon_usages'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='coupon_usages'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Coupon Usage'
        verbose_name_plural = 'Coupon Usages'
        ordering = ['-used_at']
        indexes = [
            models.Index(fields=['coupon']),
            models.Index(fields=['order']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.coupon.code} used in {self.order.order_number}"
