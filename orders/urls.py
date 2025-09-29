"""
Orders app URL configuration.

Defines REST API endpoints for order and cart management
using Django REST Framework routers.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for API endpoints
router = DefaultRouter()

# Register ViewSets
router.register(r'orders', views.OrderViewSet)
router.register(r'cart', views.CartViewSet, basename='cart')

app_name = 'orders'

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
]

# Example URL patterns that will be available when views are implemented:
#
# Order Management:
# GET    /api/v1/orders/                          - List orders (user's own or all for admin)
# POST   /api/v1/orders/                          - Create new order
# GET    /api/v1/orders/{id}/                     - Get order details
# PUT    /api/v1/orders/{id}/                     - Update order (admin only)
# DELETE /api/v1/orders/{id}/                     - Delete order (admin only)
# GET    /api/v1/orders/my_orders/                - Get current user's orders
# POST   /api/v1/orders/{id}/cancel/              - Cancel order
# PATCH  /api/v1/orders/{id}/update_status/       - Update order status (admin)
# PATCH  /api/v1/orders/{id}/add_tracking/        - Add tracking info (admin)
#
# Cart Management:
# GET    /api/v1/cart/                            - Get user's cart (auto-created)
# GET    /api/v1/cart/my_cart/                    - Get current user's cart
# POST   /api/v1/cart/add_item/                   - Add item to cart
# PATCH  /api/v1/cart/update_item/                - Update cart item quantity
# DELETE /api/v1/cart/remove_item/                - Remove item from cart
# DELETE /api/v1/cart/clear/                      - Clear entire cart
# POST   /api/v1/cart/checkout/                   - Convert cart to order