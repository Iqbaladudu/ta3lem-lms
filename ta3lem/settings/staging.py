"""
Staging settings untuk ta3lem project.
Settings untuk environment staging - mirip production tapi dengan beberapa tools debugging.
"""

import os
from pathlib import Path
from .base import *

from dotenv import load_dotenv

load_dotenv()


MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware') 
MIDDLEWARE.insert(2, 'ta3lem.middleware.SecurityHeadersMiddleware')  # CSP and security headers


# SECRET_KEY dari environment variable
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-staging-key-change-this')

# DEBUG mode - False untuk keamanan, tapi bisa diaktifkan sementara untuk debugging
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# ALLOWED_HOSTS dari environment variable + local development hosts
_env_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', 'staging.ta3lem.com').split(',')
_local_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
ALLOWED_HOSTS = list(set(_env_hosts + _local_hosts))  # Merge and deduplicate

INSTALLED_APPS = INSTALLED_APPS + [
    # 'debug_toolbar',
    'redisboard',
]

# INTERNAL_IPS = [
#     '127.0.0.1',
# ]

# Database - PostgreSQL (disarankan)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'ta3lem'),
        'USER': os.environ.get('DB_USER', 'ta3lem'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'ta3lem'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Cache - Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

# Email backend - SMTP atau layanan email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@ta3lem.com')

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise configuration for staging
WHITENOISE_USE_FINDERS = False
WHITENOISE_AUTOREFRESH = True
WHITENOISE_MAX_AGE = 31557600

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Security settings - Medium level
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'False') == 'True'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging
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
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'staging.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

CSRF_TRUSTED_ORIGINS = os.environ.get(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    'https://ta3lem-staging.zeabur.app,http://localhost:8000,http://127.0.0.1:8000'
).split(',')

# Enable HSTS
SECURE_HSTS_SECONDS = 31536000  
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security Policy (CSP) for API-only
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'",)
CSP_IMG_SRC = ("'self'", "data:",)
CSP_FONT_SRC = ("'self'", "data:",)
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_FORM_ACTION = ("'self'",)
CSP_BASE_URI = ("'self'",)

# Generate CSP header string for middleware
def get_csp_header():
    policies = [
        f"default-src {' '.join(CSP_DEFAULT_SRC)}",
        f"script-src {' '.join(CSP_SCRIPT_SRC)}",
        f"style-src {' '.join(CSP_STYLE_SRC)}",
        f"img-src {' '.join(CSP_IMG_SRC)}",
        f"font-src {' '.join(CSP_FONT_SRC)}",
        f"connect-src {' '.join(CSP_CONNECT_SRC)}",
        f"frame-ancestors {' '.join(CSP_FRAME_ANCESTORS)}",
        f"form-action {' '.join(CSP_FORM_ACTION)}",
        f"base-uri {' '.join(CSP_BASE_URI)}",
    ]
    return "; ".join(policies)

CSP_HEADER = get_csp_header()
