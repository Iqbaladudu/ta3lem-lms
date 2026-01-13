"""
URL configuration for Courses API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SubjectViewSet,
    CourseViewSet,
    ModuleViewSet,
    ContentViewSet,
    EnrollmentViewSet,
    CourseProgressView,
    MarkContentCompleteView,
    ModuleProgressView,
    LearningSessionViewSet,
)

router = DefaultRouter()
router.register('subjects', SubjectViewSet, basename='subject')
router.register('courses', CourseViewSet, basename='course')
router.register('modules', ModuleViewSet, basename='module')
router.register('contents', ContentViewSet, basename='content')
router.register('enrollments', EnrollmentViewSet, basename='enrollment')
router.register('sessions', LearningSessionViewSet, basename='session')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Progress endpoints
    path(
        'courses/<slug:course_slug>/progress/',
        CourseProgressView.as_view(),
        name='course_progress'
    ),
    path(
        'courses/<slug:course_slug>/complete/',
        MarkContentCompleteView.as_view(),
        name='mark_content_complete'
    ),
    path(
        'courses/<slug:course_slug>/modules/progress/',
        ModuleProgressView.as_view(),
        name='module_progress'
    ),
    
    # Nested module routes for a course
    path(
        'courses/<slug:course_slug>/modules/',
        ModuleViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='course_modules'
    ),
]
