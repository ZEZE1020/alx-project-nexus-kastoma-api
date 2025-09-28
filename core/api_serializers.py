"""
Core API serializers for testing.
"""
from rest_framework import serializers
from .models import SiteSetting, PageView, EmailTemplate, APILog
from .serializers import BaseModelSerializer


class SiteSettingSerializer(BaseModelSerializer):
    """Serializer for SiteSetting model."""
    
    class Meta:
        model = SiteSetting
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def to_representation(self, instance):
        """Add typed value to representation."""
        data = super().to_representation(instance)
        data['typed_value'] = instance.get_value()
        return data


class PageViewSerializer(BaseModelSerializer):
    """Serializer for PageView model."""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = PageView
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class EmailTemplateSerializer(BaseModelSerializer):
    """Serializer for EmailTemplate model."""
    
    class Meta:
        model = EmailTemplate
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class APILogSerializer(BaseModelSerializer):
    """Serializer for APILog model."""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = APILog
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')