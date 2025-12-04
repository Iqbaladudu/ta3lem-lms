# Quick Start Guide: Ta3lem LMS Development & Deployment

**Feature**: Complete Learning Management System  
**Date**: 2025-12-03  
**Prerequisites**: docker, docker-compose, Python 3.13+, Node.js 18+

## Development Environment Setup

### 1. Repository Setup

```bash
# Clone and setup repository
git clone <repository-url> ta3lem-lms
cd ta3lem-lms
git checkout 001-comprehensive-lms  # Work on feature branch

# Setup Python environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt
# OR if using uv (recommended)
uv sync
```

### 2. Database & Services Setup

```bash
# Start PostgreSQL and Redis services
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
docker-compose logs -f postgres redis

# Setup database
uv run manage.py migrate --settings=ta3lem.settings.development
```

### 3. Load Sample Data

```bash
# Load all fixture data for development
chmod +x load_all_fixtures.sh
./load_all_fixtures.sh

# This loads:
# - Sample users (students, instructors, staff)
# - Course subjects
# - Sample courses with modules and content
# - Enrollment data and progress tracking
# - Learning sessions for analytics
```

### 4. Create Superuser (Optional)

```bash
# Create admin user for Django admin
uv run manage.py createsuperuser --settings=ta3lem.settings.development
```

### 5. Frontend Development Setup

```bash
# Setup Vite frontend build system
cd vite/src
npm install

# Start frontend development server (separate terminal)
npm run dev

# Return to project root
cd ../..
```

### 6. Start Development Server

```bash
# Option 1: Use honcho (recommended - starts Django + Vite together)
uv run honcho start

# Option 2: Start Django server manually
uv run manage.py runserver 0.0.0.0:8000 --settings=ta3lem.settings.development
```

### 7. Access the Application

- **Main Application**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **Vite Dev Server**: http://localhost:5173 (auto-proxy to Django)

**Default Login Accounts** (from fixtures):
- Student: `student1` / `testpass123`
- Instructor: `instructor1` / `testpass123`  
- Staff: `admin` / `testpass123`

## API Development Setup

### 1. Install API Dependencies

```bash
# Add Django REST Framework and related packages
uv add djangorestframework
uv add djangorestframework-simplejwt
uv add drf-spectacular  # API documentation
uv add django-cors-headers  # CORS for mobile/external access
```

### 2. Configure API Settings

```python
# ta3lem/settings/base.py - Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders',
    'api',  # New API application
]

# Add REST framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# Add JWT configuration
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}
```

### 3. Create API Application

```bash
# Create new Django app for API
uv run manage.py startapp api

# Directory structure:
# api/
# ├── __init__.py
# ├── apps.py
# ├── views.py
# ├── serializers.py
# ├── urls.py
# └── v1/
#     ├── __init__.py
#     ├── auth.py
#     ├── courses.py
#     └── analytics.py
```

### 4. API URL Configuration

```python
# ta3lem/urls.py - Add API URLs
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # ... existing URLs
]
```

## Testing Setup

### 1. Install Testing Dependencies

```bash
# Add testing packages
uv add pytest-django
uv add factory-boy
uv add pytest-cov
uv add pytest-mock
```

### 2. Configure pytest

```ini
# pytest.ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = ta3lem.settings.development
python_files = tests.py test_*.py *_tests.py
python_classes = Test* *Tests
python_functions = test_*
addopts = 
    --cov=.
    --cov-report=html
    --cov-report=term
    --cov-exclude=*/migrations/*
    --cov-exclude=*/venv/*
    --cov-exclude=*/tests/*
```

### 3. Run Tests

```bash
# Run all tests
uv run pytest

# Run specific app tests
uv run pytest users/tests/
uv run pytest courses/tests/

# Run with coverage report
uv run pytest --cov

# Run API tests (when implemented)
uv run pytest api/tests/
```

### 4. Test Database Setup

```python
# ta3lem/settings/test.py
from .base import *

# Use in-memory SQLite for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable caching during tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
```

## Production Deployment

### 1. Environment Configuration

