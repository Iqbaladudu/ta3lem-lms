"""
Development settings untuk ta3lem project.
Settings untuk environment development/local.
"""

from .base import *

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

# Database - SQLite untuk development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Cache - Redis local
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379',
    }
}

# Email backend - Console untuk development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

