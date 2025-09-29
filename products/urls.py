"""
Products app URL configuration.

Defines REST API endpoints for product and category management
using Django REST Framework routers.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
# from . import views  # Uncomment when views are implemented

# Create router for API endpoints
router = DefaultRouter()

# TODO: Uncomment when views are implemented
# router.register(r'products', views.ProductViewSet)
# router.register(r'categories', views.CategoryViewSet)

app_name = 'products'

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # TODO: Add custom endpoints if needed
    # path('products/search/', views.ProductSearchView.as_view(), name='product-search'),
    # path('categories/tree/', views.CategoryTreeView.as_view(), name='category-tree'),
]

# Example URL patterns that will be available when views are implemented:
# GET    /api/v1/products/                    - List products
# POST   /api/v1/products/                    - Create product (admin)
# GET    /api/v1/products/{id}/               - Get product details
# PUT    /api/v1/products/{id}/               - Update product (admin)
# DELETE /api/v1/products/{id}/               - Delete product (admin)
# GET    /api/v1/products/featured/           - Get featured products
# GET    /api/v1/products/low_stock/          - Get low stock products
# POST   /api/v1/products/{id}/update_stock/  - Update product stock
#
# GET    /api/v1/categories/                  - List categories
# POST   /api/v1/categories/                  - Create category (admin)
# GET    /api/v1/categories/{id}/             - Get category details
# PUT    /api/v1/categories/{id}/             - Update category (admin)
# DELETE /api/v1/categories/{id}/             - Delete category (admin)
# GET    /api/v1/categories/tree/             - Get category tree
# GET    /api/v1/categories/{id}/products/    - Get products in category