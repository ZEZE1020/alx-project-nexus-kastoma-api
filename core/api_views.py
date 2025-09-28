"""
Core API views for testing.
"""
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import SiteSetting, PageView, EmailTemplate, APILog
from .api_serializers import (
    SiteSettingSerializer, 
    PageViewSerializer, 
    EmailTemplateSerializer, 
    APILogSerializer
)
from .views import BaseModelViewSet, ReadOnlyModelViewSet


class SiteSettingViewSet(BaseModelViewSet):
    """
    ViewSet for managing site settings.
    Provides CRUD operations for site configuration.
    """
    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer
    permission_classes = [permissions.AllowAny]  # Allow access without authentication for testing
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['setting_type', 'is_active']
    search_fields = ['key_name', 'description']
    ordering_fields = ['key_name', 'created_at']
    ordering = ['key_name']

    @action(detail=False, methods=['get'])
    def active_settings(self, request):
        """Get all active settings as key-value pairs."""
        active_settings = self.queryset.filter(is_active=True)
        settings_dict = {
            setting.key_name: setting.get_value() 
            for setting in active_settings
        }
        return Response(settings_dict)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get settings grouped by type."""
        settings_by_type = {}
        for setting in self.queryset.filter(is_active=True):
            if setting.setting_type not in settings_by_type:
                settings_by_type[setting.setting_type] = []
            settings_by_type[setting.setting_type].append({
                'key_name': setting.key_name,
                'value': setting.get_value(),
                'description': setting.description
            })
        return Response(settings_by_type)


class PageViewViewSet(ReadOnlyModelViewSet):
    """
    Read-only ViewSet for page views analytics.
    """
    queryset = PageView.objects.all()
    serializer_class = PageViewSerializer
    permission_classes = [permissions.AllowAny]  # Allow access without authentication for testing
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['path', 'user']
    ordering_fields = ['created_at', 'path']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def popular_pages(self, request):
        """Get most popular pages by view count."""
        from django.db.models import Count
        
        popular_pages = (
            self.queryset
            .values('path')
            .annotate(view_count=Count('id'))
            .order_by('-view_count')[:10]
        )
        return Response(popular_pages)

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get basic analytics data."""
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        analytics_data = {
            'total_views': self.queryset.count(),
            'views_last_24h': self.queryset.filter(created_at__gte=last_24h).count(),
            'views_last_7d': self.queryset.filter(created_at__gte=last_7d).count(),
            'unique_visitors': self.queryset.values('ip_address').distinct().count(),
            'top_pages': list(
                self.queryset
                .values('path')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            )
        }
        return Response(analytics_data)


class EmailTemplateViewSet(BaseModelViewSet):
    """
    ViewSet for managing email templates.
    """
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [permissions.AllowAny]  # Allow access without authentication for testing
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'subject']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['post'])
    def render_template(self, request, pk=None):
        """Render template with provided context."""
        template = self.get_object()
        context = request.data.get('context', {})
        
        try:
            rendered_data = {
                'subject': template.render_subject(context),
                'html_content': template.render_html_content(context),
                'text_content': template.render_text_content(context)
            }
            return Response(rendered_data)
        except Exception as e:
            return Response(
                {'error': f'Template rendering failed: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def active_templates(self, request):
        """Get all active templates."""
        active_templates = self.queryset.filter(is_active=True)
        serializer = self.get_serializer(active_templates, many=True)
        return Response(serializer.data)


class APILogViewSet(ReadOnlyModelViewSet):
    """
    Read-only ViewSet for API request logs.
    """
    queryset = APILog.objects.all()
    serializer_class = APILogSerializer
    permission_classes = [permissions.AllowAny]  # Allow access without authentication for testing
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['method', 'response_status', 'user']
    ordering_fields = ['created_at', 'response_time']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def api_stats(self, request):
        """Get API usage statistics."""
        from django.db.models import Count, Avg
        
        stats = {
            'total_requests': self.queryset.count(),
            'requests_by_method': dict(
                self.queryset
                .values('method')
                .annotate(count=Count('id'))
                .values_list('method', 'count')
            ),
            'requests_by_status': dict(
                self.queryset
                .values('response_status')
                .annotate(count=Count('id'))
                .values_list('response_status', 'count')
            ),
            'average_response_time': self.queryset.aggregate(
                avg_time=Avg('response_time')
            )['avg_time'] or 0,
            'top_endpoints': list(
                self.queryset
                .values('path')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            )
        }
        return Response(stats)