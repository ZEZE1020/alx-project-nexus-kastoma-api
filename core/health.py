"""
Health check views for monitoring and deployment readiness.

This module provides health check endpoints that can be used by:
- Load balancers to check if the service is ready to receive traffic
- Monitoring systems to verify service health
- Container orchestration platforms (Docker, Kubernetes) for health checks
"""

import json
import logging
from datetime import datetime

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.conf import settings

logger = logging.getLogger(__name__)


@never_cache
@csrf_exempt
@require_GET
def health_check(request):
    """
    Basic health check endpoint.
    
    Returns a simple JSON response indicating the service is running.
    This is useful for basic liveness probes.
    
    Returns:
        JsonResponse: {'status': 'ok', 'timestamp': ISO timestamp}
    """
    return JsonResponse({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'service': 'kastoma-api',
        'version': '1.0.0'
    })


@never_cache
@csrf_exempt
@require_GET
def health_check_detailed(request):
    """
    Detailed health check endpoint for comprehensive monitoring.
    
    Performs various health checks including:
    - Database connectivity
    - Basic service functionality
    - Environment information
    
    Returns:
        JsonResponse: Detailed health status with individual component checks
    """
    health_status = {
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'service': 'kastoma-api',
        'version': '1.0.0',
        'checks': {}
    }
    
    overall_status = True
    
    # Database health check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful',
            'response_time_ms': None  # Could add timing if needed
        }
    except Exception as e:
        overall_status = False
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}',
            'response_time_ms': None
        }
        logger.error(f"Database health check failed: {e}")
    
    # Static files check (in production)
    if not settings.DEBUG:
        try:
            import os
            static_root = settings.STATIC_ROOT
            if os.path.exists(static_root) and os.listdir(static_root):
                health_status['checks']['static_files'] = {
                    'status': 'healthy',
                    'message': 'Static files are available'
                }
            else:
                health_status['checks']['static_files'] = {
                    'status': 'warning',
                    'message': 'Static files directory is empty or missing'
                }
        except Exception as e:
            health_status['checks']['static_files'] = {
                'status': 'warning',
                'message': f'Static files check failed: {str(e)}'
            }
    
    # Environment check
    health_status['checks']['environment'] = {
        'status': 'healthy',
        'debug_mode': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS if settings.DEBUG else ['***hidden***'],
        'database_engine': settings.DATABASES['default']['ENGINE'].split('.')[-1],
    }
    
    # Memory usage check (optional)
    try:
        import psutil
        memory = psutil.virtual_memory()
        health_status['checks']['memory'] = {
            'status': 'healthy' if memory.percent < 90 else 'warning',
            'usage_percent': memory.percent,
            'available_mb': round(memory.available / 1024 / 1024, 2)
        }
    except ImportError:
        # psutil not installed, skip memory check
        pass
    except Exception as e:
        health_status['checks']['memory'] = {
            'status': 'warning',
            'message': f'Memory check failed: {str(e)}'
        }
    
    # Set overall status
    if not overall_status:
        health_status['status'] = 'degraded'
    
    # Return appropriate HTTP status code
    status_code = 200 if overall_status else 503
    
    return JsonResponse(health_status, status=status_code)


@never_cache
@csrf_exempt
@require_GET
def readiness_check(request):
    """
    Readiness check endpoint for deployment readiness.
    
    This endpoint should return 200 only when the service is fully ready
    to handle requests. Useful for Kubernetes readiness probes.
    
    Returns:
        JsonResponse: Readiness status
    """
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        # Check if migrations are up to date
        from django.core.management.commands.migrate import Command
        from django.db import connections
        from django.db.migrations.executor import MigrationExecutor
        
        executor = MigrationExecutor(connections['default'])
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            return JsonResponse({
                'status': 'not_ready',
                'message': 'Pending database migrations',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }, status=503)
        
        return JsonResponse({
            'status': 'ready',
            'message': 'Service is ready to handle requests',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JsonResponse({
            'status': 'not_ready',
            'message': f'Service is not ready: {str(e)}',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }, status=503)


@never_cache
@csrf_exempt
@require_GET
def liveness_check(request):
    """
    Liveness check endpoint for basic service availability.
    
    This is a minimal endpoint that should always return 200 unless
    the service is completely down. Useful for Kubernetes liveness probes.
    
    Returns:
        JsonResponse: Simple alive status
    """
    return JsonResponse({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })