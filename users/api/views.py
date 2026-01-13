"""
API Views for Users app.
"""

from django.contrib.auth import get_user_model
from rest_framework import status, viewsets, generics
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from core.api import SuccessResponseMixin, StandardResultsSetPagination
from .serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer,
    CustomTokenObtainPairSerializer,
    AvatarUploadSerializer,
)

User = get_user_model()


@extend_schema_view(
    post=extend_schema(
        tags=['Authentication'],
        summary='Obtain JWT token pair',
        description='Authenticate user and obtain access and refresh tokens.'
    )
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view that includes user information in response.
    """
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema_view(
    post=extend_schema(
        tags=['Authentication'],
        summary='Refresh JWT token',
        description='Refresh the access token using a valid refresh token.'
    )
)
class CustomTokenRefreshView(TokenRefreshView):
    """
    Token refresh view.
    """
    pass


@extend_schema(tags=['Authentication'])
class RegisterView(SuccessResponseMixin, generics.CreateAPIView):
    """
    User registration endpoint.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary='Register new user',
        description='Create a new user account. Returns user data and JWT tokens.'
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Registration successful.',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Authentication'])
class LogoutView(SuccessResponseMixin, APIView):
    """
    Logout endpoint - blacklists the refresh token.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary='Logout user',
        description='Logout the user by blacklisting their refresh token.'
    )
    def post(self, request):
        from rest_framework_simplejwt.exceptions import TokenError
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return self.success_response(message='Successfully logged out.')
        except TokenError as e:
            # Token was invalid or already blacklisted - still considered successful logout
            logger.debug(f'Token error during logout: {e}')
            return self.success_response(message='Successfully logged out.')
        except Exception as e:
            # Log unexpected errors but still return success for better UX
            logger.warning(f'Unexpected error during logout: {e}')
            return self.success_response(message='Successfully logged out.')


@extend_schema_view(
    retrieve=extend_schema(
        tags=['Users'],
        summary='Get current user profile',
        description='Retrieve the current authenticated user\'s profile.'
    ),
    partial_update=extend_schema(
        tags=['Users'],
        summary='Update current user profile',
        description='Update the current authenticated user\'s profile.'
    )
)
class CurrentUserView(SuccessResponseMixin, generics.RetrieveUpdateAPIView):
    """
    Retrieve and update current user's profile.
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return self.success_response(data=serializer.data)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return self.success_response(
            data=UserDetailSerializer(instance).data,
            message='Profile updated successfully.'
        )


@extend_schema(tags=['Users'])
class PasswordChangeView(SuccessResponseMixin, APIView):
    """
    Change password endpoint.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary='Change password',
        description='Change the current user\'s password.',
        request=PasswordChangeSerializer
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return self.success_response(message='Password changed successfully.')


@extend_schema(tags=['Users'])
class AvatarUploadView(SuccessResponseMixin, APIView):
    """
    Upload avatar endpoint.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary='Upload avatar',
        description='Upload or update the user\'s avatar image.',
        request=AvatarUploadSerializer
    )
    def post(self, request):
        serializer = AvatarUploadSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.success_response(
            data={'avatar': request.user.avatar.url if request.user.avatar else None},
            message='Avatar uploaded successfully.'
        )
    
    @extend_schema(
        summary='Delete avatar',
        description='Remove the user\'s avatar image.'
    )
    def delete(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()
        
        return self.success_response(message='Avatar removed successfully.')


@extend_schema_view(
    list=extend_schema(
        tags=['Users'],
        summary='List users',
        description='List all users. Staff/Instructor only.',
        parameters=[
            OpenApiParameter(name='role', description='Filter by user role'),
            OpenApiParameter(name='search', description='Search by username or email'),
        ]
    ),
    retrieve=extend_schema(
        tags=['Users'],
        summary='Get user details',
        description='Get details of a specific user.'
    )
)
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving users.
    Read-only for regular users, admin can see all.
    """
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    filterset_fields = ['role']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Non-staff users can only see instructors and limited info
        if not self.request.user.is_staff:
            queryset = queryset.filter(role__in=[User.INSTRUCTOR])
        
        return queryset
    
    @extend_schema(
        tags=['Users'],
        summary='List instructors',
        description='Get a list of all instructors.'
    )
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def instructors(self, request):
        """
        List all instructors (public endpoint).
        """
        instructors = User.objects.filter(role=User.INSTRUCTOR, is_active=True)
        page = self.paginate_queryset(instructors)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(instructors, many=True)
        return Response(serializer.data)
