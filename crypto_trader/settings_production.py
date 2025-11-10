"""
Production settings for PythonAnywhere deployment.
This file should be used on PythonAnywhere.
"""

from .settings import *
from decouple import config

# SECURITY SETTINGS
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')

# ALLOWED HOSTS
ALLOWED_HOSTS = [
    'CryptoIndex.pythonanywhere.com',
    'www.CryptoIndex.pythonanywhere.com',
]

# HTTPS/Security Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS Settings (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files configuration for PythonAnywhere
STATIC_URL = '/static/'
STATIC_ROOT = '/home/CryptoIndex/20_index_rebalancer/staticfiles'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/CryptoIndex/20_index_rebalancer/media'

# Database configuration
# PythonAnywhere supports MySQL - update if you want to use MySQL
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': config('DB_NAME'),
#         'USER': config('DB_USER'),
#         'PASSWORD': config('DB_PASSWORD'),
#         'HOST': config('DB_HOST'),
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#         },
#     }
# }

# For now, using SQLite (simpler for deployment)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django_errors.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# Email configuration (optional - for error notifications)
# ADMINS = [('Your Name', 'your.email@example.com')]
# SERVER_EMAIL = 'django@CryptoIndex.pythonanywhere.com'

# Domain for Stripe redirects
DOMAIN = config('DOMAIN', default='https://CryptoIndex.pythonanywhere.com')