```bash
# Create production environment file
cp .env.example .env.production

# Configure production variables:
# DATABASE_URL=postgresql://user:pass@host:port/dbname
# REDIS_URL=redis://host:port/0
# SECRET_KEY=<generate-secure-key>
# DEBUG=False
# ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### 2. Docker Production Build

```dockerfile
# Dockerfile.production
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Setup application
WORKDIR /app
COPY . .
RUN pip install uv
RUN uv sync --no-dev

# Build frontend assets
WORKDIR /app/vite/src
RUN npm ci && npm run build

# Setup production server
WORKDIR /app
RUN uv run manage.py collectstatic --noinput
EXPOSE 8000
CMD ["uv", "run", "gunicorn", "ta3lem.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### 3. Docker Compose Production

```yaml
# docker-compose.prod.yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.production
    environment:
      - DATABASE_URL=postgresql://ta3lem:${DB_PASSWORD}@postgres:5432/ta3lem_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ta3lem_db
      POSTGRES_USER: ta3lem
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./media:/app/media:ro
      - ./static:/app/static:ro

volumes:
  postgres_data:
  redis_data:
```

### 4. Production Deployment Commands

```bash
# Deploy to production
docker-compose -f docker-compose.prod.yaml up -d

# Run database migrations
docker-compose -f docker-compose.prod.yaml exec app uv run manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yaml exec app uv run manage.py createsuperuser

# Collect static files (if not done in build)
docker-compose -f docker-compose.prod.yaml exec app uv run manage.py collectstatic --noinput
```

## Performance Optimization

### 1. Database Optimization

```bash
# Add database indexes for performance
uv run manage.py makemigrations --empty courses
# Edit migration to add custom indexes:
# - Course enrollment lookups
# - Progress calculation queries  
# - Analytics aggregation indexes
```

### 2. Caching Configuration

```python
# ta3lem/settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'ta3lem',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Cache sessions in Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### 3. Static Files & CDN

```python
# Configure static files for production
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# For CDN integration (optional):
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# AWS_STORAGE_BUCKET_NAME = 'your-bucket-name'
```

## Monitoring & Logging

### 1. Application Monitoring

```python
# ta3lem/settings/production.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'ta3lem': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 2. Health Checks

```python
# Add health check endpoint
# ta3lem/urls.py
path('health/', health_check_view, name='health_check'),

# Simple health check view
def health_check_view(request):
    return JsonResponse({'status': 'healthy', 'timestamp': timezone.now()})
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database connection
   docker-compose logs postgres
   uv run manage.py dbshell --settings=ta3lem.settings.development
   ```

2. **Static Files Not Loading**
   ```bash
   # Rebuild static files
   uv run manage.py collectstatic --clear --noinput
   # Check Vite build
   cd vite/src && npm run build
   ```

3. **Cache Issues**
   ```bash
   # Clear Redis cache
   docker-compose exec redis redis-cli FLUSHALL
   ```

4. **Migration Issues**
   ```bash
   # Reset migrations (development only)
   uv run manage.py migrate --fake-initial
   # OR drop database and recreate
   docker-compose down -v && docker-compose up -d
   ```

### Performance Issues

1. **Slow Database Queries**
   ```bash
   # Enable query logging
   # Add to settings: LOGGING for django.db.backends
   # Use Django Debug Toolbar in development
   ```

2. **High Memory Usage**
   ```bash
   # Monitor memory usage
   docker stats
   # Optimize QuerySets with select_related/prefetch_related
   ```

### Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Set DEBUG=False in production
- [ ] Configure ALLOWED_HOSTS properly
- [ ] Enable HTTPS with proper certificates
- [ ] Regular backup of PostgreSQL database
- [ ] Update dependencies regularly
- [ ] Monitor for security vulnerabilities

## Next Steps

1. **API Implementation** - Use contracts in `/contracts/` to implement REST API
2. **Enhanced Testing** - Add comprehensive test coverage using pytest
3. **Mobile App Development** - Use API for mobile applications
4. **Advanced Analytics** - Implement machine learning features for learning insights
5. **Multi-tenancy** - Add support for multiple institutions

For detailed implementation guidance, refer to:
- `research.md` - Technical decisions and alternatives
- `data-model.md` - Database schema and entity relationships  
- `/contracts/` - API specifications for implementation
- `tasks.md` - Detailed implementation task breakdown (generate with `/speckit.tasks`)

**Development Status**: Ready for API implementation and enhanced features development.