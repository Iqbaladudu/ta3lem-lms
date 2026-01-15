"""
Users API package.
"""

from .serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer,
    CustomTokenObtainPairSerializer,
    AvatarUploadSerializer,
    StudentProfileSerializer,
    InstructorProfileSerializer,
)
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

__all__ = [
    # Serializers
    'UserSerializer',
    'UserDetailSerializer',
    'UserRegistrationSerializer',
    'UserUpdateSerializer',
    'PasswordChangeSerializer',
    'CustomTokenObtainPairSerializer',
    'AvatarUploadSerializer',
    'StudentProfileSerializer',
    'InstructorProfileSerializer',
    # Views
    'CustomTokenObtainPairView',
    'CustomTokenRefreshView',
    'RegisterView',
    'LogoutView',
    'CurrentUserView',
    'PasswordChangeView',
    'AvatarUploadView',
    'UserViewSet',
]
