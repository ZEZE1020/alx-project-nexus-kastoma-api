"""
Orders app views.

API views for order management, cart operations,
and order status tracking using Django REST Framework.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from core.views import BaseModelViewSet
from .models import Order, OrderItem, Cart, CartItem, Coupon
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderListSerializer,
    CartSerializer,
    CartItemSerializer,
    OrderStatusUpdateSerializer,
    OrderTrackingSerializer,
    CouponSerializer,
)


class OrderViewSet(BaseModelViewSet):
    """
    ViewSet for order management.
    
    Provides:
    - List user's orders
    - Retrieve order details
    - Create new orders
    - Update order status (admin only)
    - Cancel orders
    """
    queryset = Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter orders based on user permissions."""
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(user=user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'list':
            return OrderListSerializer
        return OrderSerializer
    
    def perform_create(self, serializer):
        """Associate order with current user."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def update_status(self, request, pk=None):
        """Update order status (admin only)."""
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(
            order, 
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            notes = serializer.validated_data.get('notes', '')
            
            order.status = new_status
            if notes:
                order.internal_notes = notes
            
            # Set timestamps based on status
            if new_status == 'confirmed' and not order.confirmed_at:
                order.confirmed_at = timezone.now()
            elif new_status == 'shipped' and not order.shipped_at:
                order.shipped_at = timezone.now()
            elif new_status == 'delivered' and not order.delivered_at:
                order.delivered_at = timezone.now()
            
            order.save()
            
            return Response(OrderSerializer(order).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order (user or admin)."""
        order = self.get_object()
        
        # Only allow cancellation for certain statuses
        if not order.can_be_cancelled():
            return Response(
                {'error': 'Order cannot be cancelled at this stage.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'cancelled'
        order.save()
        
        return Response(OrderSerializer(order).data)
    
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def add_tracking(self, request, pk=None):
        """Add tracking information to order."""
        order = self.get_object()
        serializer = OrderTrackingSerializer(data=request.data)
        
        if serializer.is_valid():
            for field, value in serializer.validated_data.items():
                if field == 'tracking_number':
                    order.tracking_number = value
                elif field == 'carrier':
                    order.tracking_carrier = value
                elif field == 'tracking_url':
                    order.tracking_url = value
                elif field == 'estimated_delivery':
                    order.estimated_delivery_date = value
            order.save()
            
            return Response(OrderSerializer(order).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """Get current user's orders."""
        orders = self.get_queryset().filter(user=request.user)
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def validate_coupon(self, request):
        """Validate a coupon code."""
        coupon_code = request.data.get('code')
        if not coupon_code:
            return Response(
                {'error': 'Coupon code is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.is_valid():
                return Response({
                    'valid': True,
                    'coupon': CouponSerializer(coupon).data
                })
            else:
                return Response({
                    'valid': False,
                    'error': 'Coupon is not valid or has expired.'
                })
        except Coupon.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Coupon does not exist.'
            })


class CartViewSet(BaseModelViewSet):
    """
    ViewSet for shopping cart management.
    
    Provides:
    - Get user's cart
    - Add items to cart
    - Update item quantities
    - Remove items from cart
    - Clear cart
    """
    queryset = Cart.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get current user's cart."""
        return self.queryset.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        return CartSerializer
    
    def get_object(self):
        """Get or create user's cart."""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart
    
    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        """Get current user's cart."""
        cart = self.get_object()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add item to cart."""
        cart = self.get_object()
        serializer = CartItemSerializer(data=request.data)
        
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            variant_id = serializer.validated_data.get('variant_id')
            quantity = serializer.validated_data['quantity']
            
            # Check if item already exists in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_id=product_id,
                variant_id=variant_id,
                defaults={'quantity': quantity}
            )
            
            if not created:
                # Update quantity if item already exists
                cart_item.quantity += quantity
                cart_item.save()
            
            return Response(CartSerializer(cart).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['patch'])
    def update_item(self, request):
        """Update cart item quantity."""
        cart = self.get_object()
        product_id = request.data.get('product_id')
        variant_id = request.data.get('variant_id')
        quantity = request.data.get('quantity')
        
        if not product_id or quantity is None:
            return Response(
                {'error': 'product_id and quantity are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cart_item = CartItem.objects.get(
                cart=cart, 
                product_id=product_id,
                variant_id=variant_id
            )
            
            if quantity <= 0:
                cart_item.delete()
            else:
                cart_item.quantity = quantity
                cart_item.save()
            
            return Response(CartSerializer(cart).data)
        
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['delete'])
    def remove_item(self, request):
        """Remove item from cart."""
        cart = self.get_object()
        product_id = request.data.get('product_id')
        variant_id = request.data.get('variant_id')
        
        if not product_id:
            return Response(
                {'error': 'product_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cart_item = CartItem.objects.get(
                cart=cart, 
                product_id=product_id,
                variant_id=variant_id
            )
            cart_item.delete()
            return Response(CartSerializer(cart).data)
        
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all items from cart."""
        cart = self.get_object()
        cart.clear()
        return Response(CartSerializer(cart).data)
    
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """Convert cart to order."""
        cart = self.get_object()
        
        if not cart.items.exists():
            return Response(
                {'error': 'Cart is empty.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create order from cart
        order_data = {
            'items': [
                {
                    'product_id': str(item.product.id),
                    'variant_id': str(item.variant.id) if item.variant else None,
                    'quantity': item.quantity
                }
                for item in cart.items.all()
            ],
            **request.data  # Include shipping/billing info from request
        }
        
        order_serializer = OrderCreateSerializer(data=order_data)
        if order_serializer.is_valid():
            order = order_serializer.save(user=request.user)
            
            # Clear cart after successful order creation
            cart.clear()
            
            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
