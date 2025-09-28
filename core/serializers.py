"""
Core app serializers.

This module contains base serializers and common utilities
that can be reused across other apps.
"""

from rest_framework import serializers


class TimestampedModelSerializer(serializers.ModelSerializer):
    """
    Base serializer for models with created_at and updated_at fields.
    Provides read-only access to timestamp fields.
    """
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        abstract = True


class BaseModelSerializer(TimestampedModelSerializer):
    """
    Enhanced base serializer with common functionality.
    """
    
    def to_representation(self, instance):
        """
        Customize the representation of model instances.
        Can be overridden in child classes for specific formatting.
        """
        data = super().to_representation(instance)
        
        # Remove None values from the response (optional)
        # return {key: value for key, value in data.items() if value is not None}
        
        return data
    
    def validate(self, attrs):
        """
        Object-level validation.
        Override in child classes for custom validation logic.
        """
        return super().validate(attrs)