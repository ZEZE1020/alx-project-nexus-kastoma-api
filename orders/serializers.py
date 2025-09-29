"""
Orders app serializers.

Django REST Framework serializers for order management,
cart operations, and order status tracking.
"""

from rest_framework import serializers
from decimal import Decimal
from .models import Order, OrderItem, Cart, CartItem, Coupon, CouponUsage
from products.serializers import ProductListSerializer
from products.models import Product
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for order items within an order.
    """
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    variant_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = (
            'id', 'product', 'product_id', 'variant', 'variant_id', 'quantity', 
            'product_name', 'product_sku', 'unit_price', 'total_price', 
            'product_attributes', 'created_at', 'subtotal'
        )
        read_only_fields = ('id', 'product_name', 'product_sku', 'unit_price', 'total_price', 'created_at', 'subtotal')
    
    def get_subtotal(self, obj):
        """Calculate subtotal for this order item."""
        return obj.total_price
    
    def validate_quantity(self, value):
        """Ensure quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError(
                "Quantity must be greater than 0."
            )
        return value


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for order management.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    item_count = serializers.SerializerMethodField()
    billing_full_name = serializers.CharField(read_only=True)
    shipping_full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id', 'user', 'order_number', 'status', 'items', 'item_count',
            'customer_email', 'customer_phone',
            'billing_first_name', 'billing_last_name', 'billing_full_name',
            'billing_company', 'billing_address_line1', 'billing_address_line2',
            'billing_city', 'billing_state', 'billing_postal_code', 'billing_country',
            'shipping_first_name', 'shipping_last_name', 'shipping_full_name',
            'shipping_company', 'shipping_address_line1', 'shipping_address_line2',
            'shipping_city', 'shipping_state', 'shipping_postal_code', 'shipping_country',
            'subtotal', 'shipping_cost', 'tax_amount', 'discount_amount', 'total_amount',
            'payment_method', 'payment_status', 'payment_reference',
            'shipping_method', 'tracking_number', 'tracking_carrier', 'tracking_url',
            'estimated_delivery_date', 'notes', 'internal_notes',
            'created_at', 'updated_at', 'confirmed_at', 'shipped_at', 'delivered_at'
        )
        read_only_fields = (
            'id', 'user', 'order_number', 'item_count', 'billing_full_name', 'shipping_full_name',
            'created_at', 'updated_at', 'confirmed_at', 'shipped_at', 'delivered_at'
        )
    
    def get_item_count(self, obj):
        """Get total number of items in order."""
        return obj.item_count


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new orders.
    """
    items = OrderItemSerializer(many=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Order
        fields = (
            'items', 'customer_email', 'customer_phone',
            'billing_first_name', 'billing_last_name', 'billing_company',
            'billing_address_line1', 'billing_address_line2', 'billing_city',
            'billing_state', 'billing_postal_code', 'billing_country',
            'shipping_first_name', 'shipping_last_name', 'shipping_company',
            'shipping_address_line1', 'shipping_address_line2', 'shipping_city',
            'shipping_state', 'shipping_postal_code', 'shipping_country',
            'payment_method', 'shipping_method', 'notes', 'coupon_code'
        )
    
    def validate_items(self, value):
        """Validate order items."""
        if not value:
            raise serializers.ValidationError(
                "Order must contain at least one item."
            )
        return value
    
    def validate(self, attrs):
        """Validate order data."""
        # Ensure required fields are provided
        required_fields = [
            'customer_email', 'billing_first_name', 'billing_last_name',
            'billing_address_line1', 'billing_city', 'billing_postal_code', 'billing_country',
            'shipping_first_name', 'shipping_last_name', 'shipping_address_line1',
            'shipping_city', 'shipping_postal_code', 'shipping_country'
        ]
        
        for field in required_fields:
            if not attrs.get(field):
                raise serializers.ValidationError(
                    f"{field.replace('_', ' ').title()} is required."
                )
        
        return attrs
    
    def create(self, validated_data):
        """Create order with items."""
        items_data = validated_data.pop('items')
        coupon_code = validated_data.pop('coupon_code', None)
        order = Order.objects.create(**validated_data)
        
        # Create order items and calculate totals
        subtotal = Decimal('0.00')
        for item_data in items_data:
            product_id = item_data.pop('product_id')
            variant_id = item_data.pop('variant_id', None)
            quantity = item_data['quantity']
            
            product = Product.objects.get(id=product_id)
            variant = None
            
            # Get product price and info
            if variant_id:
                from products.models import ProductVariant
                try:
                    variant = ProductVariant.objects.get(id=variant_id, product=product)
                    unit_price = variant.effective_price
                    product_sku = variant.sku
                    product_attributes = {
                        'variant_name': variant.name,
                        'variant_attributes': variant.attributes
                    }
                except ProductVariant.DoesNotExist:
                    raise serializers.ValidationError("Product variant does not exist.")
            else:
                unit_price = product.price  
                product_sku = product.sku
                product_attributes = {}
            
            total_price = unit_price * quantity
            subtotal += total_price
            
            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                product_name=product.name,
                product_sku=product_sku,
                unit_price=unit_price,
                quantity=quantity,
                total_price=total_price,
                product_attributes=product_attributes
            )
        
        # Set order totals
        order.subtotal = subtotal
        
        # Apply coupon if provided
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                discount = coupon.calculate_discount(subtotal)
                if discount > 0:
                    order.discount_amount = discount
                    coupon.usage_count += 1
                    coupon.save()
                    
                    # Track coupon usage
                    CouponUsage.objects.create(
                        coupon=coupon,
                        order=order,
                        user=order.user,
                        discount_amount=discount
                    )
            except Coupon.DoesNotExist:
                pass  # Invalid coupon code, ignore
        
        # Calculate final total
        order.total_amount = order.subtotal + order.shipping_cost + order.tax_amount - order.discount_amount
        order.save()
        
        return order


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for cart items.
    """
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    variant_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    subtotal = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = (
            'id', 'product', 'product_id', 'variant', 'variant_id', 
            'quantity', 'price', 'subtotal', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_price(self, obj):
        """Get the effective price for this item."""
        return obj.get_price()
    
    def get_subtotal(self, obj):
        """Calculate subtotal for this cart item."""
        return obj.subtotal
    
    def validate_quantity(self, value):
        """Ensure quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError(
                "Quantity must be greater than 0."
            )
        return value
    
    def validate(self, attrs):
        """Validate cart item data."""
        product_id = attrs.get('product_id')
        variant_id = attrs.get('variant_id')
        quantity = attrs.get('quantity')
        
        if product_id and quantity:
            try:
                product = Product.objects.get(id=product_id)
                
                # Check stock availability
                if variant_id:
                    from products.models import ProductVariant
                    try:
                        variant = ProductVariant.objects.get(id=variant_id, product=product)
                        if quantity > variant.stock:
                            raise serializers.ValidationError(
                                f"Only {variant.stock} items available in stock for this variant."
                            )
                    except ProductVariant.DoesNotExist:
                        raise serializers.ValidationError("Product variant does not exist.")
                else:
                    if hasattr(product, 'stock') and quantity > product.stock:
                        raise serializers.ValidationError(
                            f"Only {product.stock} items available in stock."
                        )
                        
            except Product.DoesNotExist:
                raise serializers.ValidationError(
                    "Product does not exist."
                )
        
        return attrs


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for shopping cart.
    """
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = (
            'id', 'user', 'session_key', 'items', 'total_amount', 'item_count',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'session_key', 'created_at', 'updated_at')
    
    def get_total_amount(self, obj):
        """Calculate total cart amount."""
        return obj.total_amount
    
    def get_item_count(self, obj):
        """Get total number of items in cart."""
        return obj.item_count


class CouponSerializer(serializers.ModelSerializer):
    """
    Serializer for coupon management.
    """
    is_valid_coupon = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = (
            'id', 'code', 'name', 'description', 'discount_type', 'discount_value',
            'minimum_order_amount', 'maximum_discount_amount', 'usage_limit',
            'usage_count', 'is_active', 'is_valid_coupon', 'valid_from', 'valid_until',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'usage_count', 'is_valid_coupon', 'created_at', 'updated_at')
    
    def get_is_valid_coupon(self, obj):
        """Check if coupon is currently valid."""
        return obj.is_valid()


class OrderListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for order lists.
    """
    item_count = serializers.SerializerMethodField()
    billing_full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'status', 'item_count', 'total_amount',
            'billing_full_name', 'customer_email', 'payment_status',
            'created_at', 'updated_at'
        )
    
    def get_item_count(self, obj):
        """Get total number of items in order."""
        return obj.item_count


class OrderStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating order status.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_status(self, value):
        """Validate status transition."""
        # Add business logic for valid status transitions
        instance = self.instance
        if instance:
            current_status = instance.status
            
            # Define valid transitions
            valid_transitions = {
                'pending': ['confirmed', 'cancelled'],
                'confirmed': ['processing', 'cancelled'],
                'processing': ['shipped', 'cancelled'],
                'shipped': ['delivered'],
                'delivered': ['refunded'],
                'cancelled': [],
                'refunded': [],
            }
            
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Cannot change status from {current_status} to {value}."
                )
        
        return value


class OrderTrackingSerializer(serializers.Serializer):
    """
    Serializer for order tracking information.
    """
    tracking_number = serializers.CharField(max_length=100, required=False)
    carrier = serializers.CharField(max_length=50, required=False)
    tracking_url = serializers.URLField(required=False)
    estimated_delivery = serializers.DateTimeField(required=False)


# TODO: Uncomment and implement when Order model is created
# class OrderListSerializer(serializers.ModelSerializer):
#     """
#     Lightweight serializer for order lists.
#     """
#     item_count = serializers.SerializerMethodField()
#     total_amount = serializers.SerializerMethodField()
#     
#     class Meta:
#         model = Order
#         fields = (
#             'id', 'status', 'item_count', 'total_amount',
#             'created_at', 'updated_at'
#         )
#     
#     def get_item_count(self, obj):
#         """Get total number of items in order."""
#         return sum(item.quantity for item in obj.items.all())
#     
#     def get_total_amount(self, obj):
#         """Calculate total order amount."""
#         return sum(item.quantity * item.price for item in obj.items.all())