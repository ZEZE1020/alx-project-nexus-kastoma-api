"""
Core app models.

Base models and utilities used across the application.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TimeStampedModel(models.Model):
    """
    Abstract base model with UUID primary key and timestamps.
    
    Provides common fields for all models in the application.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class SiteSetting(models.Model):
    """
    Site-wide configuration settings.
    
    Allows dynamic configuration of site settings through the admin interface.
    """
    SETTING_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    ]
    
    key_name = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    setting_type = models.CharField(
        max_length=20, 
        choices=SETTING_TYPES, 
        default='string'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Setting'
        verbose_name_plural = 'Site Settings'
        ordering = ['key_name']
        indexes = [
            models.Index(fields=['key_name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.key_name}: {self.value}"
    
    def get_value(self):
        """
        Get the typed value based on setting_type.
        """
        if not self.value:
            return None
            
        if self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == 'integer':
            try:
                return int(self.value)
            except (ValueError, TypeError):
                return 0
        elif self.setting_type == 'json':
            import json
            try:
                return json.loads(self.value)
            except (ValueError, TypeError):
                return {}
        else:  # string
            return self.value
    
    @classmethod
    def get_setting(cls, key, default=None):
        """
        Get a setting value by key.
        """
        try:
            setting = cls.objects.get(key_name=key, is_active=True)
            return setting.get_value()
        except cls.DoesNotExist:
            return default


class PageView(TimeStampedModel):
    """
    Track page views for analytics.
    
    Simple analytics model to track user behavior and popular pages.
    """
    path = models.CharField(max_length=500)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='page_views'
    )
    session_key = models.CharField(max_length=40, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    referer = models.CharField(max_length=500, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Page View'
        verbose_name_plural = 'Page Views'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['path']),
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        user_info = self.user.username if self.user else 'Anonymous'
        return f"{self.path} - {user_info} - {self.created_at}"
    
    @classmethod
    def record_view(cls, request, path=None):
        """
        Convenience method to record a page view.
        """
        if path is None:
            path = request.path
            
        # Get user if authenticated
        user = request.user if request.user.is_authenticated else None
        
        # Get session key
        session_key = request.session.session_key
        
        # Get IP address
        ip_address = cls.get_client_ip(request)
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Get referer
        referer = request.META.get('HTTP_REFERER', '')
        
        return cls.objects.create(
            path=path,
            user=user,
            session_key=session_key,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer
        )
    
    @staticmethod
    def get_client_ip(request):
        """
        Get the client IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class EmailTemplate(TimeStampedModel):
    """
    Email template model for dynamic email content.
    
    Allows customization of email templates through the admin interface.
    """
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=255)
    html_content = models.TextField()
    text_content = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def render_subject(self, context=None):
        """
        Render the subject template with context variables.
        """
        if context:
            from django.template import Template, Context
            template = Template(self.subject)
            return template.render(Context(context))
        return self.subject
    
    def render_html_content(self, context=None):
        """
        Render the HTML content template with context variables.
        """
        if context:
            from django.template import Template, Context
            template = Template(self.html_content)
            return template.render(Context(context))
        return self.html_content
    
    def render_text_content(self, context=None):
        """
        Render the text content template with context variables.
        """
        if context and self.text_content:
            from django.template import Template, Context
            template = Template(self.text_content)
            return template.render(Context(context))
        return self.text_content or ''


class APILog(TimeStampedModel):
    """
    Log API requests for monitoring and debugging.
    """
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='api_logs'
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    request_data = models.JSONField(default=dict, blank=True)
    response_status = models.PositiveIntegerField(blank=True, null=True)
    response_time = models.FloatField(blank=True, null=True)  # in seconds
    
    class Meta:
        verbose_name = 'API Log'
        verbose_name_plural = 'API Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['path']),
            models.Index(fields=['method']),
            models.Index(fields=['user']),
            models.Index(fields=['response_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        user_info = self.user.username if self.user else 'Anonymous'
        return f"{self.method} {self.path} - {user_info} - {self.response_status}"
