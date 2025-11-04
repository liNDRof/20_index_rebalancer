"""
Custom Middleware for Comprehensive Logging and Error Tracking
Uses specialized loggers for different aspects of the system
"""

import logging
import time
import traceback
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

# Get specialized loggers
request_logger = logging.getLogger('requests')
error_logger = logging.getLogger('errors')
perf_logger = logging.getLogger('performance')
activity_logger = logging.getLogger('user_activity')
debug_logger = logging.getLogger('debug')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all incoming requests and outgoing responses
    Tracks request path, method, user, response time, and status code
    """

    def process_request(self, request):
        """Log incoming request"""
        request._start_time = time.time()

        # Get user info
        user = 'Anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user.username

        # Log request details
        request_logger.info(
            f">>> REQUEST | {request.method} {request.path} | "
            f"User: {user} | IP: {self._get_client_ip(request)}"
        )

        # Log request body for POST/PUT/PATCH
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                if request.content_type == 'application/json' and request.body:
                    body = json.loads(request.body)
                    # Don't log sensitive data like passwords
                    safe_body = self._sanitize_data(body)
                    debug_logger.debug(f"    Request body: {safe_body}")
            except:
                pass

    def process_response(self, request, response):
        """Log outgoing response"""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time

            # Get user info
            user = 'Anonymous'
            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user.username

            # Determine log level based on status code
            status = response.status_code
            if 200 <= status < 300:
                log_level = logging.INFO
                status_text = "SUCCESS"
            elif 300 <= status < 400:
                log_level = logging.INFO
                status_text = "REDIRECT"
            elif 400 <= status < 500:
                log_level = logging.WARNING
                status_text = "CLIENT_ERROR"
            else:
                log_level = logging.ERROR
                status_text = "SERVER_ERROR"

            # Log response
            request_logger.log(
                log_level,
                f"<<< RESPONSE | {request.method} {request.path} | "
                f"User: {user} | Status: {status} ({status_text}) | "
                f"Duration: {duration:.3f}s"
            )

            # Log response body for errors (if JSON)
            if status >= 400:
                try:
                    if hasattr(response, 'content') and response.content:
                        content = json.loads(response.content)
                        error_logger.error(f"    Error response: {content}")
                        debug_logger.debug(f"    Full error response: {content}")
                except:
                    pass

        return response

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip

    def _sanitize_data(self, data):
        """Remove sensitive information from logs"""
        if not isinstance(data, dict):
            return data

        sensitive_keys = ['password', 'secret', 'token', 'api_key', 'api_secret']
        sanitized = {}

        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value

        return sanitized


class ExceptionLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to catch and log all unhandled exceptions
    Provides detailed error information for debugging
    """

    def process_exception(self, request, exception):
        """Log unhandled exceptions with full traceback"""

        # Get user info
        user = 'Anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user.username

        # Get request duration if available
        duration = "N/A"
        if hasattr(request, '_start_time'):
            duration = f"{time.time() - request._start_time:.3f}s"

        # Log the exception with full details
        error_logger.error(
            f"\n{'='*80}\n"
            f"UNHANDLED EXCEPTION\n"
            f"{'='*80}\n"
            f"Exception Type: {type(exception).__name__}\n"
            f"Exception Message: {str(exception)}\n"
            f"Request: {request.method} {request.path}\n"
            f"User: {user}\n"
            f"IP: {self._get_client_ip(request)}\n"
            f"Duration: {duration}\n"
            f"{'='*80}\n"
            f"Traceback:\n{traceback.format_exc()}\n"
            f"{'='*80}\n"
        )

        # For AJAX requests, return JSON error response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
           request.content_type == 'application/json':
            return JsonResponse({
                'status': 'error',
                'error': str(exception),
                'error_type': type(exception).__name__
            }, status=500)

        # Let Django handle the error normally for HTML requests
        return None

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


class PerformanceLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to track slow requests and database queries
    Helps identify performance bottlenecks
    """

    SLOW_REQUEST_THRESHOLD = 2.0  # seconds

    def process_request(self, request):
        """Mark request start time"""
        request._perf_start_time = time.time()

    def process_response(self, request, response):
        """Log slow requests"""
        if hasattr(request, '_perf_start_time'):
            duration = time.time() - request._perf_start_time

            if duration > self.SLOW_REQUEST_THRESHOLD:
                user = 'Anonymous'
                if hasattr(request, 'user') and request.user.is_authenticated:
                    user = request.user.username

                perf_logger.warning(
                    f"⚠️  SLOW REQUEST | {request.method} {request.path} | "
                    f"User: {user} | Duration: {duration:.3f}s | "
                    f"Status: {response.status_code} | "
                    f"Threshold: {self.SLOW_REQUEST_THRESHOLD}s"
                )

        return response


class UserActivityLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log important user activities
    Tracks login, logout, registration, profile changes, etc.
    """

    TRACKED_PATHS = [
        '/login/',
        '/logout/',
        '/register/',
        '/profile/',
        '/rebalance/',
        '/start_timer/',
        '/stop_timer/',
    ]

    def process_response(self, request, response):
        """Log important user activities"""

        # Only log successful requests to tracked paths
        if response.status_code < 400:
            path = request.path

            # Check if this is a tracked path
            for tracked_path in self.TRACKED_PATHS:
                if tracked_path in path:
                    user = 'Anonymous'
                    if hasattr(request, 'user') and request.user.is_authenticated:
                        user = request.user.username

                    activity_logger.info(
                        f"👤 USER ACTIVITY | User: {user} | "
                        f"Action: {request.method} {path} | "
                        f"IP: {self._get_client_ip(request)}"
                    )
                    break

        return response

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
