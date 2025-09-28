"""
Core app views.

This module contains base views and utilities that can be
reused across other apps in the project.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Base viewset with common functionality for all model viewsets.
    
    Provides:
    - Standard CRUD operations
    - Common filtering and ordering
    - Pagination
    - Error handling
    """
    
    def get_queryset(self):
        """
        Override to add common filtering logic.
        Child classes should call super().get_queryset() and then apply
        their specific filters.
        """
        queryset = super().get_queryset()
        
        # Add common filters here if needed
        # Example: Filter by active status
        # if hasattribute(queryset.model, 'is_active'):
        #     queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Customize object creation.
        Override in child classes for specific creation logic.
        """
        serializer.save()
    
    def perform_update(self, serializer):
        """
        Customize object updates.
        Override in child classes for specific update logic.
        """
        serializer.save()
    
    def perform_destroy(self, instance):
        """
        Customize object deletion.
        Override for soft delete functionality.
        """
        # Example soft delete implementation:
        # if hasattr(instance, 'is_active'):
        #     instance.is_active = False
        #     instance.save()
        # else:
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Generic stats endpoint that can be overridden by child classes.
        """
        queryset = self.get_queryset()
        return Response({
            'total_count': queryset.count(),
            'timestamp': timezone.now()
        })


class ReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Base read-only viewset for models that should not be modified via API.
    """
    
    def get_queryset(self):
        """
        Override to add common filtering logic.
        """
        queryset = super().get_queryset()
        return queryset
