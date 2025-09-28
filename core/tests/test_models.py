"""
Simple tests for core models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import SiteSetting, EmailTemplate, PageView, APILog

User = get_user_model()


class SiteSettingTest(TestCase):
    """Test SiteSetting model."""

    def test_string_setting(self):
        """Test string setting creation and retrieval."""
        setting = SiteSetting.objects.create(
            key_name='site_name',
            value='Kastoma API',
            setting_type='string'
        )
        self.assertEqual(setting.get_value(), 'Kastoma API')
        self.assertEqual(str(setting), 'site_name: Kastoma API')

    def test_boolean_setting(self):
        """Test boolean setting type conversion."""
        setting = SiteSetting.objects.create(
            key_name='maintenance_mode',
            value='true',
            setting_type='boolean'
        )
        self.assertTrue(setting.get_value())


class EmailTemplateTest(TestCase):
    """Test EmailTemplate model."""

    def test_template_creation(self):
        """Test email template creation."""
        template = EmailTemplate.objects.create(
            name='welcome',
            subject='Welcome {{ name }}',
            html_content='<h1>Hello {{ name }}!</h1>',
            is_active=True
        )
        self.assertEqual(str(template), 'welcome')
        self.assertTrue(template.is_active)

    def test_template_rendering(self):
        """Test template rendering with context."""
        template = EmailTemplate.objects.create(
            name='test',
            subject='Hello {{ name }}',
            html_content='<p>Welcome {{ name }}!</p>'
        )
        context = {'name': 'John'}
        self.assertEqual(template.render_subject(context), 'Hello John')
        self.assertEqual(template.render_html_content(context), '<p>Welcome John!</p>')


class PageViewTest(TestCase):
    """Test PageView model."""

    def test_page_view_creation(self):
        """Test page view creation."""
        view = PageView.objects.create(
            path='/test/',
            ip_address='127.0.0.1'
        )
        self.assertEqual(view.path, '/test/')
        self.assertIsNotNone(view.id)


class APILogTest(TestCase):
    """Test APILog model."""

    def test_api_log_creation(self):
        """Test API log creation."""
        log = APILog.objects.create(
            path='/api/test/',
            method='GET',
            response_status=200
        )
        self.assertEqual(log.method, 'GET')
        self.assertEqual(log.response_status, 200)
        self.assertIsNotNone(log.id)