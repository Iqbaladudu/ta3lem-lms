"""
URL configuration for Users API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenVerifyView

from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    RegisterView,
    LogoutView,
    CurrentUserView,
    PasswordChangeView,
    AvatarUploadView,
    UserViewSet,
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    
    # Current user endpoints
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('me/password/', PasswordChangeView.as_view(), name='password_change'),
    path('me/avatar/', AvatarUploadView.as_view(), name='avatar_upload'),
    
    # User management (via router)
    path('', include(router.urls)),
]
