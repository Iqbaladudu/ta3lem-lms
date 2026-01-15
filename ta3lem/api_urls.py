"""
Main API URL configuration for Ta3lem LMS.

This module provides versioned API routing with comprehensive
documentation via drf-spectacular (OpenAPI/Swagger).
"""

from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

app_name = 'api'

# API v1 URL patterns
v1_patterns = [
    # Users & Authentication
    path('', include('users.api.urls')),
    
    # Courses
    path('', include('courses.api.urls')),
    
    # Payments
    path('payments/', include('payments.api.urls')),
    
    # Subscriptions
    path('subscriptions/', include('subscriptions.api.urls')),
]

urlpatterns = [
    # API Version 1
    path('v1/', include((v1_patterns, 'v1'))),
    
    # OpenAPI Schema
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # API Documentation (Swagger UI)
    path(
        'docs/',
        SpectacularSwaggerView.as_view(url_name='api:schema'),
        name='swagger-ui'
    ),
    
    # API Documentation (ReDoc)
    path(
        'redoc/',
        SpectacularRedocView.as_view(url_name='api:schema'),
        name='redoc'
    ),
]
