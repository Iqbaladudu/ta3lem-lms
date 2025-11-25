"""
Development settings untuk ta3lem project.
Settings untuk environment development/local.
"""

from .base import *
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-+gdddxtl)^fib#1+ffnch4^u)0dw02_r5zeep%g2zlohgj9(bt'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

# Development-specific apps
INSTALLED_APPS += [
    'debug_toolbar',
    'redisboard',
]

INTERNAL_IPS = [
    '127.0.0.1',
]

# Development-specific middleware
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# Database - PostgreSQL (disarankan)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'ta3lem_db'),
        'USER': os.environ.get('DB_USER', 'ta3lem'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'ta3lem123'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Cache - Redis local
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379'),
    }
}

# Email backend - Console untuk development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

